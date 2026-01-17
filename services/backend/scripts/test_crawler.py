#!/usr/bin/env python
"""
CLI tool to test the newspaper crawler.

Usage:
    # Test catalog loading
    python -m scripts.test_crawler --list-sources

    # Test RSS parsing for a specific source
    python -m scripts.test_crawler --test-source "경향신문-all" --limit 3

    # Test fulltext extraction
    python -m scripts.test_crawler --test-url "https://www.khan.co.kr/..." --source "경향신문"
    
    # Fetch articles from all catalog sources (dry run)
    python -m scripts.test_crawler --fetch-all --limit 5 --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.pipeline.catalog_loader import load_catalog_sources, get_available_sources
from app.pipeline.adapters.newspaper import (
    NewspaperAdapter,
    extract_newspaper_fulltext,
    _detect_newspaper,
)
from app.pipeline.source_registry import SourceConfig


def list_sources() -> None:
    """List all available sources from the catalog."""
    sources = get_available_sources()
    print(f"\n📰 Available News Sources: {len(sources)}\n")
    print("-" * 80)
    
    # Group by newspaper
    by_paper = {}
    for s in sources:
        paper = s["name"].split("-")[0]
        if paper not in by_paper:
            by_paper[paper] = []
        by_paper[paper].append(s)
    
    for paper, feeds in by_paper.items():
        print(f"\n🗞️  {paper} ({len(feeds)} feeds)")
        for f in feeds:
            status = "✅" if f["enabled"] else "❌"
            print(f"   {status} {f['name']} [{f['category'] or '?'}]")


def test_source(source_name: str, limit: int = 3) -> None:
    """Test fetching from a specific source."""
    sources = load_catalog_sources()
    
    # Find matching source
    source = None
    for s in sources:
        if s.name == source_name or source_name in s.name:
            source = s
            break
    
    if not source:
        print(f"❌ Source not found: {source_name}")
        print("Available sources:")
        for s in sources[:10]:
            print(f"  - {s.name}")
        return
    
    print(f"\n🔍 Testing source: {source.name}")
    print(f"   RSS URL: {source.rss_url}")
    print(f"   Category: {source.category}")
    print("-" * 80)
    
    adapter = NewspaperAdapter(source, use_rate_limiter=True)
    
    count = 0
    for article in adapter.fetch():
        count += 1
        print(f"\n📄 Article {count}:")
        print(f"   Title: {article.title}")
        print(f"   URL: {article.url}")
        print(f"   Published: {article.published_at}")
        print(f"   Text length: {len(article.raw_text)} chars")
        print(f"   Preview: {article.raw_text[:200]}...")
        
        if count >= limit:
            break
    
    print(f"\n✅ Fetched {count} articles from {source.name}")


def test_url(url: str, source_name: str = "") -> None:
    """Test fulltext extraction from a URL."""
    import httpx
    
    print(f"\n🔍 Testing URL: {url}")
    
    # Detect newspaper
    newspaper = _detect_newspaper(source_name, url)
    print(f"   Detected newspaper: {newspaper or 'unknown'}")
    
    # Fetch HTML
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            })
            response.raise_for_status()
            html = response.text
    except Exception as e:
        print(f"❌ Failed to fetch: {e}")
        return
    
    print(f"   HTML length: {len(html)} chars")
    
    # Extract fulltext
    text = extract_newspaper_fulltext(html, source_name, url)
    
    print(f"   Extracted text length: {len(text)} chars")
    print("-" * 80)
    print(text[:1000])
    print("-" * 80)


def fetch_all(limit: int = 5, dry_run: bool = True) -> None:
    """Fetch articles from all catalog sources."""
    sources = load_catalog_sources()
    
    print(f"\n📰 Fetching from {len(sources)} sources (limit: {limit} per source)")
    if dry_run:
        print("   (DRY RUN - not saving to database)")
    print("-" * 80)
    
    total = 0
    for source in sources:
        adapter = NewspaperAdapter(source, use_rate_limiter=True)
        count = 0
        
        try:
            for article in adapter.fetch():
                count += 1
                total += 1
                
                if not dry_run:
                    # TODO: Save to database
                    pass
                
                if count >= limit:
                    break
        except Exception as e:
            print(f"   ❌ {source.name}: Error - {e}")
            continue
        
        print(f"   ✅ {source.name}: {count} articles")
    
    print(f"\n✅ Total: {total} articles fetched")


def main():
    parser = argparse.ArgumentParser(description="Test newspaper crawler")
    parser.add_argument("--list-sources", action="store_true", 
                        help="List all available sources")
    parser.add_argument("--test-source", type=str,
                        help="Test fetching from a specific source")
    parser.add_argument("--test-url", type=str,
                        help="Test fulltext extraction from a URL")
    parser.add_argument("--source", type=str, default="",
                        help="Source name for URL testing")
    parser.add_argument("--fetch-all", action="store_true",
                        help="Fetch from all sources")
    parser.add_argument("--limit", type=int, default=3,
                        help="Limit number of articles per source")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't save to database")
    
    args = parser.parse_args()
    
    if args.list_sources:
        list_sources()
    elif args.test_source:
        test_source(args.test_source, args.limit)
    elif args.test_url:
        test_url(args.test_url, args.source)
    elif args.fetch_all:
        fetch_all(args.limit, args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
