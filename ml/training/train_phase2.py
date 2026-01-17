import json
import os
import random
from datetime import datetime, timezone

import joblib
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sklearn.ensemble import HistGradientBoostingClassifier

from app.core.config import get_settings
from app.models.event import Event
from app.models.newsletter import Newsletter, NewsletterEmbedding
from app.models.topic import Topic
from app.models.user import User, UserEmbedding, UserPreferences
from app.services.embedding_service import EmbeddingService
from app.services.recommendation import _compute_user_embedding
from app.services.rec_features import FEATURE_NAMES, build_feature_vector


POSITIVE_EVENTS = {"click", "save", "follow"}
NEGATIVE_EVENTS = {"impression", "hide"}
DWELL_THRESHOLD_SECONDS = 20
NEGATIVE_SAMPLES_PER_POS = 3


def _load_session():
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://news:news_password@localhost:5432/news")
    engine = create_engine(db_url)
    return sessionmaker(bind=engine)()


def _build_synthetic_events(session, user_ids, newsletter_ids):
    for user_id in user_ids:
        chosen = random.sample(newsletter_ids, min(5, len(newsletter_ids)))
        for newsletter_id in chosen:
            session.add(
                Event(
                    user_id=user_id,
                    event_type="impression",
                    newsletter_id=newsletter_id,
                    ts=datetime.now(timezone.utc),
                    context={"synthetic": True},
                )
            )
            session.add(
                Event(
                    user_id=user_id,
                    event_type="click",
                    newsletter_id=newsletter_id,
                    ts=datetime.now(timezone.utc),
                    context={"synthetic": True},
                )
            )
    session.commit()


def _get_embeddings(session):
    embeddings = session.query(NewsletterEmbedding).all()
    return {row.newsletter_id: row.embedding for row in embeddings}


def _get_newsletters(session):
    newsletters = session.query(Newsletter).all()
    topics = {topic.id: topic for topic in session.query(Topic).all()}
    return {n.id: n for n in newsletters}, topics


def _label_event(event: Event) -> int | None:
    if event.event_type in POSITIVE_EVENTS:
        return 1
    if event.event_type == "dwell" and (event.value or 0) >= DWELL_THRESHOLD_SECONDS:
        return 1
    if event.event_type in NEGATIVE_EVENTS or event.event_type == "impression":
        return 0
    return None


def _build_user_vectors(session, embeddings, preferences_map):
    user_vectors = {}
    settings = get_settings()
    decay_hours = max(settings.user_embedding_decay_hours, 1)
    now = datetime.now(timezone.utc)
    for event in session.query(Event).filter(Event.event_type.in_(list(POSITIVE_EVENTS))).all():
        if not event.user_id:
            continue
        if event.newsletter_id not in embeddings:
            continue
        age_hours = max((now - event.ts).total_seconds() / 3600.0, 0.0) if event.ts else 0.0
        weight = np.exp(-age_hours / decay_hours)
        user_vectors.setdefault(event.user_id, []).append((embeddings[event.newsletter_id], weight))
    embedder = EmbeddingService()
    user_embeddings = {}
    for user_id, vectors in user_vectors.items():
        weights = np.array([w for _, w in vectors], dtype=float)
        matrix = np.array([v for v, _ in vectors], dtype=float)
        if weights.sum() == 0:
            user_embeddings[user_id] = np.mean(matrix, axis=0).tolist()
        else:
            user_embeddings[user_id] = (matrix * weights[:, None]).sum(axis=0).tolist()
    for user_id, preferences in preferences_map.items():
        if user_id not in user_embeddings:
            user_embeddings[user_id] = _compute_user_embedding(preferences, embedder)
    return user_embeddings


