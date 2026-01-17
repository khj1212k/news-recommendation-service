from typing import List


def cosine_similarity(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def should_assign_topic(similarity: float, threshold: float) -> bool:
    return similarity >= threshold
