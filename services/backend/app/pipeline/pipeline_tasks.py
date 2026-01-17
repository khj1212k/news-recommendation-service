from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Tuple

from dateutil import parser
from langdetect import detect, LangDetectException
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.article import Article, ArticleKeyword
from app.models.newsletter import Newsletter, NewsletterCitation, NewsletterEmbedding
from app.models.enums import NewsletterStatus
from app.models.source import Source
from app.models.topic import Topic, TopicArticle
from app.pipeline.adapters.rss import RssAdapter
from app.pipeline.adapters.base import BaseAdapter
from app.pipeline.source_registry import load_source_configs
from app.services.embedding_service import EmbeddingService
from app.services.keyword_extraction import extract_keywords
from app.services.llm_service import generate_newsletter
from app.pipeline.hash_utils import topic_content_hash
from app.pipeline.topic_utils import cosine_similarity, should_assign_topic
from app.utils.dedup import canonicalize_url, find_near_duplicate
from app.utils.logger import get_logger, log_metrics
from app.utils.text_utils import clean_text, content_hash, split_sentences

logger = get_logger(__name__)

CATEGORY_HINTS = {
    "정치": ["정책", "국회", "정부", "선거", "장관"],
    "경제": ["경제", "금융", "지원금", "수수료", "기업"],
    "사회": ["교육", "도서관", "복지", "안전", "지역"],
    "세계": ["국제", "해외", "포럼", "협력", "기후"],
    "IT/과학": ["AI", "기술", "과학", "칩", "디지털"],
    "문화": ["공연", "문화", "전시", "예술", "축제"],
    "스포츠": ["스포츠", "농구", "축구", "선수", "클리닉"],
}


class PipelineContext:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedder = EmbeddingService()


def _has_embedding(vector) -> bool:
    if vector is None:
        return False
    try:
        return len(vector) > 0
    except TypeError:
        return True


