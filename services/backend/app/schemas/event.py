from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.models.enums import EventType


class EventIn(BaseModel):
    event_type: EventType
    newsletter_id: Optional[str] = None
    topic_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    value: Optional[float] = None
