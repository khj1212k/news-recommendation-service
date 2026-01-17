import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=True)
    category = Column(String, nullable=True)
    first_seen_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    popularity_count = Column(Integer, nullable=False, default=0)
    centroid_embedding = Column(Vector(384), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)


class TopicArticle(Base):
    __tablename__ = "topic_articles"

    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), primary_key=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    score = Column(Float, nullable=True)

    topic = relationship("Topic")
    article = relationship("Article")


Index("ix_topics_last_updated_at", Topic.last_updated_at)
Index("ix_topics_category", Topic.category)