def _embedding_dim(vector) -> int:
    if vector is None:
        return 0
    try:
        return len(vector)
    except TypeError:
        return 0


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _get_source(db: Session, config) -> Source:
    source = db.query(Source).filter(Source.name == config.name).first()
    if source:
        source.base_url = config.base_url
        source.terms_url = config.terms_url
        source.allow_fulltext = config.allow_fulltext
        source.allow_derivatives = config.allow_derivatives
        return source
    source = Source(
        name=config.name,
        base_url=config.base_url,
        terms_url=config.terms_url,
        allow_fulltext=config.allow_fulltext,
        allow_derivatives=config.allow_derivatives,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def _build_adapters(settings, include_catalog: bool = False) -> List[BaseAdapter]:
    """
    Build adapters from source configuration.
    
    Args:
        settings: Application settings
        include_catalog: If True, also load sources from rss_sources_catalog.yaml
    
    Returns:
        List of adapters (RssAdapter or NewspaperAdapter instances)
    """
    from app.pipeline.adapters.newspaper import NewspaperAdapter
    
    adapters: List[BaseAdapter] = []
    configs = load_source_configs(settings.news_sources_file)
    
    # Optionally include catalog sources
    if include_catalog:
        from app.pipeline.catalog_loader import load_catalog_sources
        catalog_configs = load_catalog_sources()
        configs.extend(catalog_configs)
    
    for config in configs:
        if not config.enabled:
            continue
        if not (config.allow_fulltext and config.allow_derivatives):
            logger.warning(
                "source skipped due to permissions",
                extra={"extra": {"source": config.name}},
            )
            continue
        if config.max_items > settings.news_max_items_per_source:
            config.max_items = settings.news_max_items_per_source
        
        if config.adapter == "rss":
            adapters.append(
                RssAdapter(
                    config,
                    timeout=settings.news_request_timeout,
                    user_agent=settings.news_user_agent,
                )
            )
        elif config.adapter == "newspaper":
            adapters.append(
                NewspaperAdapter(
                    config,
                    timeout=settings.news_request_timeout,
                    user_agent=settings.news_user_agent,
                )
            )
        else:
            logger.warning(
                "unknown adapter type",
                extra={"extra": {"source": config.name, "adapter": config.adapter}},
            )
    return adapters


def fetch_articles() -> Dict[str, int]:
    settings = get_settings()
    db = SessionLocal()
    inserted = 0
    updated = 0
    adapters = _build_adapters(settings)
    try:
        for adapter in adapters:
            config = getattr(adapter, "source", None)
            if not config:
                continue
            source = _get_source(db, config)
            for payload in adapter.fetch():
                canonical_url = canonicalize_url(payload.url)
                published_at = parser.parse(payload.published_at) if payload.published_at else None
                stmt = insert(Article).values(
                    source_id=source.id,
                    url=payload.url,
                    url_canonical=canonical_url,
                    title=payload.title,
                    author=payload.author,
                    published_at=published_at,
                    fetched_at=_now_utc(),
                    raw_text=payload.raw_text,
                    metadata_=payload.metadata or {},
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=[Article.url],
                    set_={
                        "title": payload.title,
                        "author": payload.author,
                        "published_at": published_at,
                        "fetched_at": _now_utc(),
                        "raw_text": payload.raw_text,
                        "url_canonical": canonical_url,
                        Article.__table__.c.metadata: payload.metadata or {},
                    },
                )
                result = db.execute(stmt)
                if result.rowcount:
                    inserted += 1
                else:
                    updated += 1
        db.commit()
    finally:
        db.close()

    log_metrics(logger, "fetch_articles", inserted=inserted, updated=updated)
    if inserted == 0:
        logger.warning("fetch_articles volume drop", extra={"extra": {"inserted": inserted}})
    return {"inserted": inserted, "updated": updated}


def clean_normalize() -> Dict[str, int]:
    db = SessionLocal()
    processed = 0
    language_mismatch = 0
    empty_text = 0
    length_outliers = 0
    try:
        articles = db.query(Article).filter(Article.raw_text.isnot(None)).all()
        for article in articles:
            cleaned = clean_text(article.raw_text or "")
            if not cleaned:
                empty_text += 1
                continue
            if len(cleaned) < 50 or len(cleaned) > 20000:
                length_outliers += 1
            if article.clean_text == cleaned and article.content_hash:
                continue
            try:
                language = detect(cleaned)
            except LangDetectException:
                language = "unknown"
            if language != "ko":
                language_mismatch += 1
                article.metadata_ = {**(article.metadata_ or {}), "language_mismatch": True}
            new_hash = content_hash(cleaned)
            if article.content_hash and article.content_hash != new_hash:
                article.version += 1
            article.clean_text = cleaned
            article.language = language
            article.content_hash = new_hash
            processed += 1
        db.commit()
    finally:
        db.close()

    log_metrics(
        logger,
        "clean_normalize",
        processed=processed,
        language_mismatch=language_mismatch,
        empty_text=empty_text,
        length_outliers=length_outliers,
    )
    return {
        "processed": processed,
        "language_mismatch": language_mismatch,
        "empty_text": empty_text,
        "length_outliers": length_outliers,
    }


def deduplicate() -> Dict[str, int]:
    settings = get_settings()
    db = SessionLocal()
    exact_dupes = 0
    near_dupes = 0
    try:
        articles = db.query(Article).filter(Article.clean_text.isnot(None)).all()
        groups: Dict[str, List[Article]] = defaultdict(list)
        for article in articles:
            if not article.content_hash:
                continue
            groups[article.content_hash].append(article)
        for _, group in groups.items():
            if len(group) <= 1:
                continue
            group.sort(key=lambda a: a.published_at or _now_utc())
            keeper = group[0]
            for dup in group[1:]:
                dup.metadata_ = {**(dup.metadata_ or {}), "duplicate_of": str(keeper.id)}
                exact_dupes += 1

        candidates = [a for a in articles if not (a.metadata_ or {}).get("duplicate_of")]
        recent_texts: List[str] = []
        recent_articles: List[Article] = []
        for article in candidates:
            if not article.clean_text:
                continue
            match_idx = find_near_duplicate(article.clean_text, recent_texts, settings.dedup_near_threshold)
            if match_idx is not None:
                original = recent_articles[match_idx]
                article.metadata_ = {**(article.metadata_ or {}), "duplicate_of": str(original.id)}
                near_dupes += 1
            else:
                recent_texts.append(article.clean_text)
                recent_articles.append(article)
        db.commit()
    finally:
        db.close()

    log_metrics(logger, "deduplicate", exact_duplicates=exact_dupes, near_duplicates=near_dupes)
    return {"exact_duplicates": exact_dupes, "near_duplicates": near_dupes}


def extract_keywords_task() -> Dict[str, int]:
    db = SessionLocal()
    inserted = 0
    try:
        articles = (
            db.query(Article)
            .filter(Article.clean_text.isnot(None))
            .filter(~Article.id.in_(db.query(ArticleKeyword.article_id)))
            .all()
        )
        for article in articles:
            if (article.metadata_ or {}).get("duplicate_of"):
                continue
            if article.language and article.language != "ko":
                continue
            keywords = extract_keywords(article.clean_text or "")
            for keyword, score, method in keywords:
                stmt = insert(ArticleKeyword).values(
                    article_id=article.id,
                    keyword=keyword,
                    score=score,
                    method=method,
                )
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=[ArticleKeyword.article_id, ArticleKeyword.keyword, ArticleKeyword.method]
                )
                result = db.execute(stmt)
                if result.rowcount:
                    inserted += 1
        db.commit()
    finally:
        db.close()

    log_metrics(logger, "extract_keywords", inserted=inserted)
    return {"inserted": inserted}


