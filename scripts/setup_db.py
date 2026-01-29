#!/usr/bin/env python3
"""
Database setup script - creates indexes and validates connection.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from news_sentiment.utils.logging_config import setup_logging
from news_sentiment.database import NewsDatabase
from news_sentiment.config import get_config

import logging

logger = logging.getLogger(__name__)


def main():
    """Setup database and create indexes."""
    setup_logging()
    config = get_config()

    logger.info("Setting up MongoDB database...")
    logger.info(f"Connection URI: {config.mongodb.uri}")
    logger.info(f"Database: {config.mongodb.database_name}")

    try:
        db = NewsDatabase()
        logger.info("✓ Database connection successful")
        logger.info("✓ Indexes created")
        logger.info("\nDatabase setup complete!")

        db.close()
        return 0

    except Exception as e:
        logger.error(f"✗ Database setup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
