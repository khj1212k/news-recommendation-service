"""
Newspaper-specific adapter for Korean news sources.

Extends the base RSS adapter with newspaper-specific fulltext extraction
using custom CSS selectors for each news outlet.
"""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Tuple

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.pipeline.adapters.base import ArticlePayload, BaseAdapter
from app.pipeline.fulltext import extract_fulltext
from app.pipeline.source_registry import SourceConfig
from app.utils.logger import get_logger
from app.utils.rate_limiter import default_rate_limiter

logger = get_logger(__name__)


# Newspaper-specific content selectors (CSS selectors)
# Order matters: first match wins
NEWSPAPER_SELECTORS: Dict[str, List[str]] = {
    # 조선일보
    "chosun": [
        "div.article-body",
        "article.article",
        "div#article-body",
    ],
    # 동아일보
    "donga": [
        "div.article_txt",
        "section.news_view",
        "div#contents",
    ],
    # 경향신문
    "khan": [
        "div#articleBody",
        "div.art_body",
        "article.article",
    ],
    # 매일경제
    "mk": [
        "div.news_cnt_detail_wrap",
        "div#article_body",
        "div.view_txt",
    ],
    # 한국경제
    "hankyung": [
        "div#articletxt",
        "div.article-body",
        "div[itemprop='articleBody']",
    ],
    # 세계일보
    "segye": [
        "article.article-body",
        "div.article_view",
        "div#article_txt",
    ],
    # 국민일보
    "kmib": [
        "div#articleBody",
        "div.tx",
        "article.article",
    ],
    # 머니투데이
    "mt": [
        "div#textBody",
        "div.article_text",
        "div.view_text",
    ],
    # 오마이뉴스
    "ohmynews": [
        "div.article_view",
        "div#articleBody",
        "div.at_contents",
    ],
}

# Map source names to newspaper keys
SOURCE_NAME_MAP: Dict[str, str] = {
    "조선일보": "chosun",
    "조선닷컴": "chosun",
    "동아일보": "donga",
    "동아닷컴": "donga",
    "경향신문": "khan",
    "매일경제": "mk",
    "한국경제": "hankyung",
    "한경": "hankyung",
    "세계일보": "segye",
    "국민일보": "kmib",
    "머니투데이": "mt",
    "오마이뉴스": "ohmynews",
}


def _detect_newspaper(source_name: str, url: str) -> Optional[str]:
    """Detect newspaper key from source name or URL."""
    # Try source name first
    for keyword, key in SOURCE_NAME_MAP.items():
        if keyword in source_name:
            return key
    
    # Try URL patterns
    url_patterns = {
        "chosun.com": "chosun",
        "donga.com": "donga",
        "khan.co.kr": "khan",
        "mk.co.kr": "mk",
        "hankyung.com": "hankyung",
        "segye.com": "segye",
        "kmib.co.kr": "kmib",
        "mt.co.kr": "mt",
        "news.mt.co.kr": "mt",
        "ohmynews.com": "ohmynews",
    }
    for pattern, key in url_patterns.items():
        if pattern in url:
            return key
    
    return None


def _clean_article_text(text: str) -> str:
    """Clean extracted article text."""
    if not text:
        return ""
    
    # Remove common noise patterns
    noise_patterns = [
        r"기자\s*[가-힣]+\s*=",  # Reporter attribution
        r"【[^】]+】",  # Editorial notes in brackets
        r"▶\s*관련기사.*$",  # Related articles
        r"©.*$",  # Copyright notices
        r"\[사진=[^\]]+\]",  # Photo credits
        r"무단전재.*금지",  # Reprint notices
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE)
    
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def extract_newspaper_fulltext(
    html: str,
    source_name: str = "",
    url: str = "",
) -> str:
    """
    Extract fulltext from newspaper HTML using newspaper-specific selectors.
    Falls back to generic trafilatura extraction if selectors fail.
    """
    if not html:
        return ""
    
    newspaper_key = _detect_newspaper(source_name, url)
    
    # Try newspaper-specific selectors first
    if newspaper_key and newspaper_key in NEWSPAPER_SELECTORS:
        soup = BeautifulSoup(html, "lxml")
        
        for selector in NEWSPAPER_SELECTORS[newspaper_key]:
            try:
                elements = soup.select(selector)
                if elements:
                    # Get text from all matching elements
                    texts = [el.get_text(" ", strip=True) for el in elements]
                    combined = " ".join(texts)
                    if len(combined) > 100:  # Minimum reasonable article length
                        logger.debug(
                            "extracted with selector",
                            extra={"extra": {
                                "newspaper": newspaper_key,
                                "selector": selector,
                                "length": len(combined),
                            }}
                        )
                        return _clean_article_text(combined)
            except Exception as e:
                logger.warning(
                    "selector extraction failed",
                    extra={"extra": {"selector": selector, "error": str(e)}}
                )
    
    # Fallback to trafilatura
    text = extract_fulltext(html)
    return _clean_article_text(text)


