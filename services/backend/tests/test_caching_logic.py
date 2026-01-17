from app.pipeline.hash_utils import topic_content_hash


def test_topic_content_hash_stable():
    hashes = ["a", "b", "c"]
    h1 = topic_content_hash(hashes)
    h2 = topic_content_hash(list(reversed(hashes)))
    assert h1 == h2
    h3 = topic_content_hash(["a", "b", "d"])
    assert h1 != h3
