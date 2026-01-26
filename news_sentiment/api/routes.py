"""
API route handlers.
"""

import os
import logging
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import JSONResponse

from news_sentiment.config import get_config
from news_sentiment.database import NewsDatabase
from news_sentiment.collector import NewsCollector
from news_sentiment.models import DailyComparison
from news_sentiment.api.schemas import (
    DailyComparisonResponse,
    HistoryResponse,
    MostUpliftingResponse,
    StatsResponse,
    SourcesResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Lazy database initialization - only connect when needed
_db_instance: Optional[NewsDatabase] = None


def get_db() -> NewsDatabase:
    """Get database instance, initializing on first access."""
    global _db_instance
    if _db_instance is None:
        try:
            _db_instance = NewsDatabase()
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}", exc_info=True)
            # Re-raise as a more specific exception that route handlers can catch
            raise
    return _db_instance


# Acronyms for NewsAPI source IDs (lowercase id -> display name)
_NEWSAPI_ACRONYMS: dict[str, str] = {
    "cnn": "CNN",
    "npr": "NPR",
    "msnbc": "MSNBC",
}


def _newsapi_id_to_display_name(source_id: str) -> str:
    """Convert NewsAPI kebab-case id to display name. Use acronym map when present."""
    lower = source_id.lower()
    if lower in _NEWSAPI_ACRONYMS:
        return _NEWSAPI_ACRONYMS[lower]
    return " ".join(part.capitalize() for part in source_id.split("-"))


@router.get("/sources", response_model=SourcesResponse, tags=["sources"])
async def get_sources():
    """Return configured conservative and liberal news source display names."""
    config = get_config()
    conservative = [
        _newsapi_id_to_display_name(sid) for sid in config.sources.conservative
    ] + [rss.name for rss in config.sources.conservative_rss]
    liberal = [
        _newsapi_id_to_display_name(sid) for sid in config.sources.liberal
    ] + [rss.name for rss in config.sources.liberal_rss]
    return SourcesResponse(conservative=conservative, liberal=liberal)


@router.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        db = get_db()
        db.client.admin.command("ping")
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/today", response_model=DailyComparisonResponse, tags=["comparisons"])
async def get_today():
    """Get today's comparison."""
    try:
        db = get_db()
        # Use UTC date consistently (Render servers use UTC)
        today = datetime.utcnow().date().isoformat()
        comparison = db.get_daily_comparison(today)
        
        if not comparison:
            raise HTTPException(
                status_code=404,
                detail=f"No comparison found for today ({today})"
            )
        
        return _convert_comparison_to_response(comparison)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching today's comparison: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching today's comparison"
        )


@router.get("/date/{date_str}", response_model=DailyComparisonResponse, tags=["comparisons"])
async def get_date(date_str: str):
    """Get comparison for a specific date (YYYY-MM-DD)."""
    try:
        # Validate date format
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    try:
        db = get_db()
        comparison = db.get_daily_comparison(date_str)
        
        if not comparison:
            raise HTTPException(
                status_code=404,
                detail=f"No comparison found for date {date_str}"
            )
        
        return _convert_comparison_to_response(comparison)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching comparison for date {date_str}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching comparison for date {date_str}"
        )


@router.get("/history", response_model=HistoryResponse, tags=["comparisons"])
async def get_history(days: int = Query(7, ge=1, le=365)):
    """Get historical comparisons for the last N days."""
    try:
        db = get_db()
        comparisons = db.get_recent_comparisons(days)
        
        if not comparisons:
            raise HTTPException(
                status_code=404,
                detail="No historical comparisons found"
            )
        
        return HistoryResponse(
            comparisons=[_convert_comparison_to_response(c) for c in comparisons],
            days=len(comparisons)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching history for {days} days: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching historical comparisons"
        )


@router.get("/most-uplifting", response_model=MostUpliftingResponse, tags=["stories"])
async def get_most_uplifting(
    side: str = Query(..., description="'conservative' or 'liberal'"),
    date_str: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (defaults to today)")
):
    """Get the most uplifting story for a side on a specific date."""
    if side not in ["conservative", "liberal"]:
        raise HTTPException(status_code=400, detail="side must be 'conservative' or 'liberal'")
    
    if date_str is None:
        # Use UTC date consistently (Render servers use UTC)
        date_str = datetime.utcnow().date().isoformat()
    else:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    try:
        db = get_db()
        comparison = db.get_daily_comparison(date_str)
        
        if not comparison:
            raise HTTPException(
                status_code=404,
                detail=f"No comparison found for date {date_str}"
            )
        
        side_data = comparison.conservative if side == "conservative" else comparison.liberal
        most_uplifting = side_data.get("most_uplifting")
        
        if not most_uplifting:
            raise HTTPException(
                status_code=404,
                detail=f"No uplifting story found for {side} on {date_str}"
            )
        
        return MostUpliftingResponse(
            title=most_uplifting["title"],
            description=most_uplifting.get("description"),
            url=str(most_uplifting["url"]),
            source=most_uplifting["source"],
            uplift_score=most_uplifting["uplift_score"],
            final_score=most_uplifting["final_score"],
            published_at=most_uplifting["published_at"].isoformat() if isinstance(most_uplifting["published_at"], datetime) else str(most_uplifting["published_at"])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching most uplifting story for {side} on {date_str}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching most uplifting story"
        )


