"""
Rate limiter for domain-based request throttling.
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from threading import Lock
from typing import Dict
from urllib.parse import urlparse


class RateLimiter:
    """Simple per-domain rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_second: float = 1.0, burst: int = 3) -> None:
        self.interval = 1.0 / requests_per_second
        self.burst = burst
        self._tokens: Dict[str, float] = defaultdict(lambda: float(burst))
        self._last_update: Dict[str, float] = defaultdict(time.monotonic)
        self._lock = Lock()

    def _get_domain(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc or url

    def _refill(self, domain: str) -> None:
        now = time.monotonic()
        elapsed = now - self._last_update[domain]
        self._tokens[domain] = min(
            self.burst,
            self._tokens[domain] + elapsed / self.interval
        )
        self._last_update[domain] = now

    def acquire(self, url: str) -> None:
        """Block until a request can be made for the given URL's domain."""
        domain = self._get_domain(url)
        with self._lock:
            self._refill(domain)
            while self._tokens[domain] < 1.0:
                wait_time = (1.0 - self._tokens[domain]) * self.interval
                time.sleep(wait_time)
                self._refill(domain)
            self._tokens[domain] -= 1.0

    async def acquire_async(self, url: str) -> None:
        """Async version of acquire."""
        domain = self._get_domain(url)
        self._refill(domain)
        while self._tokens[domain] < 1.0:
            wait_time = (1.0 - self._tokens[domain]) * self.interval
            await asyncio.sleep(wait_time)
            self._refill(domain)
        self._tokens[domain] -= 1.0


# Global rate limiter instance (1 request per second per domain, burst of 3)
default_rate_limiter = RateLimiter(requests_per_second=1.0, burst=3)
