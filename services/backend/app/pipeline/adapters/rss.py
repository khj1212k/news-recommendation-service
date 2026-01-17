from __future__ import annotations

from typing import Iterable, List, Optional

import feedparser
import httpx

from app.pipeline.adapters.base import ArticlePayload, BaseAdapter
from app.pipeline.fulltext import extract_fulltext
from app.pipeline.source_registry import SourceConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RssAdapter(BaseAdapter):
    def __init__(
        self,
        source: SourceConfig,
        timeout: float = 10.0,
        user_agent: str = "NewsPipeline/1.0",
    ) -> None:
        self.source = source
        self.timeout = timeout
        self.user_agent = user_agent

    def _fetch_html(self, url: str) -> str:
        headers = {"User-Agent": self.user_agent}
        with httpx.Client(timeout=self.timeout, headers=headers, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text

    def _extract_tags(self, entry) -> List[str]:
        tags = []
        for tag in entry.get("tags", []):
            term = tag.get("term") if isinstance(tag, dict) else None
            if term:
                tags.append(term)
        return tags

    def fetch(self) -> Iterable[ArticlePayload]:
        if not self.source.rss_url:
            logger.warning("rss url missing", extra={"extra": {"source": self.source.name}})
            return []
        feed = feedparser.parse(self.source.rss_url)
        entries = feed.entries[: self.source.max_items]
        for entry in entries:
            url = entry.get("link") or entry.get("id")
            if not url:
                continue
            title = entry.get("title", "")
            author = entry.get("author")
            published_at = entry.get("published") or entry.get("updated")
            try:
                html = self._fetch_html(url)
                if self.source.license_required_patterns:
                    matched = any(pattern in html for pattern in self.source.license_required_patterns)
                    if not matched:
                        logger.info(
                            "license check failed",
                            extra={"extra": {"source": self.source.name, "url": url}},
                        )
                        continue
                raw_text = extract_fulltext(html)
            except Exception as exc:
                logger.warning(
                    "failed to fetch article",
                    extra={"extra": {"source": self.source.name, "url": url, "error": str(exc)}},
                )
                raw_text = ""
            if not raw_text:
                continue
            metadata = {
                "category": self.source.category,
                "tags": self._extract_tags(entry),
                "source_type": "rss",
            }
            yield ArticlePayload(
                source_name=self.source.name,
                url=url,
                title=title,
                author=author,
                published_at=published_at,
                raw_text=raw_text,
                metadata=metadata,
            )
