from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.newsletter import Newsletter
from app.models.topic import Topic
from app.schemas.topic import PopularTopicsResponse

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/popular", response_model=PopularTopicsResponse)
def get_popular_topics(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Topic).filter(Topic.popularity_count > 0)
    if category:
        query = query.filter(Topic.category == category)
    topics = query.order_by(Topic.popularity_count.desc()).limit(50).all()

    items = []
    for topic in topics:
        if topic.metadata_ and topic.metadata_.get("merged_into"):
            continue
        latest_newsletter = (
            db.query(Newsletter)
            .filter(Newsletter.topic_id == topic.id)
            .order_by(Newsletter.created_at.desc())
            .first()
        )
        items.append(
            {
                "topic_id": str(topic.id),
                "title": topic.title,
                "category": topic.category,
                "popularity_count": topic.popularity_count,
                "newsletter_id": str(latest_newsletter.id) if latest_newsletter else None,
                "newsletter_text": latest_newsletter.newsletter_text if latest_newsletter else None,
                "created_at": latest_newsletter.created_at.isoformat() if latest_newsletter else None,
            }
        )
    return PopularTopicsResponse(items=items)
