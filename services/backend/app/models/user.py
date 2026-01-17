import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    categories = Column(ARRAY(String), nullable=True)
    keywords = Column(ARRAY(String), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User")


class UserEmbedding(Base):
    __tablename__ = "user_embeddings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    model = Column(String, nullable=False)
    dim = Column(Integer, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User")
