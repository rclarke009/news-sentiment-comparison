"""
Main collection orchestration module.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from collections import Counter

from news_sentiment.models import (
    Headline,
    DailyComparison,
    SideStatistics,
    MostUpliftingStory,
)
from news_sentiment.news_fetcher import NewsFetcher
from news_sentiment.sentiment_scorer import SentimentScorer
from news_sentiment.database import NewsDatabase
from news_sentiment.local_sentiment import LocalSentimentScorer

logger = logging.getLogger(__name__)

# #region agent log
_DEBUG_LOG_PATH = Path(__file__).resolve().parents[2] / ".cursor" / "debug.log"


def _agent_log(payload: dict) -> None:
    try:
        with open(_DEBUG_LOG_PATH, "a") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass


# #endregion


class NewsCollector:
    """Orchestrates the news collection and scoring pipeline."""

    def __init__(self):
        """Initialize the collector with all required components."""
        self.fetcher = NewsFetcher()
        self.database = NewsDatabase()
        # Initialize local sentiment scorer
        try:
            self.local_scorer = LocalSentimentScorer()
            logger.info("Local sentiment scorer initialized")
        except Exception as e:
            logger.warning(
                f"Failed to initialize local sentiment scorer: {e}. Continuing without local model."
            )
            self.local_scorer = None
        # Pass database and local scorer to sentiment scorer
        self.scorer = SentimentScorer(
            database=self.database, local_scorer=self.local_scorer
        )

    def collect_daily_news(self, target_date: Optional[date] = None) -> DailyComparison:
        """
        Collect and process daily news headlines.

        Args:
            target_date: Date to collect for (defaults to today)

        Returns:
            DailyComparison object with aggregated results
        """
        # #region agent log
        import time

        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H2",
                "location": "collector.py:collect_daily_news",
                "message": "collect_daily_news_entry",
                "data": {
                    "target_date": target_date.isoformat() if target_date else None
                },
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion
        if target_date is None:
            # Use UTC date consistently (Render servers use UTC)
            target_date = datetime.utcnow().date()

        date_str = target_date.isoformat()
        logger.info(f"Starting daily collection for {date_str}")

        try:
            # Step 1: Fetch headlines
            logger.info("Fetching headlines from news sources...")
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2_H5",
                    "location": "collector.py:collect_daily_news",
                    "message": "before_fetch_headlines",
                    "data": {"date": date_str},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            conservative_headlines, liberal_headlines = (
                self.fetcher.fetch_all_headlines()
            )
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2_H5",
                    "location": "collector.py:collect_daily_news",
                    "message": "after_fetch_headlines",
                    "data": {
                        "conservative_count": len(conservative_headlines),
                        "liberal_count": len(liberal_headlines),
                        "date": date_str,
                    },
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion

            if not conservative_headlines and not liberal_headlines:
                # #region agent log
                _agent_log(
                    {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "H5",
                        "location": "collector.py:collect_daily_news",
                        "message": "no_headlines_fetched",
                        "data": {"date": date_str},
                        "timestamp": int(time.time() * 1000),
                    }
                )
                # #endregion
                logger.warning("No headlines fetched from any source")
                raise ValueError("No headlines available")

            # Step 2: Score headlines
            logger.info("Scoring headlines for sentiment...")
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H5",
                    "location": "collector.py:collect_daily_news",
                    "message": "before_scoring",
                    "data": {"date": date_str},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            conservative_scored = self.scorer.score_headlines(conservative_headlines)
            liberal_scored = self.scorer.score_headlines(liberal_headlines)
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H5",
                    "location": "collector.py:collect_daily_news",
                    "message": "after_scoring",
                    "data": {
                        "conservative_scored": len(conservative_scored),
                        "liberal_scored": len(liberal_scored),
                        "date": date_str,
                    },
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion

            # Step 3: Calculate statistics
            logger.info("Calculating statistics...")
            conservative_stats = self._calculate_statistics(
                conservative_scored, "conservative"
            )
            liberal_stats = self._calculate_statistics(liberal_scored, "liberal")

            # Step 4: Save to database
            logger.info("Saving to database...")
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2_H3",
                    "location": "collector.py:collect_daily_news",
                    "message": "before_save_headlines",
                    "data": {"date": date_str},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            self.database.save_headlines(conservative_scored, date_str)
            self.database.save_headlines(liberal_scored, date_str)
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2_H3",
                    "location": "collector.py:collect_daily_news",
                    "message": "after_save_headlines",
                    "data": {"date": date_str},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion

            # Step 5: Create daily comparison
            comparison = DailyComparison(
                date=date_str,
                conservative=conservative_stats.model_dump(),
                liberal=liberal_stats.model_dump(),
            )

            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2_H3",
                    "location": "collector.py:collect_daily_news",
                    "message": "before_save_daily_comparison",
                    "data": {"date": date_str},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            self.database.save_daily_comparison(comparison)
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2_H3",
                    "location": "collector.py:collect_daily_news",
                    "message": "after_save_daily_comparison",
                    "data": {"date": date_str},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion

            logger.info(
                f"Collection complete: "
                f"Conservative avg={conservative_stats.avg_uplift:.2f}, "
                f"Liberal avg={liberal_stats.avg_uplift:.2f}"
            )

            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2",
                    "location": "collector.py:collect_daily_news",
                    "message": "collect_daily_news_success",
                    "data": {
                        "date": date_str,
                        "conservative_avg": conservative_stats.avg_uplift,
                        "liberal_avg": liberal_stats.avg_uplift,
                    },
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            return comparison

        except Exception as e:
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2",
                    "location": "collector.py:collect_daily_news",
                    "message": "collect_daily_news_exception",
                    "data": {"error": str(e), "date": date_str},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            logger.error(
                f"Error during daily collection for {date_str}: {e}", exc_info=True
            )
            raise

    def _calculate_statistics(
        self, headlines: list[Headline], side: str
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
                avg_uplift=0.0, positive_percentage=0.0, total_headlines=0
            )

        # Calculate average uplift (LLM scores)
        scores = [h.final_score for h in headlines if h.final_score is not None]
        avg_uplift = sum(scores) / len(scores) if scores else 0.0

        # Calculate positive percentage (LLM scores)
        positive_count = sum(1 for s in scores if s > 0)
        positive_percentage = (positive_count / len(scores) * 100) if scores else 0.0

        # Calculate local model statistics
        local_scores = [
            h.local_sentiment_score
            for h in headlines
            if h.local_sentiment_score is not None
        ]
        avg_local_sentiment = None
        local_positive_percentage = None

        if local_scores:
            avg_local_sentiment = sum(local_scores) / len(local_scores)
            local_positive_count = sum(1 for s in local_scores if s > 0)
            local_positive_percentage = (
                (local_positive_count / len(local_scores) * 100)
                if local_scores
                else 0.0
            )

        # Find most uplifting story
        most_uplifting = None
        if headlines:
            # Sort by final_score descending
            sorted_headlines = sorted(
                headlines,
                key=lambda h: h.final_score if h.final_score is not None else -10,
                reverse=True,
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
                    published_at=top.published_at,
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
            score_distribution=dict(distribution),
            avg_local_sentiment=avg_local_sentiment,
            local_positive_percentage=local_positive_percentage,
        )

    def close(self) -> None:
        """Close database connections."""
        self.database.close()