def _infer_category(text: str) -> Optional[str]:
    for category, hints in CATEGORY_HINTS.items():
        for hint in hints:
            if hint in text:
                return category
    return None


def assign_topics() -> Dict[str, int]:
    settings = get_settings()
    ctx = PipelineContext()
    db = SessionLocal()
    created = 0
    assigned = 0
    merged = 0
    try:
        assigned_article_ids = {row.article_id for row in db.query(TopicArticle.article_id).all()}
        articles = (
            db.query(Article)
            .filter(Article.clean_text.isnot(None))
            .filter(~Article.id.in_(assigned_article_ids))
            .all()
        )
        cutoff = _now_utc() - timedelta(days=settings.topic_time_window_days)
        topics = (
            db.query(Topic)
            .filter(Topic.last_updated_at >= cutoff)
            .all()
        )

        for article in articles:
            if (article.metadata_ or {}).get("duplicate_of"):
                continue
            if article.language and article.language != "ko":
                continue
            article_category = (article.metadata_ or {}).get("category")
            embedding = ctx.embedder.embed_text(article.clean_text or "")
            best_topic = None
            best_similarity = -1.0
            for topic in topics:
                if topic.metadata_ and topic.metadata_.get("merged_into"):
                    continue
                if article_category and topic.category and topic.category != article_category:
                    continue
                if not _has_embedding(topic.centroid_embedding):
                    continue
                similarity = cosine_similarity(topic.centroid_embedding, embedding)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_topic = topic
            if best_topic and should_assign_topic(best_similarity, settings.topic_similarity_threshold):
                topic = best_topic
                if topic.category is None and article_category:
                    topic.category = article_category
                assigned += 1
            else:
                title = article.title or (split_sentences(article.clean_text or "")[:1] or ["새로운 이슈"])[0]
                category = article.metadata_.get("category") if article.metadata_ else None
                if not category:
                    category = _infer_category(article.title or "") or _infer_category(article.clean_text or "")
                topic = Topic(
                    title=title,
                    category=category,
                    first_seen_at=_now_utc(),
                    last_updated_at=_now_utc(),
                    popularity_count=0,
                    centroid_embedding=embedding,
                    metadata_={},
                )
                db.add(topic)
                db.flush()
                topics.append(topic)
                created += 1

            db.add(
                TopicArticle(
                    topic_id=topic.id,
                    article_id=article.id,
                    score=best_similarity if best_topic else None,
                )
            )
            topic.last_updated_at = _now_utc()
            topic.popularity_count = (topic.popularity_count or 0) + 1
            if _has_embedding(topic.centroid_embedding):
                count = topic.popularity_count
                topic.centroid_embedding = [
                    (v * (count - 1) + embedding[idx]) / count
                    for idx, v in enumerate(topic.centroid_embedding)
                ]
            else:
                topic.centroid_embedding = embedding

        merged += _merge_topics(db, settings.topic_merge_threshold, settings.topic_time_window_days)
        db.commit()
    finally:
        db.close()

    log_metrics(logger, "assign_topics", created=created, assigned=assigned, merged=merged)
    return {"created": created, "assigned": assigned, "merged": merged}


