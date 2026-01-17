import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import NewsletterStatus


class Newsletter(Base):
    __tablename__ = "newsletters"
    __table_args__ = (UniqueConstraint("topic_id", "content_hash", name="uq_newsletter_topic_hash"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False)
    newsletter_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    content_hash = Column(String, nullable=False)
    llm_model = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    status = Column(Enum(NewsletterStatus), nullable=False, default=NewsletterStatus.ok)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)

    topic = relationship("Topic")


class NewsletterCitation(Base):
    __tablename__ = "newsletter_citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    newsletter_id = Column(UUID(as_uuid=True), ForeignKey("newsletters.id"), nullable=False)
    sentence_index = Column(Integer, nullable=False)
    source_article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)
    source_excerpt = Column(Text, nullable=False)
    source_offset_start = Column(Integer, nullable=True)
    source_offset_end = Column(Integer, nullable=True)

    newsletter = relationship("Newsletter")


class NewsletterEmbedding(Base):
    __tablename__ = "newsletter_embeddings"

    newsletter_id = Column(UUID(as_uuid=True), ForeignKey("newsletters.id"), primary_key=True)
    model = Column(String, nullable=False)
    dim = Column(Integer, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    content_hash = Column(String, nullable=False)

    newsletter = relationship("Newsletter")


Index("ix_newsletters_topic_id", Newsletter.topic_id)
Index("ix_newsletters_created_at", Newsletter.created_at)
Index("ix_newsletters_content_hash", Newsletter.content_hash)
