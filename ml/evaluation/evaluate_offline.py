import os
from collections import defaultdict
from datetime import datetime, timezone

import joblib
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.event import Event
from app.models.newsletter import Newsletter, NewsletterEmbedding
from app.models.topic import Topic
from app.models.user import UserPreferences
from app.services.embedding_service import EmbeddingService
from app.services.rec_features import build_feature_vector
from app.services.recommendation import _compute_user_embedding


def _load_session():
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://news:news_password@localhost:5432/news")
    engine = create_engine(db_url)
    return sessionmaker(bind=engine)()


def _metrics(ranked, positives, k=5):
    if not positives:
        return 0.0, 0.0, 0.0
    hits = [1 if item in positives else 0 for item in ranked[:k]]
    recall = sum(hits) / len(positives)
    dcg = sum(hit / np.log2(idx + 2) for idx, hit in enumerate(hits))
    ideal_hits = [1] * min(len(positives), k)
    idcg = sum(hit / np.log2(idx + 2) for idx, hit in enumerate(ideal_hits))
    ndcg = dcg / idcg if idcg > 0 else 0.0
    precision_sum = 0.0
    hit_count = 0
    for idx, hit in enumerate(hits, start=1):
        if hit:
            hit_count += 1
            precision_sum += hit_count / idx
    map_k = precision_sum / min(len(positives), k)
    return recall, ndcg, map_k


def main():
    session = _load_session()
    model_path = os.getenv("RANKER_MODEL_PATH", "ml/artifacts/ranker.pkl")
    if not os.path.exists(model_path):
        print("Model not found. Run ml/training/train_phase2.py first.")
        return
    model = joblib.load(model_path)

    embeddings = {row.newsletter_id: row.embedding for row in session.query(NewsletterEmbedding).all()}
    topics = {topic.id: topic for topic in session.query(Topic).all()}
    newsletters = {n.id: n for n in session.query(Newsletter).all()}
    preferences_map = {row.user_id: row for row in session.query(UserPreferences).all()}
    embedder = EmbeddingService()

    events = session.query(Event).order_by(Event.ts).all()
    if not events:
        print("No events available for evaluation.")
        return
    cutoff_index = max(int(len(events) * 0.8), 1)
    events = events[cutoff_index:]
    user_positive = defaultdict(set)
    user_candidates = defaultdict(set)
    user_topic_clicks = defaultdict(lambda: defaultdict(int))
    user_category_clicks = defaultdict(lambda: defaultdict(int))

    for event in events:
        if not event.user_id:
            continue
        if event.newsletter_id not in embeddings:
            continue
        user_candidates[event.user_id].add(event.newsletter_id)
        if event.event_type in {"click", "save", "follow"}:
            user_positive[event.user_id].add(event.newsletter_id)
            if event.topic_id in topics and topics[event.topic_id].category:
                user_category_clicks[event.user_id][topics[event.topic_id].category] += 1
            if event.topic_id:
                user_topic_clicks[event.user_id][str(event.topic_id)] += 1

    recalls = []
    ndcgs = []
    maps = []
    coverage_topics = set()
    diversity_scores = []
    for user_id, candidates in user_candidates.items():
        user_vector = None
        positives = user_positive[user_id]
        if positives:
            user_vector = np.mean([embeddings[nid] for nid in positives], axis=0)
        else:
            preferences = preferences_map.get(user_id)
            user_vector = _compute_user_embedding(preferences, embedder)
        scores = []
        for nid in candidates:
            item_vector = embeddings[nid]
            topic_id = newsletters[nid].topic_id
            topic = topics.get(topic_id)
            if not topic:
                continue
            preferences = preferences_map.get(user_id)
            features = build_feature_vector(
                user_vector.tolist() if hasattr(user_vector, "tolist") else user_vector,
                item_vector,
                newsletters[nid],
                topic,
                preferences,
                user_topic_clicks=dict(user_topic_clicks.get(user_id, {})),
                user_category_clicks=dict(user_category_clicks.get(user_id, {})),
                position=None,
            )
            score = model.predict_proba([features])[0][1]
            scores.append((nid, score))
        ranked = [nid for nid, _ in sorted(scores, key=lambda x: x[1], reverse=True)]
        recall, ndcg, map_k = _metrics(ranked, positives, k=5)
        recalls.append(recall)
        ndcgs.append(ndcg)
        maps.append(map_k)
        top_k = ranked[:5]
        for nid in top_k:
            coverage_topics.add(newsletters[nid].topic_id)
        categories = [topics[newsletters[nid].topic_id].category for nid in top_k if newsletters[nid].topic_id in topics]
        diversity_scores.append(len(set(categories)) / max(len(top_k), 1))

    total_topics = len(topics)
    coverage = len(coverage_topics) / total_topics if total_topics else 0.0
    print("Recall@5:", float(np.mean(recalls)) if recalls else 0.0)
    print("NDCG@5:", float(np.mean(ndcgs)) if ndcgs else 0.0)
    print("MAP@5:", float(np.mean(maps)) if maps else 0.0)
    print("Coverage@5:", coverage)
    print("Diversity@5:", float(np.mean(diversity_scores)) if diversity_scores else 0.0)


if __name__ == "__main__":
    main()
