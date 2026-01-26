"""
RSS feed fetching module for news sources not available via NewsAPI.
"""

import logging
import time
from datetime import datetime
from typing import List, Optional
import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from news_sentiment.config import get_config
from news_sentiment.models import Headline

logger = logging.getLogger(__name__)


class RSSFetcher:
    """Fetches news headlines from RSS feeds."""
    
    def __init__(self):
        """Initialize the RSS fetcher with configuration."""
        self.config = get_config()
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Retry strategy - DO NOT retry on 429 errors (rate limits)
        # 429 errors should be handled explicitly to avoid wasting quota
        # Only retry on transient server errors (500, 502, 503, 504)
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],  # Removed 429 - handle explicitly
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def fetch_from_rss(
        self,
        feed_url: str,
        source_name: str,
        source_id: str,
        political_side: str,
        max_items: int = 20
    ) -> List[Headline]:
        """
        Fetch headlines from an RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            source_name: Display name of the source
            source_id: Unique identifier for the source
            political_side: 'conservative' or 'liberal'
            max_items: Maximum number of items to fetch
            
        Returns:
            List of Headline objects
        """
        headlines = []
        
        try:
            logger.info(f"Fetching RSS feed from {source_name}: {feed_url}")
            
            # Fetch the RSS feed
            response = self.session.get(feed_url, timeout=30)
            response.raise_for_status()
            
            # Parse the RSS feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(f"RSS feed parsing warning for {source_name}: {feed.bozo_exception}")
            
            entries = feed.entries[:max_items]
            logger.info(f"Found {len(entries)} entries in RSS feed for {source_name}")
            
            for entry in entries:
                try:
                    headline = self._parse_rss_entry(entry, source_name, source_id, political_side)
                    if headline:
                        headlines.append(headline)
                except Exception as e:
                    logger.warning(f"Failed to parse RSS entry from {source_name}: {e}")
                    continue
            
            # Small delay to be respectful
            time.sleep(0.3)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching RSS feed from {source_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing RSS feed from {source_name}: {e}")
            return []
        
        logger.info(f"Successfully fetched {len(headlines)} headlines from {source_name} RSS feed")
        return headlines
    
    def _parse_rss_entry(
        self,
        entry: feedparser.FeedParserDict,
        source_name: str,
        source_id: str,
        political_side: str
    ) -> Optional[Headline]:
        """
        Parse an RSS feed entry into a Headline model.
        
        Args:
            entry: RSS feed entry from feedparser
            source_name: Display name of the source
            source_id: Unique identifier for the source
            political_side: 'conservative' or 'liberal'
            
        Returns:
            Headline object or None if parsing fails
        """
        try:
            # Get title
            title = entry.get("title", "").strip()
            if not title:
                logger.warning(f"Skipping RSS entry with missing title from {source_name}")
                return None
            
            # Get URL
            url = entry.get("link", "")
            if not url:
                logger.warning(f"Skipping RSS entry with missing URL from {source_name}")
                return None
            
            # Get description/summary
            description = None
            if "summary" in entry:
                description = entry.summary.strip() or None
            elif "description" in entry:
                description = entry.description.strip() or None
            
            # Parse published date
            published_at = datetime.utcnow()  # Default fallback
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    # feedparser provides a time.struct_time
                    import time as time_module
                    published_at = datetime.utcfromtimestamp(
                        time_module.mktime(entry.published_parsed)
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse RSS date from {source_name}: {e}")
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                try:
                    import time as time_module
                    published_at = datetime.utcfromtimestamp(
                        time_module.mktime(entry.updated_parsed)
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse RSS updated date from {source_name}: {e}")
            
            return Headline(
                title=title,
                description=description,
                url=url,
                source=source_name,
                source_id=source_id,
                published_at=published_at,
                political_side=political_side
            )
        
        except Exception as e:
            logger.error(f"Error parsing RSS entry from {source_name}: {e}")
            return None
    
    def fetch_rss_sources(
        self,
        rss_sources: List[dict],
        political_side: str
    ) -> List[Headline]:
        """
        Fetch headlines from multiple RSS sources.
        
        Args:
            rss_sources: List of dicts with 'url', 'name', and 'id' keys
            political_side: 'conservative' or 'liberal'
            
        Returns:
            List of Headline objects from all RSS sources
        """
        all_headlines = []
        
        for rss_source in rss_sources:
            headlines = self.fetch_from_rss(
                feed_url=rss_source["url"],
                source_name=rss_source["name"],
                source_id=rss_source["id"],
                political_side=political_side
            )
            all_headlines.extend(headlines)
        
        return all_headlines
