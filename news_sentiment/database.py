"""
MongoDB database operations for news sentiment data.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

from news_sentiment.config import get_config
from news_sentiment.models import (
    Headline,
    DailyComparison,
)

try:
    from pydantic_core import Url as PydanticUrl
except ImportError:
    PydanticUrl = None

logger = logging.getLogger(__name__)

# #region agent log
_DEBUG_LOG_PATH = Path(__file__).resolve().parents[3] / ".cursor" / "debug.log"


def _agent_log(payload: dict) -> None:
    try:
        with open(_DEBUG_LOG_PATH, "a") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass


# #endregion


def _convert_httpurl_to_str(obj):
    """Recursively convert HttpUrl objects to strings for MongoDB."""
    # HttpUrl is a type alias and can't be used with isinstance() in Python 3.11+
    # At runtime, HttpUrl values are typically strings or pydantic_core.Url objects
    # Check for the actual runtime type instead
    if isinstance(obj, str):
        # Already a string, return as-is
        return obj
    elif obj is None:
        return obj
    elif isinstance(obj, (int, float, bool)):
        # Basic types that shouldn't be converted
        return obj
    elif PydanticUrl is not None and isinstance(obj, PydanticUrl):
        # Check for actual pydantic_core.Url type
        return str(obj)
    elif hasattr(obj, "__str__"):
        # Check if it's a URL-like object by checking if string representation looks like a URL
        try:
            str_repr = str(obj)
            # If it looks like a URL, convert it to string
            if str_repr.startswith(("http://", "https://")):
                return str_repr
        except Exception:
            pass
    if isinstance(obj, dict):
        return {k: _convert_httpurl_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_httpurl_to_str(item) for item in obj]
    return obj


class NewsDatabase:
    """MongoDB database manager for news sentiment data."""

    def __init__(self):
        """Initialize database connection."""
        self.config = get_config()
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self._connect()
        self._create_indexes()

    def _connect(self) -> None:
        """Connect to MongoDB."""
        # #region agent log
        import time

        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H1_H8",
                "location": "database.py:_connect",
                "message": "connecting_to_mongodb",
                "data": {
                    "uri_masked": (
                        self.config.mongodb.uri[:20] + "..."
                        if len(self.config.mongodb.uri) > 20
                        else self.config.mongodb.uri
                    ),
                    "database_name": self.config.mongodb.database_name,
                    "timeout": self.config.mongodb.connection_timeout,
                },
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion
        try:
            self.client = MongoClient(
                self.config.mongodb.uri,
                serverSelectionTimeoutMS=self.config.mongodb.connection_timeout * 1000,
            )
            # Test connection
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H1_H8",
                    "location": "database.py:_connect",
                    "message": "pinging_mongodb",
                    "data": {},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            self.client.admin.command("ping")
            self.db = self.client[self.config.mongodb.database_name]
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H1_H8",
                    "location": "database.py:_connect",
                    "message": "mongodb_connected",
                    "data": {"database_name": self.config.mongodb.database_name},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            logger.info(f"Connected to MongoDB: {self.config.mongodb.database_name}")
        except ConnectionFailure as e:
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H1_H8",
                    "location": "database.py:_connect",
                    "message": "mongodb_connection_failed",
                    "data": {
                        "error": str(e),
                        "database_name": self.config.mongodb.database_name,
                    },
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            logger.error(
                f"Failed to connect to MongoDB (database: {self.config.mongodb.database_name}): {e}",
                exc_info=True,
            )
            raise

    def _create_indexes(self) -> None:
        """Create database indexes for efficient queries."""
        try:
            # Headlines collection indexes
            headlines = self.db.headlines
            headlines.create_index([("date", 1), ("political_side", 1)])
            headlines.create_index([("published_at", -1)])
            headlines.create_index([("final_score", -1)])
            headlines.create_index([("source_id", 1)])

            # Daily comparisons collection indexes
            daily_comparisons = self.db.daily_comparisons
            daily_comparisons.create_index([("date", 1)], unique=True)
            daily_comparisons.create_index([("created_at", -1)])

            # API rate limits collection indexes
            api_rate_limits = self.db.api_rate_limits
            api_rate_limits.create_index([("date", 1)], unique=True)

            logger.debug("Database indexes created")
        except Exception as e:
            logger.warning(f"Error creating database indexes: {e}", exc_info=True)

    def save_headlines(self, headlines: List[Headline], date: str) -> int:
        """
        Save headlines to database.

        Args:
            headlines: List of headlines to save
            date: Date string in YYYY-MM-DD format

        Returns:
            Number of headlines saved
        """
        # #region agent log
        import time

        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H2_H3_H4",
                "location": "database.py:save_headlines",
                "message": "save_headlines_entry",
                "data": {"headlines_count": len(headlines), "date": date},
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion
        if not headlines:
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2_H5",
                    "location": "database.py:save_headlines",
                    "message": "no_headlines_to_save",
                    "data": {"date": date},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            return 0

        try:
            collection = self.db.headlines

            # Prepare documents
            documents = []
            for headline in headlines:
                doc = headline.model_dump()
                doc["date"] = date  # Add date field for easy querying
                # Convert datetime objects to ISO strings for MongoDB
                if isinstance(doc.get("published_at"), datetime):
                    doc["published_at"] = doc["published_at"].isoformat()
                if isinstance(doc.get("collected_at"), datetime):
                    doc["collected_at"] = doc["collected_at"].isoformat()
                # Convert URL to string
                if "url" in doc:
                    doc["url"] = str(doc["url"])
                documents.append(doc)

            # Log sample scores before saving (verify they're not all 0)
            if documents:
                sample = documents[0]
                logger.info(
                    f"Saving headlines with scores - sample: final_score={sample.get('final_score')}, "
                    f"uplift_score={sample.get('uplift_score')}, title='{sample.get('title', '')[:50]}...'"
                )

            # Insert documents
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H3",
                    "location": "database.py:save_headlines",
                    "message": "before_insert_many",
                    "data": {"documents_count": len(documents), "date": date},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            result = collection.insert_many(documents)
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H3",
                    "location": "database.py:save_headlines",
                    "message": "after_insert_many",
                    "data": {"inserted_count": len(result.inserted_ids), "date": date},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            logger.info(f"Saved {len(result.inserted_ids)} headlines to database")
            return len(result.inserted_ids)

        except Exception as e:
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H3",
                    "location": "database.py:save_headlines",
                    "message": "save_headlines_exception",
                    "data": {
                        "error": str(e),
                        "headlines_count": len(headlines),
                        "date": date,
                    },
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            logger.error(
                f"Error saving {len(headlines)} headlines to database for date {date}: {e}",
                exc_info=True,
            )
            raise

    def save_daily_comparison(self, comparison: DailyComparison) -> bool:
        """
        Save or update daily comparison.

        Args:
            comparison: DailyComparison object

        Returns:
            True if successful
        """
        # #region agent log
        import time

        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H2_H3_H4",
                "location": "database.py:save_daily_comparison",
                "message": "save_daily_comparison_entry",
                "data": {"date": comparison.date},
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion
        try:
            collection = self.db.daily_comparisons

            doc = comparison.model_dump()
            # Convert datetime objects
            if isinstance(doc.get("created_at"), datetime):
                doc["created_at"] = doc["created_at"].isoformat()
            if isinstance(doc.get("updated_at"), datetime):
                doc["updated_at"] = doc["updated_at"].isoformat()

            # Convert HttpUrl objects to strings (MongoDB can't encode them directly)
            doc = _convert_httpurl_to_str(doc)

            # Upsert (insert or update)
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H3",
                    "location": "database.py:save_daily_comparison",
                    "message": "before_upsert",
                    "data": {"date": comparison.date},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            result = collection.update_one(
                {"date": comparison.date}, {"$set": doc}, upsert=True
            )
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H3",
                    "location": "database.py:save_daily_comparison",
                    "message": "after_upsert",
                    "data": {
                        "date": comparison.date,
                        "matched": result.matched_count,
                        "modified": result.modified_count,
                        "upserted_id": (
                            str(result.upserted_id) if result.upserted_id else None
                        ),
                    },
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            logger.info(f"Saved daily comparison for {comparison.date}")
            return True

        except Exception as e:
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H3",
                    "location": "database.py:save_daily_comparison",
                    "message": "save_daily_comparison_exception",
                    "data": {"error": str(e), "date": comparison.date},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            logger.error(
                f"Error saving daily comparison for date {comparison.date}: {e}",
                exc_info=True,
            )
            raise

    def get_daily_comparison(self, date: str) -> Optional[DailyComparison]:
        """
        Get daily comparison for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            DailyComparison or None if not found
        """
        # #region agent log
        import time

        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H4_H7_H8",
                "location": "database.py:get_daily_comparison",
                "message": "get_daily_comparison_entry",
                "data": {"date": date},
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion
        try:
            collection = self.db.daily_comparisons
            doc = collection.find_one({"date": date})
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H4_H7_H8",
                    "location": "database.py:get_daily_comparison",
                    "message": "get_daily_comparison_result",
                    "data": {"date": date, "found": doc is not None},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion

            if doc:
                # Convert ISO strings back to datetime
                if "created_at" in doc and isinstance(doc["created_at"], str):
                    doc["created_at"] = datetime.fromisoformat(doc["created_at"])
                if "updated_at" in doc and isinstance(doc["updated_at"], str):
                    doc["updated_at"] = datetime.fromisoformat(doc["updated_at"])

                return DailyComparison(**doc)

            return None

        except Exception as e:
            logger.error(
                f"Error getting daily comparison for date {date}: {e}", exc_info=True
            )
            return None

    def get_headlines_by_date(
        self, date: str, political_side: Optional[str] = None
    ) -> List[Headline]:
        """
        Get headlines for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format
            political_side: Optional filter by 'conservative' or 'liberal'

        Returns:
            List of Headline objects
        """
        try:
            collection = self.db.headlines
            query = {"date": date}
            if political_side:
                query["political_side"] = political_side

            docs = collection.find(query).sort("final_score", -1)

            headlines = []
            for doc in docs:
                # Convert ISO strings back to datetime
                if "published_at" in doc and isinstance(doc["published_at"], str):
                    doc["published_at"] = datetime.fromisoformat(doc["published_at"])
                if "collected_at" in doc and isinstance(doc["collected_at"], str):
                    doc["collected_at"] = datetime.fromisoformat(doc["collected_at"])
                # Convert URL string back to HttpUrl
                if "url" in doc:
                    doc["url"] = str(doc["url"])

                headlines.append(Headline(**doc))

            return headlines

        except Exception as e:
            side_filter = f" (side: {political_side})" if political_side else ""
            logger.error(
                f"Error getting headlines for date {date}{side_filter}: {e}",
                exc_info=True,
            )
            return []

    def get_recent_comparisons(self, days: int = 7) -> List[DailyComparison]:
        """
        Get recent daily comparisons.

        Args:
            days: Number of days to retrieve

        Returns:
            List of DailyComparison objects
        """
        try:
            collection = self.db.daily_comparisons
            docs = collection.find().sort("date", -1).limit(days)

            comparisons = []
            for doc in docs:
                # Convert ISO strings back to datetime
                if "created_at" in doc and isinstance(doc["created_at"], str):
                    doc["created_at"] = datetime.fromisoformat(doc["created_at"])
                if "updated_at" in doc and isinstance(doc["updated_at"], str):
                    doc["updated_at"] = datetime.fromisoformat(doc["updated_at"])

                comparisons.append(DailyComparison(**doc))

            return comparisons

        except Exception as e:
            logger.error(
                f"Error getting recent comparisons (last {days} days): {e}",
                exc_info=True,
            )
            return []

    def get_openai_call_count(self, date: str) -> int:
        """
        Get current OpenAI API call count for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            Current call count (0 if no record exists)
        """
        try:
            collection = self.db.api_rate_limits
            doc = collection.find_one({"date": date})

            if doc:
                return doc.get("openai_calls", 0)

            return 0

        except Exception as e:
            logger.error(
                f"Error getting OpenAI call count for date {date}: {e}", exc_info=True
            )
            return 0

    def increment_openai_call_count(self, date: str) -> int:
        """
        Increment OpenAI API call count for a specific date.
        Uses atomic operation to prevent race conditions.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            New call count after increment
        """
        try:
            collection = self.db.api_rate_limits

            # Use find_one_and_update with upsert for atomic increment
            result = collection.find_one_and_update(
                {"date": date},
                {
                    "$inc": {"openai_calls": 1},
                    "$set": {"updated_at": datetime.utcnow()},
                    "$setOnInsert": {"date": date},
                },
                upsert=True,
                return_document=True,
            )

            new_count = result.get("openai_calls", 1)
            logger.debug(f"Incremented OpenAI call count for {date}: {new_count}")
            return new_count

        except Exception as e:
            logger.error(
                f"Error incrementing OpenAI call count for date {date}: {e}",
                exc_info=True,
            )
            raise

    def get_headlines_for_comparison(
        self, days: int = 30, political_side: Optional[str] = None
    ) -> List[Headline]:
        """
        Get headlines with both LLM and local scores for model comparison.

        Args:
            days: Number of days to look back
            political_side: Optional filter by 'conservative' or 'liberal'

        Returns:
            List of Headline objects with both scores
        """
        # #region agent log
        import time

        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H7",
                "location": "database.py:get_headlines_for_comparison",
                "message": "get_headlines_for_comparison_entry",
                "data": {"days": days, "political_side": political_side},
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion
        try:
            collection = self.db.headlines
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()

            query = {
                "date": {"$gte": cutoff_date},
                "uplift_score": {"$exists": True, "$ne": None},
                "local_sentiment_score": {"$exists": True, "$ne": None},
            }

            if political_side:
                query["political_side"] = political_side

            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H7",
                    "location": "database.py:get_headlines_for_comparison",
                    "message": "before_query",
                    "data": {"query": query, "cutoff_date": cutoff_date},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            docs = collection.find(query).sort("date", -1)
            # #region agent log
            doc_list = list(docs)
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H7",
                    "location": "database.py:get_headlines_for_comparison",
                    "message": "after_query",
                    "data": {"docs_count": len(doc_list)},
                    "timestamp": int(time.time() * 1000),
                }
            )
            docs = iter(doc_list)
            # #endregion

            headlines = []
            for doc in docs:
                # Convert ISO strings back to datetime
                if "published_at" in doc and isinstance(doc["published_at"], str):
                    doc["published_at"] = datetime.fromisoformat(doc["published_at"])
                if "collected_at" in doc and isinstance(doc["collected_at"], str):
                    doc["collected_at"] = datetime.fromisoformat(doc["collected_at"])
                # Convert URL string back to HttpUrl
                if "url" in doc:
                    doc["url"] = str(doc["url"])

                headlines.append(Headline(**doc))

            return headlines

        except Exception as e:
            side_filter = f" (side: {political_side})" if political_side else ""
            logger.error(
                f"Error getting headlines for comparison (last {days} days){side_filter}: {e}",
                exc_info=True,
            )
            return []

    def close(self) -> None:
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
