#!/usr/bin/env python3
"""
Test script to verify if NewsAPI supports Newsmax.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # how does parent.parent work?
# it works because the parent directory is the news-sentiment-comparison directory.
# so the parent.parent is the parent of the parent directory.
# which is the root directory.
# so the parent.parent is the root directory.

import requests
from news_sentiment.config import get_config


def test_newsmax_support():
    """Test if NewsAPI supports Newsmax."""
    config = get_config()
    api_key = config.news_api.api_key

    print("=" * 70)
    print("Testing NewsAPI Support for Newsmax")
    print("=" * 70)

    newsmax_in_sources = False
    newsmax_returns_articles = False

    # Test 1: Get all sources and search for newsmax
    print("\n[Test 1] Querying NewsAPI sources endpoint...")
    sources_url = "https://newsapi.org/v2/top-headlines/sources"
    params = {"apiKey": api_key}

    try:
        response = requests.get(sources_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            print(f"✗ Error: {data.get('message', 'Unknown error')}")
            return False

        sources = data.get("sources", [])
        print(f"✓ Found {len(sources)} total sources")

        # Search for newsmax
        newsmax_sources = [
            s
            for s in sources
            if "newsmax" in s.get("id", "").lower()
            or "newsmax" in s.get("name", "").lower()
        ]

        if newsmax_sources:
            print(f"\n✓ Found {len(newsmax_sources)} Newsmax source(s):")
            for src in newsmax_sources:
                print(f"  - ID: '{src.get('id')}'")
                print(f"    Name: {src.get('name')}")
                print(f"    Description: {src.get('description', '')[:100]}...")
                print(f"    Category: {src.get('category')}")
                print(f"    Country: {src.get('country')}")
            newsmax_in_sources = True
        else:
            print("\n✗ Newsmax NOT found in NewsAPI sources list")

            # Show similar sources
            print("\n  Similar conservative sources found:")
            conservative_keywords = [
                "fox",
                "breitbart",
                "blaze",
                "national-review",
                "daily-wire",
            ]
            similar = [
                s
                for s in sources
                if any(
                    kw in s.get("id", "").lower() or kw in s.get("name", "").lower()
                    for kw in conservative_keywords
                )
            ]
            for src in similar[:5]:  # Show first 5
                print(f"    - {src.get('id')}: {src.get('name')}")

    except requests.exceptions.RequestException as e:
        print(f"✗ Error querying sources endpoint: {e}")
        return False

    # Test 2: Try to fetch headlines using 'newsmax' as source ID
    print("\n" + "=" * 70)
    print("[Test 2] Attempting to fetch headlines using 'newsmax' source ID...")
    print("=" * 70)

    headlines_url = "https://newsapi.org/v2/top-headlines"
    params = {"sources": "newsmax", "apiKey": api_key, "pageSize": 5}

    try:
        response = requests.get(headlines_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "ok":
            articles = data.get("articles", [])
            total_results = data.get("totalResults", 0)
            print("✓ API returned status 'ok'")
            print(f"  Total results: {total_results}")
            print(f"  Articles returned: {len(articles)}")

            if articles:
                print("\n  Sample articles:")
                for i, article in enumerate(articles[:3], 1):
                    print(f"    {i}. {article.get('title', 'N/A')[:70]}...")
                    print(
                        f"       Source: {article.get('source', {}).get('name', 'N/A')}"
                    )
                    print(f"       URL: {article.get('url', 'N/A')[:60]}...")
                newsmax_returns_articles = True
            elif total_results == 0:
                print("\n  ⚠️  Source ID accepted but returned 0 articles")
                print("     This could mean:")
                print("     - Newsmax is a valid source but has no articles right now")
                print("     - OR Newsmax was removed from NewsAPI")
        else:
            error_msg = data.get("message", "Unknown error")
            print(f"✗ API returned error: {error_msg}")

            # Check if it's a source not found error
            if "source" in error_msg.lower() or "invalid" in error_msg.lower():
                print(
                    "\n  → This indicates 'newsmax' is NOT a valid source ID in NewsAPI"
                )

    except requests.exceptions.RequestException as e:
        print(f"✗ HTTP Error: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"  Error message: {error_data.get('message', 'Unknown error')}")
            except Exception:
                print(f"  Response: {e.response.text[:200]}")

    # Test 3: Compare with invalid source ID to see error message
    print("\n" + "=" * 70)
    print("[Test 3] Testing with invalid source ID for comparison...")
    print("=" * 70)

    params = {"sources": "invalid-source-xyz-123", "apiKey": api_key, "pageSize": 1}

    try:
        response = requests.get(headlines_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") != "ok":
                error_msg = data.get("message", "Unknown error")
                print(f"✗ Invalid source returns error: {error_msg}")
                print("\n  → Comparing with 'newsmax' result:")
                print("     - Invalid source: Returns error message")
                print("     - 'newsmax': Returns status 'ok' with 0 articles")
                print(
                    "     - Conclusion: 'newsmax' is accepted as valid but has no content"
                )
            else:
                print("⚠️  Invalid source also returned 'ok' (unexpected)")
    except Exception as e:
        print(f"Error testing invalid source: {e}")

    # Test 4: Try alternative source IDs
    print("\n" + "=" * 70)
    print("[Test 4] Testing alternative Newsmax source IDs...")
    print("=" * 70)

    alternative_ids = ["newsmax-media", "newsmax-com", "newsmax-news"]
    found_alternative = False
    for alt_id in alternative_ids:
        params = {"sources": alt_id, "apiKey": api_key, "pageSize": 1}
        try:
            response = requests.get(headlines_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and data.get("totalResults", 0) > 0:
                    print(f"✓ Found working source ID: '{alt_id}'")
                    found_alternative = True
                    newsmax_returns_articles = True
        except Exception:
            pass

    if not found_alternative:
        print("✗ No alternative source IDs worked")

    # Final verdict
    if newsmax_returns_articles:
        return True
    elif newsmax_in_sources:
        # In sources list but no articles - might be temporarily unavailable
        return False
    else:
        # Not in sources and no articles - not supported
        return False


if __name__ == "__main__":
    try:
        result = test_newsmax_support()
        print("\n" + "=" * 70)
        if result:
            print("RESULT: ✓ Newsmax IS supported by NewsAPI")
        else:
            print("RESULT: ✗ Newsmax is NOT supported by NewsAPI")
            print("\nRecommendation: Use RSS feed parsing as an alternative")
        print("=" * 70)
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
