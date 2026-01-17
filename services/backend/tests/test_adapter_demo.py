from types import SimpleNamespace

import feedparser

from app.pipeline.adapters.rss import RssAdapter
from app.pipeline.source_registry import SourceConfig


def test_rss_adapter_extracts_fulltext(monkeypatch):
    source = SourceConfig(
        name="테스트소스",
        adapter="rss",
        rss_url="https://example.com/feed.xml",
        base_url="https://example.com",
        terms_url="https://example.com/terms",
        allow_fulltext=True,
        allow_derivatives=True,
        category="사회",
        license_required_patterns=["공공누리"],
    )
    adapter = RssAdapter(source)
    fake_feed = SimpleNamespace(entries=[{"link": "https://example.com/news/1", "title": "테스트", "published": "2024-01-01"}])
    monkeypatch.setattr(feedparser, "parse", lambda *_args, **_kwargs: fake_feed)
    monkeypatch.setattr(adapter, "_fetch_html", lambda *_args, **_kwargs: "<article>공공누리 테스트 기사 본문입니다.</article>")
    items = list(adapter.fetch())
    assert items
    first = items[0]
    assert first.url == "https://example.com/news/1"
    assert "테스트 기사" in first.raw_text
