from app.pipeline.topic_utils import should_assign_topic


def test_topic_assignment_threshold():
    assert should_assign_topic(0.8, 0.78) is True
    assert should_assign_topic(0.5, 0.78) is False
