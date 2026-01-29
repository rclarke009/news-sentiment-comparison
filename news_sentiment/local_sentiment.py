"""
Local sentiment analysis using Hugging Face transformers.
"""

import logging
from typing import Dict, Union
from transformers import pipeline

logger = logging.getLogger(__name__)


class LocalSentimentScorer:
    """Scores headlines using a local Hugging Face transformer model."""

    def __init__(self):
        """Initialize the local sentiment pipeline."""
        try:
            # Initialize sentiment analysis pipeline
            # Uses default model: distilbert-base-uncased-finetuned-sst-2-english
            self.pipeline = pipeline("sentiment-analysis")
            logger.info("Local sentiment pipeline initialized successfully")
        except Exception as e:
            logger.error(
                f"Failed to initialize local sentiment pipeline: {e}", exc_info=True
            )
            raise

    def score_text(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Score text for sentiment using local model.

        Args:
            text: Text to analyze (headline title + description)

        Returns:
            Dictionary with:
                - score: float (mapped to -5 to +5 scale)
                - label: str (POSITIVE or NEGATIVE)
                - confidence: float (model confidence 0.0 to 1.0)
        """
        try:
            # Run sentiment analysis
            result = self.pipeline(text)[0]

            label = result["label"]  # "POSITIVE" or "NEGATIVE"
            confidence = result["score"]  # 0.0 to 1.0

            # Map to -5 to +5 scale based on label and confidence
            mapped_score = self._map_to_scale(label, confidence)

            return {"score": mapped_score, "label": label, "confidence": confidence}

        except Exception as e:
            logger.error(f"Error scoring text with local model: {e}", exc_info=True)
            # Return neutral score on error
            return {"score": 0.0, "label": "NEUTRAL", "confidence": 0.0}

    def _map_to_scale(self, label: str, confidence: float) -> float:
        """
        Map POSITIVE/NEGATIVE label with confidence to -5 to +5 scale.

        Args:
            label: "POSITIVE" or "NEGATIVE"
            confidence: Model confidence score (0.0 to 1.0)

        Returns:
            Score from -5 to +5
        """
        if label == "POSITIVE":
            if confidence >= 0.9:
                return 4.5
            elif confidence >= 0.7:
                return 3.0
            else:
                return 1.5
        elif label == "NEGATIVE":
            if confidence >= 0.9:
                return -4.5
            elif confidence >= 0.7:
                return -3.0
            else:
                return -1.5
        else:
            # Neutral/unknown
            return 0.0
