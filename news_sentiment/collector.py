"""
Main collection orchestration module.
"""

import logging
from datetime import datetime, date
from typing import Optional
from collections import Counter

from news_sentiment.models import (
    Headline,
    DailyComparison,
    SideStatistics,
    MostUpliftingStory
)
from news_sentiment.news_fetcher import NewsFetcher
from news_sentiment.sentiment_scorer import SentimentScorer
from news_sentiment.database import NewsDatabase

logger = logging.getLogger(__name__)


class NewsCollector:
    """Orchestrates the news collection and scoring pipeline."""
    
    def __init__(self):
        """Initialize the collector with all required components."""
        self.fetcher = NewsFetcher()
        self.scorer = SentimentScorer()
        self.database = NewsDatabase()
    
    def collect_daily_news(self, target_date: Optional[date] = None) -> DailyComparison:
        """
        Collect and process daily news headlines.
        
        Args:
            target_date: Date to collect for (defaults to today)
            
        Returns:
            DailyComparison object with aggregated results
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        logger.info(f"Starting daily collection for {date_str}")
        
        try:
            # Step 1: Fetch headlines
            logger.info("Fetching headlines from news sources...")
            conservative_headlines, liberal_headlines = self.fetcher.fetch_all_headlines()
            
            if not conservative_headlines and not liberal_headlines:
                logger.warning("No headlines fetched from any source")
                raise ValueError("No headlines available")
            
            # Step 2: Score headlines
            logger.info("Scoring headlines for sentiment...")
            conservative_scored = self.scorer.score_headlines(conservative_headlines)
            liberal_scored = self.scorer.score_headlines(liberal_headlines)
            
            # Step 3: Calculate statistics
            logger.info("Calculating statistics...")
            conservative_stats = self._calculate_statistics(conservative_scored, "conservative")
            liberal_stats = self._calculate_statistics(liberal_scored, "liberal")
            
            # Step 4: Save to database
            logger.info("Saving to database...")
            self.database.save_headlines(conservative_scored, date_str)
            self.database.save_headlines(liberal_scored, date_str)
            
            # Step 5: Create daily comparison
            comparison = DailyComparison(
                date=date_str,
                conservative=conservative_stats.model_dump(),
                liberal=liberal_stats.model_dump()
            )
            
            self.database.save_daily_comparison(comparison)
            
            logger.info(
                f"Collection complete: "
                f"Conservative avg={conservative_stats.avg_uplift:.2f}, "
                f"Liberal avg={liberal_stats.avg_uplift:.2f}"
            )
            
            return comparison
        
        except Exception as e:
            logger.error(f"Error during daily collection: {e}")
            raise
    
    def _calculate_statistics(
        self,
        headlines: list[Headline],
        side: str
    ) -> SideStatistics:
        """
        Calculate statistics for a set of headlines.
        
        Args:
            headlines: List of scored headlines
            side: 'conservative' or 'liberal'
            
        Returns:
            SideStatistics object
        """
        if not headlines:
            return SideStatistics(
                avg_uplift=0.0,
                positive_percentage=0.0,
                total_headlines=0
            )
        
        # Calculate average uplift
        scores = [h.final_score for h in headlines if h.final_score is not None]
        avg_uplift = sum(scores) / len(scores) if scores else 0.0
        
        # Calculate positive percentage
        positive_count = sum(1 for s in scores if s > 0)
        positive_percentage = (positive_count / len(scores) * 100) if scores else 0.0
        
        # Find most uplifting story
        most_uplifting = None
        if headlines:
            # Sort by final_score descending
            sorted_headlines = sorted(
                headlines,
                key=lambda h: h.final_score if h.final_score is not None else -10,
                reverse=True
            )
            top = sorted_headlines[0]
            if top.final_score is not None and top.final_score > 0:
                most_uplifting = MostUpliftingStory(
                    title=top.title,
                    description=top.description,
                    url=top.url,
                    source=top.source,
                    uplift_score=top.uplift_score or 0.0,
                    final_score=top.final_score,
                    published_at=top.published_at
                )
        
        # Calculate score distribution
        distribution = Counter()
        for score in scores:
            if score >= 4:
                distribution["4-5"] += 1
            elif score >= 2:
                distribution["2-4"] += 1
            elif score >= 0:
                distribution["0-2"] += 1
            elif score >= -2:
                distribution["-2-0"] += 1
            else:
                distribution["-5--2"] += 1
        
        return SideStatistics(
            avg_uplift=avg_uplift,
            positive_percentage=positive_percentage,
            total_headlines=len(headlines),
            most_uplifting=most_uplifting,
            score_distribution=dict(distribution)
        )
    
    def close(self) -> None:
        """Close database connections."""
        self.database.close()
