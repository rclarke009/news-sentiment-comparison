"""
News fetching module using NewsAPI.org and RSS feeds.
"""

import logging
import time
from datetime import datetime
from typing import List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from news_sentiment.config import get_config
from news_sentiment.models import Headline
from news_sentiment.rss_fetcher import RSSFetcher

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetches news headlines from NewsAPI.org and RSS feeds."""
    
    def __init__(self):
        """Initialize the news fetcher with configuration."""
        self.config = get_config()
        self.session = self._create_session()
        self.rss_fetcher = RSSFetcher()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=self.config.news_api.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def fetch_headlines(
        self,
        sources: List[str],
        political_side: str,
        page_size: int = 20
    ) -> List[Headline]:
        """
        Fetch top headlines from specified sources.
        
        Args:
            sources: List of NewsAPI source IDs
            political_side: 'conservative' or 'liberal'
            page_size: Number of headlines to fetch per source
            
        Returns:
            List of Headline objects
        """
        all_headlines = []
        
        # NewsAPI allows multiple sources in one request (comma-separated)
        sources_str = ",".join(sources)
        
        try:
            url = f"{self.config.news_api.base_url}/top-headlines"
            params = {
                "sources": sources_str,
                "pageSize": page_size,
                "apiKey": self.config.news_api.api_key
            }
            
            logger.info(f"Fetching headlines from {len(sources)} {political_side} sources")
            
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.news_api.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "ok":
                logger.error(f"NewsAPI returned error: {data.get('message', 'Unknown error')}")
                return []
            
            articles = data.get("articles", [])
            logger.info(f"Received {len(articles)} articles from NewsAPI")
            
            for article in articles:
                try:
                    headline = self._parse_article(article, political_side)
                    if headline:
                        all_headlines.append(headline)
                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")
                    continue
            
            # Rate limiting: NewsAPI free tier allows 100 requests/day
            # Be respectful and add a small delay
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching headlines: {e}")
            raise
        
        logger.info(f"Successfully fetched {len(all_headlines)} headlines for {political_side} side")
        return all_headlines
    
    def _parse_article(self, article: dict, political_side: str) -> Optional[Headline]:
        """
        Parse a NewsAPI article into a Headline model.
        
        Args:
            article: Article dictionary from NewsAPI
            political_side: 'conservative' or 'liberal'
            
        Returns:
            Headline object or None if parsing fails
        """
        try:
            # Parse published date
            published_str = article.get("publishedAt", "")
            if published_str:
                # NewsAPI format: "2024-01-15T10:30:00Z" or "2026-01-24T00:52:20.0261369+00:00"
                # Handle 7-digit microseconds (Python only supports 6)
                published_str = published_str.replace("Z", "+00:00")
                # Truncate microseconds to 6 digits if present
                if "." in published_str:
                    # Find the dot and timezone separator
                    dot_idx = published_str.rfind(".")
                    # Look for timezone separator after the dot
                    tz_sep_plus = published_str.find("+", dot_idx)
                    tz_sep_minus = published_str.find("-", dot_idx + 7)  # Skip date part
                    tz_sep = -1
                    if tz_sep_plus > dot_idx:
                        tz_sep = tz_sep_plus
                    elif tz_sep_minus > dot_idx:
                        tz_sep = tz_sep_minus
                    if tz_sep > dot_idx:
                        # Extract microseconds part
                        microsec = published_str[dot_idx+1:tz_sep]
                        if len(microsec) > 6:
                            # Truncate to 6 digits
                            published_str = published_str[:dot_idx+1] + microsec[:6] + published_str[tz_sep:]
                try:
                    published_at = datetime.fromisoformat(published_str)
                except ValueError:
                    # Fallback to current time if parsing fails
                    logger.warning(f"Failed to parse date: {published_str}, using current time")
                    published_at = datetime.utcnow()
            else:
                published_at = datetime.utcnow()
            
            # Get source information
            source_info = article.get("source", {})
            source_name = source_info.get("name", "Unknown")
            source_id = source_info.get("id", source_name.lower().replace(" ", "-"))
            
            # Validate required fields
            title = article.get("title", "").strip()
            url = article.get("url", "")
            
            if not title or not url:
                logger.warning(f"Skipping article with missing title or URL")
                return None
            
            return Headline(
                title=title,
                description=article.get("description", "").strip() or None,
                url=url,
                source=source_name,
                source_id=source_id,
                published_at=published_at,
                political_side=political_side
            )
        
        except Exception as e:
            logger.error(f"Error parsing article: {e}")
            return None
    
    def fetch_all_headlines(self) -> tuple[List[Headline], List[Headline]]:
        """
        Fetch headlines from both conservative and liberal sources.
        Combines NewsAPI and RSS feed sources.
        
        Returns:
            Tuple of (conservative_headlines, liberal_headlines)
        """
        config = get_config()
        cap = config.sources.headlines_per_side

        # Fetch from NewsAPI
        conservative_headlines = self.fetch_headlines(
            sources=config.sources.conservative,
            political_side="conservative",
            page_size=cap
        )

        liberal_headlines = self.fetch_headlines(
            sources=config.sources.liberal,
            political_side="liberal",
            page_size=cap
        )

        # Fetch from RSS feeds
        if config.sources.conservative_rss:
            rss_sources = [
                {"url": rss.url, "name": rss.name, "id": rss.id}
                for rss in config.sources.conservative_rss
            ]
            rss_headlines = self.rss_fetcher.fetch_rss_sources(
                rss_sources=rss_sources,
                political_side="conservative"
            )
            conservative_headlines.extend(rss_headlines)
            logger.info(f"Added {len(rss_headlines)} headlines from RSS feeds to conservative sources")

        if config.sources.liberal_rss:
            rss_sources = [
                {"url": rss.url, "name": rss.name, "id": rss.id}
                for rss in config.sources.liberal_rss
            ]
            rss_headlines = self.rss_fetcher.fetch_rss_sources(
                rss_sources=rss_sources,
                political_side="liberal"
            )
            liberal_headlines.extend(rss_headlines)
            logger.info(f"Added {len(rss_headlines)} headlines from RSS feeds to liberal sources")

        # Cap each side at headlines_per_side for even comparison
        if len(conservative_headlines) > cap:
            logger.info(f"Capping conservative headlines from {len(conservative_headlines)} to {cap}")
            conservative_headlines = conservative_headlines[:cap]
        if len(liberal_headlines) > cap:
            logger.info(f"Capping liberal headlines from {len(liberal_headlines)} to {cap}")
            liberal_headlines = liberal_headlines[:cap]

        return conservative_headlines, liberal_headlines
