from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.feed import FeedResponse
from app.services.recommendation import get_personalized_feed

router = APIRouter(tags=["feed"])


@router.get("/feed", response_model=FeedResponse)
def get_feed(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = get_personalized_feed(db, current_user.id)
    return FeedResponse(items=items)
