from typing import Iterable, Optional
from urllib.parse import parse_qsl, urlparse, urlunparse

from rapidfuzz import fuzz


TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref"}


def canonicalize_url(url: str) -> str:
    if not url:
        return url
    parsed = urlparse(url)
    query_params = [(k, v) for k, v in parse_qsl(parsed.query) if k not in TRACKING_PARAMS]
    canonical = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        query="&".join([f"{k}={v}" for k, v in query_params]),
        fragment="",
    )
    return urlunparse(canonical)


def find_near_duplicate(text: str, candidates: Iterable[str], threshold: float) -> Optional[int]:
    for idx, candidate in enumerate(candidates):
        score = fuzz.token_set_ratio(text, candidate) / 100.0
        if score >= threshold:
            return idx
    return None
