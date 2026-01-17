from typing import List

from app.utils.text_utils import content_hash


def topic_content_hash(article_hashes: List[str]) -> str:
    normalized = "|".join(sorted(article_hashes))
    return content_hash(normalized)