@router.get("/stats", response_model=StatsResponse, tags=["statistics"])
async def get_stats(days: int = Query(30, ge=1, le=365)):
    """Get aggregate statistics over the last N days."""
    try:
        db = get_db()
        comparisons = db.get_recent_comparisons(days)
        
        if not comparisons:
            raise HTTPException(
                status_code=404,
                detail="No data available for statistics"
            )
        
        conservative_avgs = [
            c.conservative.get("avg_uplift", 0) for c in comparisons
            if c.conservative.get("avg_uplift") is not None
        ]
        liberal_avgs = [
            c.liberal.get("avg_uplift", 0) for c in comparisons
            if c.liberal.get("avg_uplift") is not None
        ]
        
        conservative_positive_pcts = [
            c.conservative.get("positive_percentage", 0) for c in comparisons
            if c.conservative.get("positive_percentage") is not None
        ]
        liberal_positive_pcts = [
            c.liberal.get("positive_percentage", 0) for c in comparisons
            if c.liberal.get("positive_percentage") is not None
        ]
        
        return StatsResponse(
            total_days=len(comparisons),
            conservative_avg=sum(conservative_avgs) / len(conservative_avgs) if conservative_avgs else 0.0,
            liberal_avg=sum(liberal_avgs) / len(liberal_avgs) if liberal_avgs else 0.0,
            conservative_positive_pct=sum(conservative_positive_pcts) / len(conservative_positive_pcts) if conservative_positive_pcts else 0.0,
            liberal_positive_pct=sum(liberal_positive_pcts) / len(liberal_positive_pcts) if liberal_positive_pcts else 0.0
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stats for {days} days: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching statistics"
        )


@router.post("/collect", tags=["collection"])
async def trigger_collection(
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret")
):
    """
    Trigger news collection manually (for use with external cron services).
    
    Requires X-Cron-Secret header matching CRON_SECRET_KEY environment variable.
    This endpoint is protected to prevent unauthorized collection triggers.
    """
    expected_secret = os.getenv("CRON_SECRET_KEY")
    
    # Check authentication
    if not expected_secret:
        logger.warning("CRON_SECRET_KEY not set - endpoint is disabled for security")
        raise HTTPException(
            status_code=503,
            detail="Collection endpoint is not configured"
        )
    
    if not x_cron_secret or x_cron_secret != expected_secret:
        logger.warning(f"Unauthorized collection attempt from IP")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing X-Cron-Secret header"
        )
    
    try:
        logger.info("Manual collection triggered via API endpoint")
        collector = NewsCollector()
        
        # Run collection for today
        comparison = collector.collect_daily_news()
        
        # Cleanup
        collector.close()
        
        return {
            "status": "success",
            "message": "Collection completed successfully",
            "date": comparison.date,
            "conservative": {
                "avg_uplift": comparison.conservative.get("avg_uplift", 0),
                "total_headlines": comparison.conservative.get("total_headlines", 0)
            },
            "liberal": {
                "avg_uplift": comparison.liberal.get("avg_uplift", 0),
                "total_headlines": comparison.liberal.get("total_headlines", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error during manual collection: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Collection failed: {str(e)}"
        )


def _convert_comparison_to_response(comparison: DailyComparison) -> DailyComparisonResponse:
    """Convert DailyComparison model to API response schema."""
    try:
        return DailyComparisonResponse(
            date=comparison.date,
            conservative=_convert_side_stats(comparison.conservative),
            liberal=_convert_side_stats(comparison.liberal),
            created_at=comparison.created_at.isoformat() if isinstance(comparison.created_at, datetime) else str(comparison.created_at),
            updated_at=comparison.updated_at.isoformat() if isinstance(comparison.updated_at, datetime) else str(comparison.updated_at)
        )
    except Exception as e:
        logger.error(f"Error converting comparison to response: {e}", exc_info=True)
        raise ValueError(f"Failed to convert comparison data: {str(e)}")


def _convert_side_stats(side_data: dict) -> dict:
    """Convert side statistics to response format."""
    try:
        most_uplifting = side_data.get("most_uplifting")
        return {
            "avg_uplift": side_data.get("avg_uplift", 0.0),
            "positive_percentage": side_data.get("positive_percentage", 0.0),
            "total_headlines": side_data.get("total_headlines", 0),
            "most_uplifting": {
                "title": most_uplifting["title"],
                "description": most_uplifting.get("description"),
                "url": str(most_uplifting["url"]),
                "source": most_uplifting["source"],
                "uplift_score": most_uplifting["uplift_score"],
                "final_score": most_uplifting["final_score"],
                "published_at": most_uplifting["published_at"].isoformat() if isinstance(most_uplifting["published_at"], datetime) else str(most_uplifting["published_at"])
            } if most_uplifting else None,
            "score_distribution": side_data.get("score_distribution", {})
        }
    except (KeyError, TypeError, AttributeError) as e:
        logger.error(f"Error converting side stats: {e}. Side data: {side_data}", exc_info=True)
        raise ValueError(f"Invalid side data structure: {str(e)}")
