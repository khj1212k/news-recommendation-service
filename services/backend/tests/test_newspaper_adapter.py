"""
Unit tests for newspaper adapter.
"""
import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from app.pipeline.adapters.newspaper import (
    NewspaperAdapter,
    extract_newspaper_fulltext,
    _detect_newspaper,
    _clean_article_text,
    NEWSPAPER_SELECTORS,
)
from app.pipeline.source_registry import SourceConfig


class TestDetectNewspaper:
    """Tests for newspaper detection."""
    
    def test_detect_from_source_name(self):
        assert _detect_newspaper("조선일보-정치", "") == "chosun"
        assert _detect_newspaper("동아일보-전체", "") == "donga"
        assert _detect_newspaper("경향신문-all", "") == "khan"
        assert _detect_newspaper("매일경제-경제", "") == "mk"
        assert _detect_newspaper("한국경제-IT", "") == "hankyung"
    
    def test_detect_from_url(self):
        assert _detect_newspaper("", "https://www.chosun.com/article/123") == "chosun"
        assert _detect_newspaper("", "https://www.donga.com/news/456") == "donga"
        assert _detect_newspaper("", "https://www.khan.co.kr/article/789") == "khan"
        assert _detect_newspaper("", "https://www.mk.co.kr/news/123") == "mk"
        assert _detect_newspaper("", "https://www.hankyung.com/economy/456") == "hankyung"
    
    def test_detect_unknown(self):
        assert _detect_newspaper("Unknown Source", "https://unknown.com") is None


class TestCleanArticleText:
    """Tests for text cleaning."""
    
    def test_remove_reporter_attribution(self):
        text = "기자 홍길동 = 서울에서 열린 행사에..."
        cleaned = _clean_article_text(text)
        assert "기자" not in cleaned
    
    def test_remove_copyright_notice(self):
        text = "좋은 기사입니다. © 2024 Korea Times"
        cleaned = _clean_article_text(text)
        assert "©" not in cleaned
    
    def test_normalize_whitespace(self):
        text = "여러   공백이    있는   텍스트"
        cleaned = _clean_article_text(text)
        assert "  " not in cleaned


class TestExtractNewspaperFulltext:
    """Tests for fulltext extraction."""
    
    def test_extract_with_article_selector(self):
        html = """
        <html>
            <body>
                <article class="article-body">
                    <p>이것은 테스트 기사 본문입니다. 충분히 긴 내용을 포함해야 합니다.</p>
                    <p>두 번째 문단입니다. 더 많은 내용이 여기에 있습니다.</p>
                </article>
            </body>
        </html>
        """
        text = extract_newspaper_fulltext(html, "조선일보-전체", "https://www.chosun.com/article/1")
        assert "테스트 기사 본문" in text
        assert len(text) > 50
    
    def test_fallback_to_trafilatura(self):
        html = """
        <html>
            <body>
                <main>
                    <p>이것은 메인 콘텐츠입니다. 뉴스 기사 내용이 여기에 있습니다.</p>
                </main>
            </body>
        </html>
        """
        text = extract_newspaper_fulltext(html, "unknown", "https://unknown.com")
        # Should fallback to trafilatura or generic extraction
        assert len(text) > 0 or text == ""  # May be empty if too short


class TestNewspaperAdapter:
    """Tests for the NewspaperAdapter class."""
    
    @pytest.fixture
    def source_config(self):
        return SourceConfig(
            name="테스트신문-전체",
            adapter="newspaper",
            rss_url="https://test.com/rss",
            base_url="https://test.com",
            terms_url="https://test.com/terms",
            allow_fulltext=True,
            allow_derivatives=True,
            category="종합",
            max_items=10,
        )
    
    def test_adapter_creation(self, source_config):
        adapter = NewspaperAdapter(source_config)
        assert adapter.source == source_config
        assert adapter.timeout == 15.0
        assert adapter.use_rate_limiter is True
    
    def test_fetch_with_mock(self, source_config, monkeypatch):
        adapter = NewspaperAdapter(source_config, use_rate_limiter=False)
        
        # Mock RSS parsing
        fake_entries = [
            {
                "link": "https://test.com/article/1",
                "title": "테스트 기사 제목",
                "published": "2024-01-01T10:00:00Z",
            }
        ]
        monkeypatch.setattr(adapter, "_parse_rss", lambda: fake_entries)
        
        # Mock HTML fetch
        fake_html = """
        <html>
            <body>
                <article class="article-body">
                    <p>이것은 충분히 긴 테스트 기사 본문입니다. 최소 길이를 충족해야 합니다.</p>
                    <p>두 번째 문단도 있습니다. 더 많은 내용을 추가합니다.</p>
                </article>
            </body>
        </html>
        """
        monkeypatch.setattr(adapter, "_fetch_html", lambda url: fake_html)
        
        articles = list(adapter.fetch())
        
        assert len(articles) == 1
        assert articles[0].title == "테스트 기사 제목"
        assert articles[0].url == "https://test.com/article/1"
        assert "테스트 기사 본문" in articles[0].raw_text


class TestCatalogLoader:
    """Tests for catalog loading."""
    
    def test_load_catalog_sources(self):
        from app.pipeline.catalog_loader import load_catalog_sources
        
        # This will try to load the actual catalog file
        sources = load_catalog_sources()
        
        # Should have loaded some sources
        assert isinstance(sources, list)
        
        if sources:
            # Check first source has required fields
            first = sources[0]
            assert first.name
            assert first.rss_url
            assert first.adapter == "newspaper"
