"""
MongoDB database operations for news sentiment data.
"""

import logging
from datetime import datetime
from typing import List, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, OperationFailure

from news_sentiment.config import get_config
from news_sentiment.models import Headline, DailyComparison, SideStatistics, MostUpliftingStory
from pydantic.networks import HttpUrl

logger = logging.getLogger(__name__)



def _convert_httpurl_to_str(obj):
    """Recursively convert HttpUrl objects to strings for MongoDB."""
    if isinstance(obj, HttpUrl):
        return str(obj)
    elif isinstance(obj, dict):
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
        try:
            self.client = MongoClient(
                self.config.mongodb.uri,
                serverSelectionTimeoutMS=self.config.mongodb.connection_timeout * 1000
            )
            # Test connection
            self.client.admin.command("ping")
            self.db = self.client[self.config.mongodb.database_name]
            logger.info(f"Connected to MongoDB: {self.config.mongodb.database_name}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
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
            
            logger.debug("Database indexes created")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def save_headlines(self, headlines: List[Headline], date: str) -> int:
        """
        Save headlines to database.
        
        Args:
            headlines: List of headlines to save
            date: Date string in YYYY-MM-DD format
            
        Returns:
            Number of headlines saved
        """
        if not headlines:
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
            result = collection.insert_many(documents)
            logger.info(f"Saved {len(result.inserted_ids)} headlines to database")
            return len(result.inserted_ids)
        
        except Exception as e:
            logger.error(f"Error saving headlines: {e}")
            raise
    
    def save_daily_comparison(self, comparison: DailyComparison) -> bool:
        """
        Save or update daily comparison.
        
        Args:
            comparison: DailyComparison object
            
        Returns:
            True if successful
        """
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
            result = collection.update_one(
                {"date": comparison.date},
                {"$set": doc},
                upsert=True
            )
            
            logger.info(f"Saved daily comparison for {comparison.date}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving daily comparison: {e}")
            raise
    
    def get_daily_comparison(self, date: str) -> Optional[DailyComparison]:
        """
        Get daily comparison for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            DailyComparison or None if not found
        """
        try:
            collection = self.db.daily_comparisons
            doc = collection.find_one({"date": date})
            
            if doc:
                # Convert ISO strings back to datetime
                if "created_at" in doc and isinstance(doc["created_at"], str):
                    doc["created_at"] = datetime.fromisoformat(doc["created_at"])
                if "updated_at" in doc and isinstance(doc["updated_at"], str):
                    doc["updated_at"] = datetime.fromisoformat(doc["updated_at"])
                
                return DailyComparison(**doc)
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting daily comparison: {e}")
            return None
    
    def get_headlines_by_date(
        self,
        date: str,
        political_side: Optional[str] = None
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
            logger.error(f"Error getting headlines: {e}")
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
            logger.error(f"Error getting recent comparisons: {e}")
            return []
    
    def close(self) -> None:
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
