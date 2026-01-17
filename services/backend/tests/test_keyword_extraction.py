from app.services.keyword_extraction import extract_keywords


def test_extract_keywords_returns_items():
    text = "정부는 중소기업 디지털 전환 지원금 신청 절차를 간소화한다고 발표했다."
    keywords = extract_keywords(text, top_k=5)
    assert keywords
    assert any("지원금" in keyword for keyword, _, _ in keywords)
