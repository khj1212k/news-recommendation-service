from app.utils.dedup import canonicalize_url, find_near_duplicate


def test_canonicalize_url_strips_tracking():
    url = "https://Example.com/news?id=1&utm_source=test#section"
    canonical = canonicalize_url(url)
    assert "utm_source" not in canonical
    assert canonical.startswith("https://example.com")


def test_near_duplicate_detection():
    text = "서울에서 열린 행사에서 예산 확대가 논의됐다."
    candidates = ["서울에서 열린 행사에서 예산 확대가 논의됐다!", "완전히 다른 문장"]
    idx = find_near_duplicate(text, candidates, 0.9)
    assert idx == 0
