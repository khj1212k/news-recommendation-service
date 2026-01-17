import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import EventType


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(Enum(EventType), nullable=False)
    newsletter_id = Column(UUID(as_uuid=True), ForeignKey("newsletters.id"), nullable=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    ts = Column(DateTime(timezone=True), default=datetime.utcnow)
    context = Column(JSONB, nullable=False, default=dict)
    value = Column(Float, nullable=True)

    user = relationship("User")
    newsletter = relationship("Newsletter")
    topic = relationship("Topic")
