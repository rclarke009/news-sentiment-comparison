"""
Unit tests for the daily comparison cache (hit, miss, TTL expiry, invalidation).
"""

import time
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from news_sentiment.cache import DailyComparisonCache, create_cache_from_config, get_cache, set_cache
from news_sentiment.models import DailyComparison


def _make_comparison(date: str) -> DailyComparison:
    """Build a minimal DailyComparison for the given date."""
    return DailyComparison(
        date=date,
        conservative={
            "avg_uplift": 0.5,
            "positive_percentage": 60.0,
            "total_headlines": 10,
            "most_uplifting": None,
            "score_distribution": {},
        },
        liberal={
            "avg_uplift": 0.4,
            "positive_percentage": 55.0,
            "total_headlines": 10,
            "most_uplifting": None,
            "score_distribution": {},
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_cache_miss_returns_none():
    """Cache get with no prior set returns None."""
    cache = DailyComparisonCache(ttl_today_seconds=60, ttl_past_seconds=3600)
    assert cache.get("2025-01-15") is None


def test_cache_hit_returns_stored_value():
    """After set, get returns the same DailyComparison."""
    cache = DailyComparisonCache(ttl_today_seconds=60, ttl_past_seconds=3600)
    comp = _make_comparison("2025-01-15")
    cache.set("2025-01-15", comp)
    result = cache.get("2025-01-15")
    assert result is not None
    assert result.date == "2025-01-15"
    assert result.conservative["avg_uplift"] == 0.5


def test_cache_invalidate_removes_entry():
    """After invalidate, get returns None for that date."""
    cache = DailyComparisonCache(ttl_today_seconds=60, ttl_past_seconds=3600)
    comp = _make_comparison("2025-01-15")
    cache.set("2025-01-15", comp)
    cache.invalidate("2025-01-15")
    assert cache.get("2025-01-15") is None


def test_cache_ttl_expiry_past_date():
    """Past-date entry expires after ttl_past_seconds."""
    cache = DailyComparisonCache(ttl_today_seconds=60, ttl_past_seconds=1)
    comp = _make_comparison("2025-01-15")
    cache.set("2025-01-15", comp)
    assert cache.get("2025-01-15") is not None
    time.sleep(1.1)
    assert cache.get("2025-01-15") is None


def test_cache_ttl_expiry_today():
    """Today entry uses ttl_today_seconds (short TTL)."""
    today = datetime.now(timezone.utc).date().isoformat()
    cache = DailyComparisonCache(ttl_today_seconds=1, ttl_past_seconds=3600)
    comp = _make_comparison(today)
    cache.set(today, comp)
    assert cache.get(today) is not None
    time.sleep(1.1)
    assert cache.get(today) is None


def test_create_cache_from_config_disabled_returns_none():
    """When cache is disabled in config, create_cache_from_config returns None."""
    with patch("news_sentiment.cache.get_config") as mock_get_config:
        mock_config = type("Config", (), {})()
        mock_config.cache = type("CacheConfig", (), {})()
        mock_config.cache.cache_enabled = False
        mock_config.cache.cache_ttl_today_seconds = 300
        mock_config.cache.cache_ttl_past_seconds = 86400
        mock_get_config.return_value = mock_config
        result = create_cache_from_config()
        assert result is None


def test_create_cache_from_config_enabled_returns_cache():
    """When cache is enabled, create_cache_from_config returns a DailyComparisonCache."""
    with patch("news_sentiment.cache.get_config") as mock_get_config:
        mock_config = type("Config", (), {})()
        mock_config.cache = type("CacheConfig", (), {})()
        mock_config.cache.cache_enabled = True
        mock_config.cache.cache_ttl_today_seconds = 300
        mock_config.cache.cache_ttl_past_seconds = 86400
        mock_get_config.return_value = mock_config
        result = create_cache_from_config()
        assert result is not None
        assert isinstance(result, DailyComparisonCache)


def test_set_cache_and_get_cache_roundtrip():
    """set_cache and get_cache allow registering and retrieving the global cache."""
    set_cache(None)
    assert get_cache() is None
    cache = DailyComparisonCache(ttl_today_seconds=60, ttl_past_seconds=3600)
    set_cache(cache)
    assert get_cache() is cache
    set_cache(None)
    assert get_cache() is None
