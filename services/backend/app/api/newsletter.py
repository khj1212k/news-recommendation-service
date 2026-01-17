from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.article import Article
from app.models.newsletter import Newsletter, NewsletterCitation
from app.models.source import Source
from app.models.topic import Topic
from app.schemas.newsletter import NewsletterOut

router = APIRouter(tags=["newsletter"])


@router.get("/newsletter/{newsletter_id}", response_model=NewsletterOut)
def get_newsletter(newsletter_id: str, db: Session = Depends(get_db)):
    newsletter = db.query(Newsletter).filter(Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Newsletter not found")
    topic = db.query(Topic).filter(Topic.id == newsletter.topic_id).first()
    citations = (
        db.query(NewsletterCitation)
        .filter(NewsletterCitation.newsletter_id == newsletter.id)
        .order_by(NewsletterCitation.sentence_index)
        .all()
    )
    article_ids = {c.source_article_id for c in citations}
    articles = db.query(Article, Source).join(Source, Article.source_id == Source.id).filter(Article.id.in_(article_ids)).all()
    sources = []
    for article, source in articles:
        sources.append(
            {
                "id": str(article.id),
                "url": article.url,
                "title": article.title,
                "publisher": source.name,
                "published_at": article.published_at.isoformat() if article.published_at else None,
            }
        )

    citation_out = [
        {
            "sentence_index": c.sentence_index,
            "source_article_id": str(c.source_article_id),
            "source_excerpt": c.source_excerpt,
            "source_offset_start": c.source_offset_start,
            "source_offset_end": c.source_offset_end,
        }
        for c in citations
    ]

    return NewsletterOut(
        id=str(newsletter.id),
        topic_id=str(newsletter.topic_id),
        category=topic.category if topic else None,
        title=topic.title if topic else None,
        newsletter_text=newsletter.newsletter_text,
        created_at=newsletter.created_at.isoformat(),
        citations=citation_out,
        sources=sources,
    )
