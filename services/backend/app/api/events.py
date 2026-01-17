from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.db.session import get_db
from app.models.event import Event
from app.schemas.event import EventIn

router = APIRouter(tags=["events"])


@router.post("/events")
def log_event(
    payload: EventIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    event = Event(
        user_id=current_user.id if current_user else None,
        event_type=payload.event_type,
        newsletter_id=payload.newsletter_id,
        topic_id=payload.topic_id,
        ts=datetime.now(timezone.utc),
        context=payload.context or {},
        value=payload.value,
    )
    db.add(event)
    db.commit()
    return {"status": "ok"}
