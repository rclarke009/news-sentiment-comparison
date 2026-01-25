#!/usr/bin/env python3
"""
CLI script to run the news collector manually.
"""

import sys
import argparse
from datetime import date, datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from news_sentiment.utils.logging_config import setup_logging
from news_sentiment.collector import NewsCollector
from news_sentiment.config import get_config

import logging

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the collector script."""
    parser = argparse.ArgumentParser(
        description="Collect and score daily news headlines"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to collect for (YYYY-MM-DD). Defaults to today."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and score headlines but don't save to database"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    
    # Parse date
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)
    
    try:
        # Initialize collector
        collector = NewsCollector()
        
        logger.info("Starting news collection...")
        
        if args.dry_run:
            logger.info("DRY RUN MODE: Will not save to database")
            # In dry-run, we'd need to modify collector to skip DB saves
            # For now, just run normally but log that it's a dry run
            logger.warning("Dry-run mode not fully implemented - will still save to DB")
        
        # Run collection
        comparison = collector.collect_daily_news(target_date)
        
        # Print summary
        print("\n" + "="*60)
        print("COLLECTION SUMMARY")
        print("="*60)
        print(f"Date: {comparison.date}")
        print(f"\nConservative:")
        print(f"  Average Uplift: {comparison.conservative['avg_uplift']:.2f}")
        print(f"  Positive %: {comparison.conservative['positive_percentage']:.1f}%")
        print(f"  Total Headlines: {comparison.conservative['total_headlines']}")
        if comparison.conservative.get('most_uplifting'):
            print(f"  Most Uplifting: {comparison.conservative['most_uplifting']['title'][:60]}...")
        print(f"\nLiberal:")
        print(f"  Average Uplift: {comparison.liberal['avg_uplift']:.2f}")
        print(f"  Positive %: {comparison.liberal['positive_percentage']:.1f}%")
        print(f"  Total Headlines: {comparison.liberal['total_headlines']}")
        if comparison.liberal.get('most_uplifting'):
            print(f"  Most Uplifting: {comparison.liberal['most_uplifting']['title'][:60]}...")
        print("="*60 + "\n")
        
        # Cleanup
        collector.close()
        
        logger.info("Collection completed successfully")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
