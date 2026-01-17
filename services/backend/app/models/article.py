import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    url = Column(String, unique=True, nullable=False)
    url_canonical = Column(String, nullable=True)
    title = Column(String, nullable=True)
    author = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    language = Column(String, nullable=True)
    raw_text = Column(Text, nullable=True)
    clean_text = Column(Text, nullable=True)
    content_hash = Column(String, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)

    source = relationship("Source")


class ArticleKeyword(Base):
    __tablename__ = "article_keywords"

    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), primary_key=True)
    keyword = Column(String, primary_key=True)
    method = Column(String, primary_key=True)
    score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    article = relationship("Article")


Index("ix_articles_published_at", Article.published_at)
Index("ix_articles_url_canonical", Article.url_canonical)
Index("ix_articles_content_hash", Article.content_hash)
Index("ix_article_keywords_keyword", ArticleKeyword.keyword)
