from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SourceConfig:
    name: str
    adapter: str
    base_url: str
    terms_url: str
    allow_fulltext: bool
    allow_derivatives: bool
    rss_url: Optional[str] = None
    category: Optional[str] = None
    language: str = "ko"
    enabled: bool = True
    max_items: int = 50
    license_required_patterns: List[str] = field(default_factory=list)


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    # Resolve relative to the backend service root (services/backend)
    base_dir = Path(__file__).resolve().parents[2]
    return base_dir / path


def load_source_configs(path_str: str | None) -> List[SourceConfig]:
    source_path = _resolve_path(path_str or "config/sources.yaml")
    if not source_path.exists():
        logger.warning("sources file not found", extra={"extra": {"path": str(source_path)}})
        return []
    data = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    items = data.get("sources", [])
    configs: List[SourceConfig] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        config = SourceConfig(
            name=raw.get("name", "").strip(),
            adapter=raw.get("adapter", "rss"),
            base_url=raw.get("base_url", "").strip(),
            terms_url=raw.get("terms_url", "").strip(),
            allow_fulltext=bool(raw.get("allow_fulltext", False)),
            allow_derivatives=bool(raw.get("allow_derivatives", False)),
            rss_url=(raw.get("rss_url") or "").strip() or None,
            category=(raw.get("category") or "").strip() or None,
            language=(raw.get("language") or "ko").strip() or "ko",
            enabled=bool(raw.get("enabled", True)),
            max_items=int(raw.get("max_items", 50) or 50),
            license_required_patterns=list(raw.get("license_required_patterns", []) or []),
        )
        if not config.name or not config.adapter:
            continue
        configs.append(config)
    return configs
