"""
In-memory TTL cache for daily comparison reads.

Caches get_daily_comparison(date) results by date string (YYYY-MM-DD).
Today (UTC) uses a short TTL; past dates use a longer TTL.
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional

from news_sentiment.config import get_config
from news_sentiment.models import DailyComparison

logger = logging.getLogger(__name__)

# Singleton cache instance (set when API starts; used by routes and optionally by database for invalidation)
_cache_instance: Optional["DailyComparisonCache"] = None
_lock = threading.Lock()


def get_cache() -> Optional["DailyComparisonCache"]:
    """Return the global cache instance, or None if not initialized."""
    return _cache_instance


def set_cache(cache: "DailyComparisonCache") -> None:
    """Set the global cache instance (e.g. from API startup)."""
    global _cache_instance
    with _lock:
        _cache_instance = cache


class DailyComparisonCache:
    """
    In-memory TTL cache for DailyComparison by date (YYYY-MM-DD).

    Today (UTC) uses ttl_today_seconds; past dates use ttl_past_seconds.
    Thread-safe for get/set/invalidate.
    """

    def __init__(
        self,
        ttl_today_seconds: int = 300,
        ttl_past_seconds: int = 86400,
    ) -> None:
        self._ttl_today = ttl_today_seconds
        self._ttl_past = ttl_past_seconds
        self._store: dict[str, tuple[DailyComparison, float]] = {}
        self._lock = threading.Lock()

    def _today_utc(self) -> str:
        return datetime.now(timezone.utc).date().isoformat()

    def _ttl_for_date(self, date: str) -> int:
        if date == self._today_utc():
            return self._ttl_today
        return self._ttl_past

    def get(self, date: str) -> Optional[DailyComparison]:
        """
        Return cached DailyComparison for date if present and not expired.
        Otherwise return None.
        """
        with self._lock:
            entry = self._store.get(date)
            if entry is None:
                return None
            comparison, expiry_ts = entry
            if time.time() >= expiry_ts:
                del self._store[date]
                return None
            return comparison

    def set(self, date: str, comparison: DailyComparison) -> None:
        """Store comparison for date with TTL based on whether date is today (UTC) or past."""
        ttl = self._ttl_for_date(date)
        expiry_ts = time.time() + ttl
        with self._lock:
            self._store[date] = (comparison, expiry_ts)

    def invalidate(self, date: str) -> None:
        """Remove cached entry for date so next read refetches from DB."""
        with self._lock:
            self._store.pop(date, None)


def create_cache_from_config() -> Optional[DailyComparisonCache]:
    """
    Create and return a DailyComparisonCache from config, or None if cache disabled.
    Does not set the global cache; caller should call set_cache(cache) if needed.
    """
    config = get_config()
    if not config.cache.cache_enabled:
        return None
    return DailyComparisonCache(
        ttl_today_seconds=config.cache.cache_ttl_today_seconds,
        ttl_past_seconds=config.cache.cache_ttl_past_seconds,
    )
