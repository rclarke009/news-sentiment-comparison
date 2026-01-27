"""
Rate limiting module for OpenAI API calls.
"""

import logging
from datetime import datetime
from typing import Optional

from news_sentiment.database import NewsDatabase

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when daily API call limit is exceeded."""
    
    def __init__(self, message: str, current_count: int, limit: int):
        """
        Initialize rate limit exception.
        
        Args:
            message: Error message
            current_count: Current call count
            limit: Daily limit
        """
        self.message = message
        self.current_count = current_count
        self.limit = limit
        super().__init__(self.message)


class RateLimiter:
    """Rate limiter for OpenAI API calls."""
    
    def __init__(self, database: NewsDatabase, daily_limit: int = 20):
        """
        Initialize rate limiter.
        
        Args:
            database: NewsDatabase instance for tracking calls
            daily_limit: Maximum number of calls per day (default: 20)
        """
        self.database = database
        self.daily_limit = daily_limit
    
    def check_and_increment(self, provider: str, date: Optional[str] = None) -> bool:
        """
        Check if API call is allowed and increment count if so.
        
        Args:
            provider: LLM provider ('openai' or 'groq')
            date: Date string in YYYY-MM-DD format (defaults to today in UTC)
            
        Returns:
            True if call is allowed and count was incremented
            
        Raises:
            RateLimitExceeded: If daily limit is reached
        """
        # Only track OpenAI calls, skip Groq
        if provider != "openai":
            return True
        
        # Use UTC date if not provided
        if date is None:
            date = datetime.utcnow().date().isoformat()
        
        # Get current count
        current_count = self.database.get_openai_call_count(date)
        
        # Check if limit would be exceeded
        if current_count >= self.daily_limit:
            error_message = (
                f"Daily OpenAI API call limit reached ({self.daily_limit} calls/day). "
                "This is a test project with rate limiting to control costs. "
                "Please try again tomorrow or switch to Groq provider for unlimited calls."
            )
            logger.warning(
                f"OpenAI rate limit exceeded for {date}: {current_count}/{self.daily_limit} calls"
            )
            raise RateLimitExceeded(error_message, current_count, self.daily_limit)
        
        # Increment count atomically
        new_count = self.database.increment_openai_call_count(date)
        
        logger.debug(
            f"OpenAI API call allowed for {date}: {new_count}/{self.daily_limit} calls used"
        )
        
        return True
