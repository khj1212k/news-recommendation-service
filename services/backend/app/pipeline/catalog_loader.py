"""
Catalog loader for rss_sources_catalog.yaml format.

Converts the extended catalog format into SourceConfig objects
compatible with the existing pipeline.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml

from app.pipeline.source_registry import SourceConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


def load_catalog_sources(path_str: str | None = None) -> List[SourceConfig]:
    """
    Load news sources from rss_sources_catalog.yaml format.
    
    Args:
        path_str: Path to the catalog YAML file.
                  Defaults to docs/sources/rss_sources_catalog.yaml
    
    Returns:
        List of SourceConfig objects ready for use with adapters.
    """
    if path_str:
        catalog_path = Path(path_str)
    else:
        # Default: look for catalog relative to project root
        base_dir = Path(__file__).resolve().parents[3]  # services/backend -> project root
        catalog_path = base_dir / "docs" / "sources" / "rss_sources_catalog.yaml"
    
    if not catalog_path.exists():
        logger.warning("catalog file not found", extra={"extra": {"path": str(catalog_path)}})
        return []
    
    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    news_sources = data.get("news_sources", [])
    
    configs: List[SourceConfig] = []
    
    for source in news_sources:
        if not isinstance(source, dict):
            continue
        
        source_name = source.get("name", "")
        display_name = source.get("display_name", source_name)
        list_page = source.get("list_page", "")
        feeds = source.get("feeds", [])
        notes = source.get("notes", [])
        
        if not feeds:
            continue
        
        # Extract base URL from list_page or first feed URL
        base_url = list_page
        if not base_url and feeds:
            first_url = feeds[0].get("url", "")
            if first_url:
                from urllib.parse import urlparse
                parsed = urlparse(first_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Create a config for each feed
        for feed in feeds:
            if not isinstance(feed, dict):
                continue
            
            feed_key = feed.get("key", "all")
            feed_url = feed.get("url", "")
            
            if not feed_url:
                continue
            
            # Construct unique source name
            full_name = f"{display_name}-{feed_key}"
            
            # Default to newspaper adapter for all catalog sources
            config = SourceConfig(
                name=full_name,
                adapter="newspaper",  # Use newspaper adapter
                rss_url=feed_url,
                base_url=base_url,
                terms_url=list_page,
                allow_fulltext=True,
                allow_derivatives=True,
                category=_infer_category_from_key(feed_key),
                language="ko",
                enabled=True,
                max_items=50,
                license_required_patterns=[],
            )
            configs.append(config)
    
    logger.info(
        "loaded catalog sources",
        extra={"extra": {"count": len(configs), "path": str(catalog_path)}}
    )
    return configs


def _infer_category_from_key(key: str) -> Optional[str]:
    """Map feed key to Korean category name."""
    category_map = {
        "all": "종합",
        "politics": "정치",
        "economy": "경제",
        "society": "사회",
        "international": "국제",
        "world": "국제",
        "culture": "문화",
        "culture_life": "문화",
        "culture_ent": "문화",
        "entertainment": "연예",
        "sports": "스포츠",
        "opinion": "오피니언",
        "editorials": "오피니언",
        "science": "IT/과학",
        "science_env": "IT/과학",
        "it": "IT/과학",
        "finance": "경제",
        "stock": "경제",
        "realestate": "경제",
        "business": "경제",
        "life": "생활",
        "health": "생활",
        "travel": "생활",
        "english": "영문",
        "english_edition": "영문",
    }
    return category_map.get(key.lower())


def get_available_sources() -> List[dict]:
    """
    Get a summary of available sources from the catalog.
    Useful for CLI/debugging.
    """
    configs = load_catalog_sources()
    return [
        {
            "name": c.name,
            "rss_url": c.rss_url,
            "category": c.category,
            "enabled": c.enabled,
        }
        for c in configs
    ]
