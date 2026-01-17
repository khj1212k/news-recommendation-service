from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import feedparser
import httpx
import yaml


def _load_catalog(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"catalog not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _fetch_feed(url: str, timeout: float = 15.0) -> Tuple[int, List[Dict[str, Any]]]:
    headers = {"User-Agent": "NewsPipeline/1.0"}
    try:
        with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
            resp = client.get(url)
            status = resp.status_code
            if status != 200:
                return status, []
            parsed = feedparser.parse(resp.text)
            return status, list(parsed.entries)
    except Exception:
        return 0, []


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    catalog_path = repo_root / "docs" / "sources" / "rss_sources_catalog.yaml"
    catalog = _load_catalog(catalog_path)
    sources = catalog.get("news_sources", [])
    failures: List[str] = []

    for source in sources:
        name = source.get("display_name") or source.get("name") or "unknown"
        feeds = source.get("feeds", [])
        for feed in feeds:
            key = feed.get("key", "unknown")
            url = feed.get("url", "")
            if not url:
                continue
            status, entries = _fetch_feed(url)
            sample_titles = [e.get("title", "").strip() for e in entries[:2] if e.get("title")]
            print(f"{name}\t{key}\t{status}\tentries={len(entries)}\t{url}")
            if sample_titles:
                print(f"  samples: {sample_titles}")
            if status != 200:
                failures.append(f"{name}/{key} ({status}) {url}")

    if failures:
        print("\nFailed feeds:")
        for item in failures:
            print(f"- {item}")


if __name__ == "__main__":
    main()
