import re
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer


KOREAN_WORD_RE = re.compile(r"[가-힣]{2,}")
STOPWORDS = {"그리고", "하지만", "또한", "대한", "위해", "이번", "관련", "있는", "한다", "했다", "것이다", "있다"}


def _extract_keyphrases(text: str, top_k: int = 10) -> List[Tuple[str, float]]:
    if not text:
        return []
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=2000)
    tfidf = vectorizer.fit_transform([text])
    scores = tfidf.toarray()[0]
    terms = vectorizer.get_feature_names_out()
    ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
    results = [(term, float(score)) for term, score in ranked if term]
    return results[:top_k]


def _extract_entities(text: str, top_k: int = 10) -> List[Tuple[str, float]]:
    if not text:
        return []
    matches = KOREAN_WORD_RE.findall(text)
    candidates = [m for m in matches if m not in STOPWORDS]
    if not candidates:
        return []
    counts = {}
    first_index = {}
    for idx, term in enumerate(candidates):
        counts[term] = counts.get(term, 0) + 1
        if term not in first_index:
            first_index[term] = idx
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], first_index[kv[0]]))
    return [(term, float(counts[term])) for term, _ in ranked[:top_k]]


def extract_keywords(text: str, top_k: int = 10) -> List[Tuple[str, float, str]]:
    keyphrases = _extract_keyphrases(text, top_k=top_k)
    entities = _extract_entities(text, top_k=top_k)
    seen = set()
    combined: List[Tuple[str, float, str]] = []
    for term, score in keyphrases:
        normalized = re.sub(r"[\W_]+", "", term).strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            combined.append((normalized, score, "tfidf"))
    for term, score in entities:
        normalized = re.sub(r"[\W_]+", "", term).strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            combined.append((normalized, score, "ner"))
    return combined
