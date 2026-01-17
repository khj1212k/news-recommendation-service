from __future__ import annotations

from datetime import datetime, timezone
from math import log1p
from typing import Dict, List, Optional

from app.models.newsletter import Newsletter
from app.models.topic import Topic
from app.models.user import UserPreferences


FEATURE_NAMES = [
    "similarity",
    "recency_hours",
    "popularity_log",
    "user_topic_clicks",
    "category_match",
    "keyword_overlap",
    "position",
    "topic_age_hours",
    "newsletter_length",
    "user_category_clicks",
]


def build_feature_vector(
    user_vector: Optional[List[float]],
    item_vector: List[float],
    newsletter: Newsletter,
    topic: Topic,
    preferences: Optional[UserPreferences],
    user_topic_clicks: Dict[str, int],
    user_category_clicks: Optional[Dict[str, int]] = None,
    position: Optional[int] = None,
) -> List[float]:
    similarity = float(sum(a * b for a, b in zip(user_vector or [], item_vector))) if user_vector else 0.0
    now_seconds = datetime.now(timezone.utc).timestamp()
    created_at = newsletter.created_at or datetime.now(timezone.utc)
    recency_hours = max((now_seconds - created_at.timestamp()) / 3600.0, 0.0)
    popularity = log1p(topic.popularity_count or 0)
    topic_key = str(topic.id)
    topic_clicks = float(user_topic_clicks.get(topic_key, 0))
    categories = set(preferences.categories or []) if preferences else set()
    category_match = 1.0 if topic.category and topic.category in categories else 0.0
    keywords = set(preferences.keywords or []) if preferences else set()
    newsletter_text = (newsletter.newsletter_text or "").lower()
    keyword_overlap = float(sum(1 for keyword in keywords if keyword and keyword.lower() in newsletter_text))
    position_value = float(position or 0)
    topic_base = topic.last_updated_at or topic.first_seen_at or datetime.now(timezone.utc)
    topic_age_hours = max((now_seconds - topic_base.timestamp()) / 3600.0, 0.0)
    newsletter_length = float(len(newsletter.newsletter_text or ""))
    category_key = topic.category or ""
    category_clicks = float((user_category_clicks or {}).get(category_key, 0))
    return [
        similarity,
        recency_hours,
        popularity,
        topic_clicks,
        category_match,
        keyword_overlap,
        position_value,
        topic_age_hours,
        newsletter_length,
        category_clicks,
    ]