def _build_training_data(session, events):
    embeddings = _get_embeddings(session)
    newsletters, topics = _get_newsletters(session)
    preferences_map = {row.user_id: row for row in session.query(UserPreferences).all()}
    user_embeddings = _build_user_vectors(session, embeddings, preferences_map)

    user_topic_clicks: dict[str, dict[str, int]] = {}
    user_category_clicks: dict[str, dict[str, int]] = {}
    for event in session.query(Event).filter(Event.event_type.in_(list(POSITIVE_EVENTS))).all():
        if not event.user_id:
            continue
        if not event.topic_id:
            continue
        user_topic_clicks.setdefault(str(event.user_id), {})
        key = str(event.topic_id)
        user_topic_clicks[str(event.user_id)][key] = user_topic_clicks[str(event.user_id)].get(key, 0) + 1
        topic = topics.get(event.topic_id)
        if topic and topic.category:
            user_category_clicks.setdefault(str(event.user_id), {})
            user_category_clicks[str(event.user_id)][topic.category] = (
                user_category_clicks[str(event.user_id)].get(topic.category, 0) + 1
            )

    features = []
    labels = []

    for event in events:
        if not event.user_id:
            continue
        if event.newsletter_id not in embeddings or event.newsletter_id not in newsletters:
            continue
        label = _label_event(event)
        if label is None:
            continue
        newsletter = newsletters[event.newsletter_id]
        topic = topics.get(newsletter.topic_id)
        if not topic:
            continue
        user_vector = user_embeddings.get(event.user_id)
        preferences = preferences_map.get(event.user_id)
        clicks = user_topic_clicks.get(str(event.user_id), {})
        category_clicks = user_category_clicks.get(str(event.user_id), {})
        position = None
        if event.context and isinstance(event.context, dict):
            position = event.context.get("rank_position")
        vector = build_feature_vector(
            user_vector,
            embeddings[event.newsletter_id],
            newsletter,
            topic,
            preferences,
            clicks,
            category_clicks,
            position=position,
        )
        features.append(vector)
        labels.append(label)

    # Negative sampling for positives
    newsletter_ids = list(newsletters.keys())
    for event in events:
        if event.event_type not in POSITIVE_EVENTS:
            continue
        if not event.user_id:
            continue
        if event.newsletter_id not in embeddings:
            continue
        for _ in range(NEGATIVE_SAMPLES_PER_POS):
            sampled = random.choice(newsletter_ids)
            if sampled == event.newsletter_id:
                continue
            newsletter = newsletters.get(sampled)
            if not newsletter:
                continue
            topic = topics.get(newsletter.topic_id)
            if not topic:
                continue
            user_vector = user_embeddings.get(event.user_id)
            preferences = preferences_map.get(event.user_id)
            clicks = user_topic_clicks.get(str(event.user_id), {})
            category_clicks = user_category_clicks.get(str(event.user_id), {})
            vector = build_feature_vector(
                user_vector,
                embeddings[sampled],
                newsletter,
                topic,
                preferences,
                clicks,
                category_clicks,
                position=None,
            )
            features.append(vector)
            labels.append(0)

    return np.array(features), np.array(labels)


def _update_user_embeddings(session):
    settings = get_settings()
    decay_hours = max(settings.user_embedding_decay_hours, 1)
    now = datetime.now(timezone.utc)
    embeddings = _get_embeddings(session)
    events = session.query(Event).filter(Event.event_type.in_(list(POSITIVE_EVENTS))).all()
    user_vectors = {}
    for event in events:
        if not event.user_id:
            continue
        if event.newsletter_id not in embeddings:
            continue
        age_hours = max((now - event.ts).total_seconds() / 3600.0, 0.0) if event.ts else 0.0
        weight = np.exp(-age_hours / decay_hours)
        user_vectors.setdefault(event.user_id, []).append((embeddings[event.newsletter_id], weight))

    for user_id, vectors in user_vectors.items():
        weights = np.array([w for _, w in vectors], dtype=float)
        matrix = np.array([v for v, _ in vectors], dtype=float)
        if weights.sum() == 0:
            avg = np.mean(matrix, axis=0).tolist()
        else:
            avg = (matrix * weights[:, None]).sum(axis=0).tolist()
        row = session.query(UserEmbedding).filter(UserEmbedding.user_id == user_id).first()
        if not row:
            row = UserEmbedding(user_id=user_id, model="phase2-avg", dim=len(avg), embedding=avg)
            session.add(row)
        else:
            row.model = "phase2-avg"
            row.dim = len(avg)
            row.embedding = avg
    session.commit()


def main():
    session = _load_session()
    events = session.query(Event).order_by(Event.ts).all()
    if not events:
        users = session.query(User).all()
        newsletters = session.query(Newsletter).all()
        if not users or not newsletters:
            print("No training data available.")
            return
        _build_synthetic_events(session, [u.id for u in users], [n.id for n in newsletters])
        events = session.query(Event).order_by(Event.ts).all()

    cutoff_index = max(int(len(events) * 0.8), 1)
    train_events = events[:cutoff_index]

    features, labels = _build_training_data(session, train_events)
    if features.size == 0:
        print("No training data available.")
        return
    model = HistGradientBoostingClassifier(max_depth=6, learning_rate=0.1)
    model.fit(features, labels)
    model_path = os.getenv("RANKER_MODEL_PATH", "ml/artifacts/ranker.pkl")
    meta_path = os.getenv("RANKER_META_PATH", "ml/artifacts/ranker_meta.json")
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)
    with open(meta_path, "w", encoding="utf-8") as handle:
        json.dump({"features": FEATURE_NAMES}, handle, ensure_ascii=False, indent=2)
    _update_user_embeddings(session)
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
