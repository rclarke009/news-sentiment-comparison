"""
Sentiment scoring module using LLM APIs (Groq or OpenAI).
"""

import logging
import re
from typing import Optional
from datetime import datetime
from groq import Groq
from openai import OpenAI

from news_sentiment.config import get_config
from news_sentiment.models import Headline
from news_sentiment.rate_limiter import RateLimiter, RateLimitExceeded
from news_sentiment.database import NewsDatabase

logger = logging.getLogger(__name__)


class SentimentScorer:
    """Scores headlines for uplift/positivity using LLM APIs."""
    
    def __init__(self, database: Optional[NewsDatabase] = None):
        """
        Initialize the sentiment scorer with configuration.
        
        Args:
            database: Optional NewsDatabase instance for rate limiting (required for OpenAI rate limiting)
        """
        self.config = get_config()
        self.llm_client = self._create_client()
        self.puff_keywords = self.config.puff_pieces.keywords
        self.rate_limiter: Optional[RateLimiter] = None
        
        # Initialize rate limiter if database is provided
        if database is not None:
            self.rate_limiter = RateLimiter(database, daily_limit=20)
    
    def _create_client(self):
        """Create the appropriate LLM client based on configuration."""
        if self.config.llm.provider == "groq":
            if not self.config.llm.groq_api_key:
                raise ValueError("GROQ_API_KEY is required when provider is 'groq'")
            return Groq(api_key=self.config.llm.groq_api_key)
        else:
            if not self.config.llm.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when provider is 'openai'")
            return OpenAI(api_key=self.config.llm.openai_api_key)
    
    def score_headline(self, headline: Headline) -> float:
        """
        Score a headline for uplift/positivity.
        
        Args:
            headline: Headline to score
            
        Returns:
            Uplift score from -5 (very negative) to +5 (very positive/uplifting)
        """
        try:
            # Get base score from LLM
            base_score = self._get_llm_score(headline)
            
            # Apply keyword boost for puff pieces
            keyword_boost = self._calculate_keyword_boost(headline)
            
            # Calculate final score (clamped to -5 to +5 range)
            final_score = max(-5.0, min(5.0, base_score + keyword_boost))
            
            # Update headline with scores
            headline.uplift_score = base_score
            headline.keyword_boost = keyword_boost
            headline.final_score = final_score
            
            logger.debug(
                f"Scored '{headline.title[:50]}...': "
                f"base={base_score:.2f}, boost={keyword_boost:.2f}, final={final_score:.2f}"
            )
            
            return final_score
        
        except Exception as e:
            logger.error(f"Error scoring headline '{headline.title}': {e}", exc_info=True)
            # Return neutral score on error
            headline.uplift_score = 0.0
            headline.final_score = 0.0
            return 0.0
    
    def _get_llm_score(self, headline: Headline) -> float:
        """
        Get uplift score from LLM API.
        
        Args:
            headline: Headline to score
            
        Returns:
            Score from -5 to +5
        """
        # Check rate limit for OpenAI before making API call
        if self.config.llm.provider == "openai" and self.rate_limiter is not None:
            try:
                # Get current date for rate limiting
                current_date = datetime.utcnow().date().isoformat()
                self.rate_limiter.check_and_increment("openai", current_date)
            except RateLimitExceeded as e:
                logger.warning(
                    f"Rate limit exceeded for headline '{headline.title[:50]}...': {e.message}"
                )
                # Return neutral score when rate limit is exceeded
                return 0.0
        
        # Construct prompt
        text = headline.title
        if headline.description:
            text += f" {headline.description}"
        
        prompt = f"""Rate how uplifting/positive this news headline is on a scale of -5 to +5.

-5 = Very negative, alarming, depressing
-3 = Somewhat negative
0 = Neutral, factual
+3 = Somewhat positive, mildly uplifting
+5 = Very positive, uplifting, heartwarming, inspiring

Headline: {text}

Respond with ONLY a single number between -5 and +5 (e.g., "3.2" or "-1.5"). Do not include any explanation or other text."""

        try:
            if self.config.llm.provider == "groq":
                response = self.llm_client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=[
                        {"role": "system", "content": "You are a sentiment analysis expert. Respond with only a number."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.llm.temperature,
                    max_tokens=self.config.llm.max_tokens
                )
            else:
                response = self.llm_client.chat.completions.create(
                    model=self.config.llm.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a sentiment analysis expert. Respond with only a number."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.llm.temperature,
                    max_tokens=self.config.llm.max_tokens
                )
            
            content = response.choices[0].message.content.strip()
            
            # Extract number from response
            score = self._parse_score(content)
            
            return score
        
        except Exception as e:
            provider = self.config.llm.provider
            logger.error(f"LLM API error ({provider}) for headline '{headline.title[:50]}...' (source: {headline.source}): {e}", exc_info=True)
            raise
    
    def _parse_score(self, content: str) -> float:
        """
        Parse numeric score from LLM response.
        
        Args:
            content: LLM response text
            
        Returns:
            Parsed score, or 0.0 if parsing fails
        """
        # Try to extract a number between -5 and +5
        # Look for patterns like "3.2", "-1.5", "4", etc.
        patterns = [
            r"(-?\d+\.?\d*)",  # Any number with optional decimal
            r"[-+]?\d+\.?\d*"   # Explicit sign
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                try:
                    score = float(matches[0])
                    # Clamp to valid range
                    score = max(-5.0, min(5.0, score))
                    return score
                except ValueError:
                    continue
        
        # If no number found, try to extract from common phrases
        content_lower = content.lower()
        if "very positive" in content_lower or "very uplifting" in content_lower:
            return 4.5
        elif "positive" in content_lower or "uplifting" in content_lower:
            return 3.0
        elif "neutral" in content_lower:
            return 0.0
        elif "negative" in content_lower:
            return -2.0
        elif "very negative" in content_lower:
            return -4.5
        
        logger.warning(f"Could not parse score from LLM response: '{content}' (length: {len(content)})")
        return 0.0
    
    def _calculate_keyword_boost(self, headline: Headline) -> float:
        """
        Calculate keyword boost for puff pieces.
        
        Args:
            headline: Headline to check for keywords
            
        Returns:
            Boost value (0.0 or positive)
        """
        text = headline.title.lower()
        if headline.description:
            text += " " + headline.description.lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in self.puff_keywords if keyword.lower() in text)
        
        if matches == 0:
            return 0.0
        
        # Apply boost multiplier
        boost = matches * self.config.puff_pieces.boost_multiplier
        
        # Cap the boost to prevent excessive inflation
        max_boost = 2.0
        return min(boost, max_boost)
    
    def score_headlines(self, headlines: list[Headline]) -> list[Headline]:
        """
        Score multiple headlines.
        
        Args:
            headlines: List of headlines to score
            
        Returns:
            List of headlines with scores assigned
        """
        logger.info(f"Scoring {len(headlines)} headlines...")
        
        scored = []
        for i, headline in enumerate(headlines, 1):
            try:
                self.score_headline(headline)
                scored.append(headline)
                
                # Log progress every 10 headlines
                if i % 10 == 0:
                    logger.info(f"Scored {i}/{len(headlines)} headlines...")
            
            except Exception as e:
                logger.error(f"Failed to score headline {i}: {e}")
                # Continue with next headline
                continue
        
        logger.info(f"Successfully scored {len(scored)}/{len(headlines)} headlines")
        return scored