def _merge_topics(db: Session, threshold: float, window_days: int) -> int:
    cutoff = _now_utc() - timedelta(days=window_days)
    topics = db.query(Topic).filter(Topic.last_updated_at >= cutoff).all()
    merged = 0
    for i, topic in enumerate(topics):
        if topic.metadata_ and topic.metadata_.get("merged_into"):
            continue
        if not _has_embedding(topic.centroid_embedding):
            continue
        for other in topics[i + 1 :]:
            if other.metadata_ and other.metadata_.get("merged_into"):
                continue
            if topic.category and other.category and topic.category != other.category:
                continue
            if not _has_embedding(other.centroid_embedding):
                continue
            similarity = cosine_similarity(topic.centroid_embedding, other.centroid_embedding)
            if similarity >= threshold:
                primary, secondary = (topic, other) if (topic.popularity_count or 0) >= (other.popularity_count or 0) else (other, topic)
                db.query(TopicArticle).filter(TopicArticle.topic_id == secondary.id).update(
                    {TopicArticle.topic_id: primary.id}, synchronize_session=False
                )
                primary.popularity_count = (primary.popularity_count or 0) + (secondary.popularity_count or 0)
                secondary.metadata_ = {**(secondary.metadata_ or {}), "merged_into": str(primary.id)}
                merged += 1
    return merged


def generate_newsletters() -> Dict[str, int]:
    db = SessionLocal()
    generated = 0
    skipped = 0
    try:
        topics = db.query(Topic).all()
        for topic in topics:
            if topic.metadata_ and topic.metadata_.get("merged_into"):
                continue
            article_rows = (
                db.query(Article)
                .join(TopicArticle, TopicArticle.article_id == Article.id)
                .filter(TopicArticle.topic_id == topic.id)
                .all()
            )
            if not article_rows:
                continue
            article_hashes = [a.content_hash for a in article_rows if a.content_hash]
            if not article_hashes:
                continue
            topic_hash = topic_content_hash(article_hashes)
            existing = (
                db.query(Newsletter)
                .filter(Newsletter.topic_id == topic.id, Newsletter.content_hash == topic_hash)
                .first()
            )
            if existing:
                skipped += 1
                continue
            payload_articles = [
                {
                    "id": str(a.id),
                    "title": a.title,
                    "clean_text": a.clean_text,
                    "published_at": a.published_at.isoformat() if a.published_at else None,
                }
                for a in article_rows
            ]
            result = generate_newsletter(topic.title or "주요 이슈", payload_articles)
            newsletter = Newsletter(
                topic_id=topic.id,
                newsletter_text=result.text,
                content_hash=topic_hash,
                llm_model=get_settings().llm_model,
                prompt_version="v2",
                status=NewsletterStatus.ok,
                metadata_={"article_ids": [str(a.id) for a in article_rows]},
            )
            db.add(newsletter)
            db.flush()
            for citation in result.citations:
                article = next((a for a in article_rows if str(a.id) == citation["source_article_id"]), None)
                offset_start = None
                offset_end = None
                if article and article.clean_text:
                    idx = article.clean_text.find(citation["source_excerpt"])
                    if idx >= 0:
                        offset_start = idx
                        offset_end = idx + len(citation["source_excerpt"])
                db.add(
                    NewsletterCitation(
                        newsletter_id=newsletter.id,
                        sentence_index=citation["sentence_index"],
                        source_article_id=citation["source_article_id"],
                        source_excerpt=citation["source_excerpt"],
                        source_offset_start=offset_start,
                        source_offset_end=offset_end,
                    )
                )
            generated += 1
        db.commit()
    finally:
        db.close()

    log_metrics(logger, "generate_newsletters", generated=generated, skipped=skipped)
    return {"generated": generated, "skipped": skipped}


