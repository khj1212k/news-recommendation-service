from datetime import datetime, timezone
from math import exp, log1p
import json
from typing import Dict, List, Optional, Tuple

import joblib
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import EventType
from app.models.event import Event
from app.models.newsletter import Newsletter, NewsletterEmbedding
from app.models.topic import Topic
from app.models.user import UserEmbedding, UserPreferences
from app.services.embedding_service import EmbeddingService
from app.services.rec_features import FEATURE_NAMES, build_feature_vector


CATEGORY_LABELS = ["정치", "경제", "사회", "세계", "IT/과학", "문화", "스포츠"]
_RANKER_MODEL = None
_RANKER_PATH = None
_RANKER_META = None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _combine_embeddings(vectors: List[List[float]]) -> List[float]:
    if not vectors:
        return []
    length = len(vectors[0])
    summed = [0.0] * length
    for vec in vectors:
        for idx, value in enumerate(vec):
            summed[idx] += value
    norm = sum(v * v for v in summed) ** 0.5
    if norm == 0:
        return summed
    return [v / norm for v in summed]


def _compute_user_embedding(preferences: Optional[UserPreferences], embedder: EmbeddingService) -> List[float]:
    if not preferences:
        return embedder.embed_text("한국 뉴스")
    vectors: List[List[float]] = []
    categories = preferences.categories or []
    keywords = preferences.keywords or []
    for category in categories:
        vectors.append(embedder.embed_text(f"{category} 뉴스"))
    for keyword in keywords:
        vectors.append(embedder.embed_text(keyword))
    if not vectors:
        return embedder.embed_text("한국 뉴스")
    return _combine_embeddings(vectors)


def get_or_create_user_embedding(
    db: Session, user_id, preferences: Optional[UserPreferences], embedder: EmbeddingService
) -> Tuple[List[float], str, int]:
    settings = get_settings()
    embedding_row = db.query(UserEmbedding).filter(UserEmbedding.user_id == user_id).first()
    if embedding_row:
        return embedding_row.embedding, embedding_row.model, embedding_row.dim
    vector = _compute_user_embedding(preferences, embedder)
    embedding_row = UserEmbedding(
        user_id=user_id,
        model=settings.embedding_model,
        dim=settings.embedding_dim,
        embedding=vector,
    )
    db.add(embedding_row)
    db.commit()
    return vector, settings.embedding_model, settings.embedding_dim


def _score_item(
    similarity: float,
    created_at: datetime,
    popularity_count: int,
) -> float:
    age_hours = max((_now_utc() - created_at).total_seconds() / 3600.0, 0.0)
    recency_boost = exp(-age_hours / 48.0)
    popularity_boost = log1p(popularity_count) / 5.0
    return similarity + recency_boost + popularity_boost


def _load_ranker_model():
    global _RANKER_MODEL, _RANKER_PATH, _RANKER_META
    settings = get_settings()
    model_path = settings.ranker_model_path
    if not model_path:
        return None
    if _RANKER_MODEL is not None and _RANKER_PATH == model_path:
        if _RANKER_META and _RANKER_META.get("features") == FEATURE_NAMES:
            return _RANKER_MODEL
        _RANKER_MODEL = None
    try:
        meta_path = settings.ranker_meta_path
        if meta_path and _RANKER_META is None:
            try:
                with open(meta_path, "r", encoding="utf-8") as handle:
                    _RANKER_META = json.load(handle)
            except Exception:
                _RANKER_META = {}
        if _RANKER_META:
            features = _RANKER_META.get("features")
            if features and features != FEATURE_NAMES:
                _RANKER_MODEL = None
                return None
        _RANKER_MODEL = joblib.load(model_path)
        _RANKER_PATH = model_path
        return _RANKER_MODEL
    except Exception:
        return None


def _build_reason(
    preferences: Optional[UserPreferences],
    topic: Topic,
    newsletter: Newsletter,
    clicked_topic_ids: set,
) -> str:
    categories = set(preferences.categories or []) if preferences else set()
    keywords = set(preferences.keywords or []) if preferences else set()
    if topic.category and topic.category in categories:
        return f"선택한 카테고리: {topic.category}"
    if keywords:
        for keyword in keywords:
            if keyword and keyword in (newsletter.newsletter_text or ""):
                return f"선택한 키워드: {keyword}"
    if topic.id in clicked_topic_ids:
        return "최근 읽은 주제와 유사"
    return "최신 이슈"


