from datetime import datetime, timezone
import uuid

from app.models.newsletter import Newsletter
from app.models.topic import Topic
from app.services.rec_features import FEATURE_NAMES, build_feature_vector


def test_build_feature_vector_length():
    topic = Topic(
        id=uuid.uuid4(),
        title="테스트",
        category="사회",
        first_seen_at=datetime.now(timezone.utc),
        last_updated_at=datetime.now(timezone.utc),
        popularity_count=3,
        centroid_embedding=None,
        metadata_={},
    )
    newsletter = Newsletter(
        id=uuid.uuid4(),
        topic_id=topic.id,
        newsletter_text="테스트 뉴스레터",
        content_hash="hash",
        llm_model="model",
        prompt_version="v2",
        status="ok",
        metadata_={},
    )
    newsletter.created_at = datetime.now(timezone.utc)
    vector = build_feature_vector(
        user_vector=[0.1, 0.2],
        item_vector=[0.1, 0.2],
        newsletter=newsletter,
        topic=topic,
        preferences=None,
        user_topic_clicks={},
        user_category_clicks={},
        position=2,
    )
    assert len(vector) == len(FEATURE_NAMES)
