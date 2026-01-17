from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User, UserEmbedding, UserPreferences
from app.schemas.preferences import PreferencesIn, PreferencesOut
from app.services.embedding_service import EmbeddingService
from app.services.recommendation import _compute_user_embedding

router = APIRouter(prefix="/me", tags=["preferences"])


@router.get("/preferences", response_model=PreferencesOut)
def get_preferences(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()
    if not prefs:
        return PreferencesOut(categories=[], keywords=[])
    return PreferencesOut(categories=prefs.categories or [], keywords=prefs.keywords or [])


@router.post("/preferences", response_model=PreferencesOut)
def update_preferences(
    payload: PreferencesIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)
    prefs.categories = payload.categories or []
    prefs.keywords = payload.keywords or []
    prefs.updated_at = datetime.now(timezone.utc)

    embedder = EmbeddingService()
    vector = _compute_user_embedding(prefs, embedder)
    settings = get_settings()

    embedding_row = db.query(UserEmbedding).filter(UserEmbedding.user_id == current_user.id).first()
    if not embedding_row:
        embedding_row = UserEmbedding(user_id=current_user.id)
        db.add(embedding_row)
    embedding_row.model = settings.embedding_model
    embedding_row.dim = settings.embedding_dim
    embedding_row.embedding = vector
    embedding_row.updated_at = datetime.now(timezone.utc)

    db.commit()

    return PreferencesOut(categories=prefs.categories or [], keywords=prefs.keywords or [])