def get_personalized_feed(db: Session, user_id, limit: int = 30) -> List[Dict]:
    settings = get_settings()
    embedder = EmbeddingService()
    preferences = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    user_vector, _, _ = get_or_create_user_embedding(db, user_id, preferences, embedder)
    ranker = _load_ranker_model()

    hidden_topic_ids = {
        row.topic_id
        for row in db.query(Event.topic_id)
        .filter(Event.user_id == user_id, Event.event_type == EventType.hide)
        .all()
        if row.topic_id
    }
    clicked_topic_ids = {
        row.topic_id
        for row in db.query(Event.topic_id)
        .filter(Event.user_id == user_id, Event.event_type == EventType.click)
        .all()
        if row.topic_id
    }
    user_topic_clicks = {
        str(row.topic_id): 0
        for row in db.query(Event.topic_id)
        .filter(Event.user_id == user_id, Event.event_type == EventType.click)
        .all()
        if row.topic_id
    }
    topic_categories = {
        str(topic.id): topic.category or ""
        for topic in db.query(Topic.id, Topic.category).all()
    }
    user_category_clicks: Dict[str, int] = {}
    for row in (
        db.query(Event.topic_id)
        .filter(Event.user_id == user_id, Event.event_type.in_([EventType.click, EventType.save, EventType.follow]))
        .all()
    ):
        if row.topic_id:
            key = str(row.topic_id)
            user_topic_clicks[key] = user_topic_clicks.get(key, 0) + 1
            category = topic_categories.get(key, "")
            if category:
                user_category_clicks[category] = user_category_clicks.get(category, 0) + 1

    candidates = (
        db.query(NewsletterEmbedding, Newsletter, Topic)
        .join(Newsletter, NewsletterEmbedding.newsletter_id == Newsletter.id)
        .join(Topic, Newsletter.topic_id == Topic.id)
        .filter(Newsletter.status == "ok")
        .order_by(NewsletterEmbedding.embedding.cosine_distance(user_vector))
        .limit(max(limit * 3, 60))
        .all()
    )

    scored: List[Tuple[float, Newsletter, Topic, List[float]]] = []
    for embedding_row, newsletter, topic in candidates:
        if topic.metadata_ and topic.metadata_.get("merged_into"):
            continue
        if topic.id in hidden_topic_ids:
            continue
        similarity = sum(a * b for a, b in zip(embedding_row.embedding, user_vector))
        if ranker is not None:
            features = build_feature_vector(
                user_vector,
                embedding_row.embedding,
                newsletter,
                topic,
                preferences,
                user_topic_clicks,
                user_category_clicks,
                position=None,
            )
            score = float(ranker.predict_proba([features])[0][1])
        else:
            score = _score_item(similarity, newsletter.created_at, topic.popularity_count or 0)
        scored.append((score, newsletter, topic, embedding_row.embedding))

    scored.sort(key=lambda x: x[0], reverse=True)
    if settings.mmr_lambda and len(scored) > 1:
        max_candidates = min(settings.mmr_max_candidates, len(scored))
        remaining = scored[:max_candidates]
        reranked: List[Tuple[float, Newsletter, Topic, List[float]]] = []
        selected_vectors: List[List[float]] = []
        while remaining:
            best_idx = 0
            best_score = None
            for idx, (score, newsletter, topic, vector) in enumerate(remaining):
                if not selected_vectors:
                    mmr_score = score
                else:
                    max_sim = max(
                        sum(a * b for a, b in zip(vector, selected))
                        for selected in selected_vectors
                    )
                    mmr_score = settings.mmr_lambda * score - (1.0 - settings.mmr_lambda) * max_sim
                if best_score is None or mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx
            chosen = remaining.pop(best_idx)
            reranked.append(chosen)
            selected_vectors.append(chosen[3])
        scored = reranked + scored[max_candidates:]

    results: List[Dict] = []
    category_counts: Dict[str, int] = {}
    topic_counts: Dict[str, int] = {}
    for score, newsletter, topic, _ in scored:
        category = topic.category or "기타"
        if category_counts.get(category, 0) >= settings.max_per_category:
            continue
        if topic_counts.get(str(topic.id), 0) >= settings.max_per_topic:
            continue
        category_counts[category] = category_counts.get(category, 0) + 1
        topic_counts[str(topic.id)] = topic_counts.get(str(topic.id), 0) + 1
        reason = _build_reason(preferences, topic, newsletter, clicked_topic_ids)
        results.append(
            {
                "newsletter_id": str(newsletter.id),
                "topic_id": str(topic.id),
                "title": topic.title,
                "category": topic.category,
                "newsletter_text": newsletter.newsletter_text,
                "created_at": newsletter.created_at.isoformat(),
                "popularity_count": topic.popularity_count or 0,
                "reason": reason,
            }
        )
        if len(results) >= limit:
            break

    return results