def embed_newsletters() -> Dict[str, int]:
    settings = get_settings()
    ctx = PipelineContext()
    db = SessionLocal()
    embedded = 0
    skipped = 0
    try:
        newsletters = db.query(Newsletter).all()
        for newsletter in newsletters:
            existing = db.query(NewsletterEmbedding).filter(NewsletterEmbedding.newsletter_id == newsletter.id).first()
            if existing and (
                existing.dim != settings.embedding_dim
                or _embedding_dim(existing.embedding) != settings.embedding_dim
            ):
                db.delete(existing)
                db.flush()
                existing = None
            if (
                existing
                and existing.content_hash == newsletter.content_hash
                and existing.dim == settings.embedding_dim
            ):
                skipped += 1
                continue
            vector = ctx.embedder.embed_text(newsletter.newsletter_text)
            if not existing:
                existing = NewsletterEmbedding(
                    newsletter_id=newsletter.id,
                    model=settings.embedding_model,
                    dim=settings.embedding_dim,
                    embedding=vector,
                    content_hash=newsletter.content_hash,
                )
                db.add(existing)
            else:
                existing.model = settings.embedding_model
                existing.dim = settings.embedding_dim
                existing.embedding = vector
                existing.content_hash = newsletter.content_hash
            embedded += 1

        _update_topic_centroids(db, settings.embedding_dim)
        db.commit()
    finally:
        db.close()

    log_metrics(logger, "embed_newsletters", embedded=embedded, skipped=skipped)
    return {"embedded": embedded, "skipped": skipped}


def _update_topic_centroids(db: Session, expected_dim: int) -> None:
    topics = db.query(Topic).all()
    for topic in topics:
        embeddings = (
            db.query(NewsletterEmbedding)
            .join(Newsletter, NewsletterEmbedding.newsletter_id == Newsletter.id)
            .filter(Newsletter.topic_id == topic.id)
            .all()
        )
        embeddings = [row for row in embeddings if _embedding_dim(row.embedding) == expected_dim]
        if not embeddings:
            continue
        length = len(embeddings[0].embedding)
        avg = [0.0] * length
        for embedding in embeddings:
            for idx, value in enumerate(embedding.embedding):
                avg[idx] += value
        avg = [v / len(embeddings) for v in avg]
        topic.centroid_embedding = avg


def update_popularity() -> Dict[str, int]:
    db = SessionLocal()
    updated = 0
    try:
        topics = db.query(Topic).all()
        for topic in topics:
            count = db.query(func.count(TopicArticle.article_id)).filter(TopicArticle.topic_id == topic.id).scalar()
            topic.popularity_count = int(count or 0)
            updated += 1
        db.commit()
    finally:
        db.close()

    log_metrics(logger, "update_popularity", updated=updated)
    return {"updated": updated}