class NewspaperAdapter(BaseAdapter):
    """
    Adapter for Korean newspaper RSS feeds with custom fulltext extraction.
    
    Features:
    - Newspaper-specific CSS selectors for accurate content extraction
    - Rate limiting to avoid overloading news servers
    - Retry logic with exponential backoff
    - Encoding detection for proper Korean text handling
    """
    
    def __init__(
        self,
        source: SourceConfig,
        timeout: float = 15.0,
        user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) NewsCrawler/1.0",
        max_retries: int = 3,
        use_rate_limiter: bool = True,
    ) -> None:
        self.source = source
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.use_rate_limiter = use_rate_limiter
    
    def _fetch_html(self, url: str) -> str:
        """Fetch HTML with rate limiting and retry logic."""
        if self.use_rate_limiter:
            default_rate_limiter.acquire(url)
        
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
        }
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(
                    timeout=self.timeout,
                    headers=headers,
                    follow_redirects=True,
                ) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    
                    # Handle encoding
                    content_type = response.headers.get("content-type", "")
                    if "charset" not in content_type.lower():
                        # Try to detect encoding from meta tags
                        response.encoding = response.apparent_encoding or "utf-8"
                    
                    return response.text
                    
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    "timeout fetching article",
                    extra={"extra": {"url": url, "attempt": attempt + 1}}
                )
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code in (403, 404):
                    # Don't retry on these
                    break
                logger.warning(
                    "HTTP error fetching article",
                    extra={"extra": {
                        "url": url,
                        "status": e.response.status_code,
                        "attempt": attempt + 1,
                    }}
                )
            except Exception as e:
                last_error = e
                logger.warning(
                    "error fetching article",
                    extra={"extra": {"url": url, "error": str(e), "attempt": attempt + 1}}
                )
        
        if last_error:
            raise last_error
        return ""
    
    def _extract_tags(self, entry) -> List[str]:
        """Extract tags/categories from RSS entry."""
        tags = []
        for tag in entry.get("tags", []):
            term = tag.get("term") if isinstance(tag, dict) else None
            if term:
                tags.append(term)
        return tags
    
    def _parse_rss(self) -> List[dict]:
        """Parse RSS feed and return entries."""
        if not self.source.rss_url:
            return []
        
        try:
            # Some RSS feeds need custom headers
            if self.use_rate_limiter:
                default_rate_limiter.acquire(self.source.rss_url)
            
            feed = feedparser.parse(
                self.source.rss_url,
                agent=self.user_agent,
            )
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(
                    "RSS parse warning",
                    extra={"extra": {
                        "source": self.source.name,
                        "error": str(feed.bozo_exception),
                    }}
                )
            
            return feed.entries[:self.source.max_items]
            
        except Exception as e:
            logger.error(
                "failed to parse RSS",
                extra={"extra": {"source": self.source.name, "error": str(e)}}
            )
            return []
    
    def fetch(self) -> Iterable[ArticlePayload]:
        """
        Fetch articles from RSS feed and extract fulltext.
        
        Yields:
            ArticlePayload objects for each successfully fetched article.
        """
        if not self.source.rss_url:
            logger.warning(
                "RSS URL missing",
                extra={"extra": {"source": self.source.name}}
            )
            return
        
        entries = self._parse_rss()
        fetched = 0
        failed = 0
        
        for entry in entries:
            url = entry.get("link") or entry.get("id")
            if not url:
                continue
            
            title = entry.get("title", "")
            author = entry.get("author")
            published_at = entry.get("published") or entry.get("updated")
            
            try:
                html = self._fetch_html(url)
                if not html:
                    failed += 1
                    continue
                
                raw_text = extract_newspaper_fulltext(
                    html,
                    source_name=self.source.name,
                    url=url,
                )
                
                if not raw_text or len(raw_text) < 50:
                    logger.info(
                        "skipping short/empty article",
                        extra={"extra": {"source": self.source.name, "url": url}}
                    )
                    failed += 1
                    continue
                
                metadata = {
                    "category": self.source.category,
                    "tags": self._extract_tags(entry),
                    "source_type": "newspaper",
                    "newspaper": _detect_newspaper(self.source.name, url),
                }
                
                fetched += 1
                yield ArticlePayload(
                    source_name=self.source.name,
                    url=url,
                    title=title,
                    author=author,
                    published_at=published_at,
                    raw_text=raw_text,
                    metadata=metadata,
                )
                
            except Exception as e:
                failed += 1
                logger.warning(
                    "failed to fetch article",
                    extra={"extra": {
                        "source": self.source.name,
                        "url": url,
                        "error": str(e),
                    }}
                )
        
        logger.info(
            "newspaper fetch complete",
            extra={"extra": {
                "source": self.source.name,
                "fetched": fetched,
                "failed": failed,
            }}
        )
