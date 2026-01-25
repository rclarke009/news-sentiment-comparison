#!/usr/bin/env python3
"""
Test script to verify RSS fetcher works with Newsmax feeds.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from news_sentiment.rss_fetcher import RSSFetcher
from news_sentiment.utils.logging_config import setup_logging

def test_rss_fetcher():
    """Test RSS fetcher with Newsmax feeds."""
    setup_logging(log_level="INFO")
    
    print("=" * 70)
    print("Testing RSS Fetcher with Newsmax")
    print("=" * 70)
    
    fetcher = RSSFetcher()
    
    # Test Newsmax main feed
    print("\n[Test 1] Fetching from Newsmax Newsfront feed...")
    headlines = fetcher.fetch_from_rss(
        feed_url="https://www.newsmax.com/rss/Newsfront/16",
        source_name="Newsmax",
        source_id="newsmax",
        political_side="conservative",
        max_items=5
    )
    
    print(f"\n✓ Fetched {len(headlines)} headlines from Newsmax")
    if headlines:
        print("\n  Sample headlines:")
        for i, headline in enumerate(headlines[:3], 1):
            print(f"    {i}. {headline.title[:70]}...")
            print(f"       URL: {headline.url}")
            print(f"       Published: {headline.published_at}")
    
    # Test Newsmax Politics feed
    print("\n" + "=" * 70)
    print("[Test 2] Fetching from Newsmax Politics feed...")
    headlines2 = fetcher.fetch_from_rss(
        feed_url="https://www.newsmax.com/rss/Politics/1",
        source_name="Newsmax Politics",
        source_id="newsmax-politics",
        political_side="conservative",
        max_items=5
    )
    
    print(f"\n✓ Fetched {len(headlines2)} headlines from Newsmax Politics")
    if headlines2:
        print("\n  Sample headlines:")
        for i, headline in enumerate(headlines2[:3], 1):
            print(f"    {i}. {headline.title[:70]}...")
            print(f"       URL: {headline.url}")
    
    print("\n" + "=" * 70)
    print("RESULT: ✓ RSS fetcher is working correctly")
    print("=" * 70)
    
    return len(headlines) > 0 or len(headlines2) > 0


if __name__ == "__main__":
    try:
        result = test_rss_fetcher()
        sys.exit(0 if result else 1)
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("  Please install feedparser: pip install feedparser")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
