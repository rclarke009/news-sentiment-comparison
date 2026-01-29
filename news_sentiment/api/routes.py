"""
API route handlers.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Header, Request
import requests

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
    ModelComparisonResponse,
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
            logger.error(
                f"Failed to initialize database connection: {e}", exc_info=True
            )
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
    liberal = [_newsapi_id_to_display_name(sid) for sid in config.sources.liberal] + [
        rss.name for rss in config.sources.liberal_rss
    ]
    return SourcesResponse(conservative=conservative, liberal=liberal)


@router.get("/health", tags=["health"])
async def health_check(request: Request):
    """
    Simple health check endpoint (app is running).

    Used by keep-alive pings, Render health checks, and smoke tests.
    Returns 200 as long as the app is running, without checking database connectivity.
    """
    # #region agent log
    logger.info(
        "health_check entered path=/health client=%s",
        request.client.host if request.client else "unknown",
        extra={"hypothesisId": "H1_H3_H5", "path": "/health"},
    )
    # #endregion
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/db", tags=["health"])
async def health_check_db(request: Request):
    """
    Full health check endpoint (app + database connectivity).

    Use this for monitoring/debugging when you need to verify database connectivity.
    Returns 503 if database connection fails.
    """
    # #region agent log
    logger.info(
        "health_check_db entered path=/health/db client=%s",
        request.client.host if request.client else "unknown",
        extra={"hypothesisId": "H4", "path": "/health/db"},
    )
    # #endregion
    try:
        # Test database connection
        db = get_db()
        db.client.admin.command("ping")
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
        }
    except Exception as e:
        context = _get_request_context(request)
        logger.error(f"Health check (DB) failed - {context}: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/today", response_model=DailyComparisonResponse, tags=["comparisons"])
async def get_today(request: Request):
    """Get today's comparison."""
    # #region agent log
    import time
    import json
    from pathlib import Path

    _DEBUG_LOG_PATH = Path(__file__).resolve().parents[3] / ".cursor" / "debug.log"

    def _agent_log(payload: dict) -> None:
        try:
            with open(_DEBUG_LOG_PATH, "a") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception:
            pass

    _agent_log(
        {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "H6_H7_H8",
            "location": "routes.py:get_today",
            "message": "get_today_entry",
            "data": {},
            "timestamp": int(time.time() * 1000),
        }
    )
    # #endregion
    try:
        # #region agent log
        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H8",
                "location": "routes.py:get_today",
                "message": "before_get_db",
                "data": {},
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion
        db = get_db()
        # Use UTC date consistently (Render servers use UTC)
        today = datetime.utcnow().date().isoformat()
        # #region agent log
        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H4",
                "location": "routes.py:get_today",
                "message": "querying_date",
                "data": {"today": today},
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion
        comparison = db.get_daily_comparison(today)
        # #region agent log
        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H7_H8",
                "location": "routes.py:get_today",
                "message": "after_get_daily_comparison",
                "data": {"found": comparison is not None, "today": today},
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion

        if not comparison:
            # #region agent log
            _agent_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H7",
                    "location": "routes.py:get_today",
                    "message": "no_comparison_found",
                    "data": {"today": today},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            logger.info("No comparison for today (%s)", today)
            raise HTTPException(
                status_code=404, detail=f"No comparison found for today ({today})"
            )

        # #region agent log
        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H7",
                "location": "routes.py:get_today",
                "message": "returning_comparison",
                "data": {"date": comparison.date},
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion
        return _convert_comparison_to_response(comparison)
    except HTTPException:
        raise
    except Exception as e:
        # #region agent log
        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H7_H8",
                "location": "routes.py:get_today",
                "message": "get_today_exception",
                "data": {"error": str(e)},
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion
        context = _get_request_context(request)
        logger.error(
            f"Error fetching today's comparison - {context}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching today's comparison",
        )


@router.get(
    "/date/{date_str}", response_model=DailyComparisonResponse, tags=["comparisons"]
)
async def get_date(date_str: str, request: Request):
    """Get comparison for a specific date (YYYY-MM-DD)."""
    try:
        # Validate date format
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    try:
        db = get_db()
        comparison = db.get_daily_comparison(date_str)

        if not comparison:
            logger.info("No comparison for date %s", date_str)
            raise HTTPException(
                status_code=404, detail=f"No comparison found for date {date_str}"
            )

        return _convert_comparison_to_response(comparison)
    except HTTPException:
        raise
    except Exception as e:
        context = _get_request_context(request)
        logger.error(
            f"Error fetching comparison for date {date_str} - {context}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching comparison for date {date_str}",
        )


@router.get("/history", response_model=HistoryResponse, tags=["comparisons"])
async def get_history(days: int = Query(7, ge=1, le=365), request: Request = None):
    """Get historical comparisons for the last N days."""
    try:
        db = get_db()
        comparisons = db.get_recent_comparisons(days)

        if not comparisons:
            logger.info("No historical comparisons (days=%d)", days)
            return HistoryResponse(comparisons=[], days=0)

        return HistoryResponse(
            comparisons=[_convert_comparison_to_response(c) for c in comparisons],
            days=len(comparisons),
        )
    except HTTPException:
        raise
    except Exception as e:
        context = _get_request_context(request) if request else "unknown"
        logger.error(
            f"Error fetching history for {days} days - {context}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching historical comparisons",
        )


@router.get("/most-uplifting", response_model=MostUpliftingResponse, tags=["stories"])
async def get_most_uplifting(
    side: str = Query(..., description="'conservative' or 'liberal'"),
    date_str: Optional[str] = Query(
        None, description="Date in YYYY-MM-DD format (defaults to today)"
    ),
    request: Request = None,
):
    """Get the most uplifting story for a side on a specific date."""
    if side not in ["conservative", "liberal"]:
        raise HTTPException(
            status_code=400, detail="side must be 'conservative' or 'liberal'"
        )

    if date_str is None:
        # Use UTC date consistently (Render servers use UTC)
        date_str = datetime.utcnow().date().isoformat()
    else:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
            )

    try:
        db = get_db()
        comparison = db.get_daily_comparison(date_str)

        if not comparison:
            raise HTTPException(
                status_code=404, detail=f"No comparison found for date {date_str}"
            )

        side_data = (
            comparison.conservative if side == "conservative" else comparison.liberal
        )
        most_uplifting = side_data.get("most_uplifting")

        if not most_uplifting:
            raise HTTPException(
                status_code=404,
                detail=f"No uplifting story found for {side} on {date_str}",
            )

        return MostUpliftingResponse(
            title=most_uplifting["title"],
            description=most_uplifting.get("description"),
            url=str(most_uplifting["url"]),
            source=most_uplifting["source"],
            uplift_score=most_uplifting["uplift_score"],
            final_score=most_uplifting["final_score"],
            published_at=(
                most_uplifting["published_at"].isoformat()
                if isinstance(most_uplifting["published_at"], datetime)
                else str(most_uplifting["published_at"])
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        context = _get_request_context(request) if request else "unknown"
        logger.error(
            f"Error fetching most uplifting story for {side} on {date_str} - {context}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching most uplifting story",
        )


@router.get("/stats", response_model=StatsResponse, tags=["statistics"])
async def get_stats(days: int = Query(30, ge=1, le=365), request: Request = None):
    """Get aggregate statistics over the last N days."""
    try:
        db = get_db()
        comparisons = db.get_recent_comparisons(days)

        if not comparisons:
            raise HTTPException(
                status_code=404, detail="No data available for statistics"
            )

        conservative_avgs = [
            c.conservative.get("avg_uplift", 0)
            for c in comparisons
            if c.conservative.get("avg_uplift") is not None
        ]
        liberal_avgs = [
            c.liberal.get("avg_uplift", 0)
            for c in comparisons
            if c.liberal.get("avg_uplift") is not None
        ]

        conservative_positive_pcts = [
            c.conservative.get("positive_percentage", 0)
            for c in comparisons
            if c.conservative.get("positive_percentage") is not None
        ]
        liberal_positive_pcts = [
            c.liberal.get("positive_percentage", 0)
            for c in comparisons
            if c.liberal.get("positive_percentage") is not None
        ]

        return StatsResponse(
            total_days=len(comparisons),
            conservative_avg=(
                sum(conservative_avgs) / len(conservative_avgs)
                if conservative_avgs
                else 0.0
            ),
            liberal_avg=sum(liberal_avgs) / len(liberal_avgs) if liberal_avgs else 0.0,
            conservative_positive_pct=(
                sum(conservative_positive_pcts) / len(conservative_positive_pcts)
                if conservative_positive_pcts
                else 0.0
            ),
            liberal_positive_pct=(
                sum(liberal_positive_pcts) / len(liberal_positive_pcts)
                if liberal_positive_pcts
                else 0.0
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        context = _get_request_context(request) if request else "unknown"
        logger.error(
            f"Error fetching stats for {days} days - {context}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching statistics"
        )


def _client_ip(request: Request) -> str:
    """Return client IP, honoring X-Forwarded-For when behind a proxy (e.g. Render)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_request_context(request: Request) -> str:
    """Extract request context for logging (path, method, client IP)."""
    path = request.url.path
    method = request.method
    client_ip = _client_ip(request)
    return f"{method} {path} (IP: {client_ip})"


@router.post("/collect", tags=["collection"])
async def trigger_collection(
    request: Request,
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret"),
):
    """
    Trigger news collection manually (for use with external cron services).

    Requires X-Cron-Secret header matching CRON_SECRET_KEY environment variable.
    This endpoint is protected to prevent unauthorized collection triggers.
    """
    expected_secret = os.getenv("CRON_SECRET_KEY")

    if not expected_secret:
        logger.warning("CRON_SECRET_KEY not set - endpoint is disabled for security")
        raise HTTPException(
            status_code=503,
            detail="Collection endpoint is not configured",
        )

    if not x_cron_secret or x_cron_secret != expected_secret:
        ip = _client_ip(request)
        logger.warning("Unauthorized collection attempt from IP=%s", ip)
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing X-Cron-Secret header",
        )

    try:
        logger.info("Manual collection triggered via API endpoint")
        collector = NewsCollector()

        # Run collection for today
        comparison = collector.collect_daily_news()

        # Log collection results to diagnose scoring issues
        logger.info(
            f"Collection completed for {comparison.date}: "
            f"conservative avg_uplift={comparison.conservative.get('avg_uplift', 0)}, "
            f"total_headlines={comparison.conservative.get('total_headlines', 0)}, "
            f"liberal avg_uplift={comparison.liberal.get('avg_uplift', 0)}, "
            f"total_headlines={comparison.liberal.get('total_headlines', 0)}"
        )

        # Cleanup
        collector.close()

        return {
            "status": "success",
            "message": "Collection completed successfully",
            "date": comparison.date,
            "conservative": {
                "avg_uplift": comparison.conservative.get("avg_uplift", 0),
                "total_headlines": comparison.conservative.get("total_headlines", 0),
            },
            "liberal": {
                "avg_uplift": comparison.liberal.get("avg_uplift", 0),
                "total_headlines": comparison.liberal.get("total_headlines", 0),
            },
        }
    except requests.exceptions.HTTPError as e:
        # Check if it's a 429 rate limit error
        context = _get_request_context(request)
        if (
            hasattr(e, "response")
            and e.response is not None
            and e.response.status_code == 429
        ):
            logger.error(
                f"NewsAPI rate limit exceeded during collection - {context}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=429,
                detail=f"NewsAPI rate limit exceeded. {str(e)}. This may be due to the daily limit (100 requests/day on free tier). Please try again later.",
            )
        # Re-raise other HTTP errors as 500
        logger.error(
            f"HTTP error during manual collection - {context}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")
    except Exception as e:
        context = _get_request_context(request)
        logger.error(f"Error during manual collection - {context}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")


def _convert_comparison_to_response(
    comparison: DailyComparison,
) -> DailyComparisonResponse:
    """Convert DailyComparison model to API response schema."""
    try:
        return DailyComparisonResponse(
            date=comparison.date,
            conservative=_convert_side_stats(comparison.conservative),
            liberal=_convert_side_stats(comparison.liberal),
            created_at=(
                comparison.created_at.isoformat()
                if isinstance(comparison.created_at, datetime)
                else str(comparison.created_at)
            ),
            updated_at=(
                comparison.updated_at.isoformat()
                if isinstance(comparison.updated_at, datetime)
                else str(comparison.updated_at)
            ),
        )
    except Exception as e:
        logger.error(f"Error converting comparison to response: {e}", exc_info=True)
        raise ValueError(f"Failed to convert comparison data: {str(e)}")


@router.get(
    "/model-comparison", response_model=ModelComparisonResponse, tags=["statistics"]
)
async def get_model_comparison(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    source: Optional[str] = Query(
        None, description="Filter by 'conservative' or 'liberal'"
    ),
    request: Request = None,
):
    """
    Get comparison statistics between LLM and local sentiment models.

    Returns correlation stats, agreement rate, and divergence examples.
    """
    # #region agent log
    import time
    import json
    from pathlib import Path

    _DEBUG_LOG_PATH = Path(__file__).resolve().parents[3] / ".cursor" / "debug.log"

    def _agent_log(payload: dict) -> None:
        try:
            with open(_DEBUG_LOG_PATH, "a") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception:
            pass

    _agent_log(
        {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "H7",
            "location": "routes.py:get_model_comparison",
            "message": "get_model_comparison_entry",
            "data": {"days": days, "source": source},
            "timestamp": int(time.time() * 1000),
        }
    )
    # #endregion
    if source and source not in ["conservative", "liberal"]:
        raise HTTPException(
            status_code=400, detail="source must be 'conservative' or 'liberal'"
        )

    try:
        import statistics

        db = get_db()
        # #region agent log
        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H7",
                "location": "routes.py:get_model_comparison",
                "message": "before_get_headlines_for_comparison",
                "data": {"days": days, "source": source},
                "timestamp": int(time.time() * 1000),
            }
        )
        # #endregion
        headlines = db.get_headlines_for_comparison(days=days, political_side=source)
        # #region agent log
        _agent_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H7",
                "location": "routes.py:get_model_comparison",
                "message": "after_get_headlines_for_comparison",
                "data": {
                    "headlines_count": len(headlines),
                    "days": days,
                    "source": source,
                },
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
                    "hypothesisId": "H7",
                    "location": "routes.py:get_model_comparison",
                    "message": "no_headlines_with_both_scores",
                    "data": {"days": days, "source": source},
                    "timestamp": int(time.time() * 1000),
                }
            )
            # #endregion
            raise HTTPException(
                status_code=404,
                detail=f"No headlines with both scores found for the last {days} days",
            )

        # Calculate statistics
        llm_scores = []
        local_scores = []
        score_differences = []
        agreements = 0  # Both positive or both negative
        total_comparable = 0

        # Track by political side
        conservative_llm = []
        conservative_local = []
        liberal_llm = []
        liberal_local = []

        # Find divergence examples (large differences)
        divergence_examples = []

        for headline in headlines:
            if (
                headline.uplift_score is not None
                and headline.local_sentiment_score is not None
            ):
                llm_score = headline.uplift_score
                local_score = headline.local_sentiment_score

                llm_scores.append(llm_score)
                local_scores.append(local_score)

                diff = abs(llm_score - local_score)
                score_differences.append(diff)

                # Check agreement (both positive or both negative)
                if (llm_score > 0 and local_score > 0) or (
                    llm_score < 0 and local_score < 0
                ):
                    agreements += 1
                total_comparable += 1

                # Track by side
                if headline.political_side == "conservative":
                    conservative_llm.append(llm_score)
                    conservative_local.append(local_score)
                else:
                    liberal_llm.append(llm_score)
                    liberal_local.append(local_score)

                # Collect divergence examples (difference > 2.0)
                if diff > 2.0 and len(divergence_examples) < 10:
                    divergence_examples.append(
                        {
                            "title": headline.title[:100],
                            "source": headline.source,
                            "political_side": headline.political_side,
                            "llm_score": round(llm_score, 2),
                            "local_score": round(local_score, 2),
                            "local_label": headline.local_sentiment_label,
                            "local_confidence": round(
                                headline.local_sentiment_confidence or 0.0, 2
                            ),
                            "difference": round(diff, 2),
                        }
                    )

        # Calculate correlation
        correlation = 0.0
        if len(llm_scores) > 1:
            try:
                correlation = statistics.correlation(llm_scores, local_scores)
            except Exception:
                # Fallback if correlation calculation fails
                correlation = 0.0

        # Calculate agreement rate
        agreement_rate = (
            (agreements / total_comparable * 100) if total_comparable > 0 else 0.0
        )

        # Calculate average score difference
        avg_diff = statistics.mean(score_differences) if score_differences else 0.0

        # Calculate side-specific stats
        conservative_correlation = 0.0
        if len(conservative_llm) > 1:
            try:
                conservative_correlation = statistics.correlation(
                    conservative_llm, conservative_local
                )
            except Exception:
                pass

        liberal_correlation = 0.0
        if len(liberal_llm) > 1:
            try:
                liberal_correlation = statistics.correlation(liberal_llm, liberal_local)
            except Exception:
                pass

        return ModelComparisonResponse(
            total_headlines=len(headlines),
            agreement_rate=round(agreement_rate, 2),
            avg_score_difference=round(avg_diff, 2),
            correlation=round(correlation, 3),
            divergence_examples=divergence_examples,
            conservative_stats={
                "count": len(conservative_llm),
                "correlation": round(conservative_correlation, 3),
                "avg_llm": (
                    round(statistics.mean(conservative_llm), 2)
                    if conservative_llm
                    else 0.0
                ),
                "avg_local": (
                    round(statistics.mean(conservative_local), 2)
                    if conservative_local
                    else 0.0
                ),
            },
            liberal_stats={
                "count": len(liberal_llm),
                "correlation": round(liberal_correlation, 3),
                "avg_llm": (
                    round(statistics.mean(liberal_llm), 2) if liberal_llm else 0.0
                ),
                "avg_local": (
                    round(statistics.mean(liberal_local), 2) if liberal_local else 0.0
                ),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        context = _get_request_context(request) if request else "unknown"
        logger.error(f"Error fetching model comparison - {context}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching model comparison",
        )


def _convert_side_stats(side_data: dict) -> dict:
    """Convert side statistics to response format."""
    try:
        most_uplifting = side_data.get("most_uplifting")
        return {
            "avg_uplift": side_data.get("avg_uplift", 0.0),
            "positive_percentage": side_data.get("positive_percentage", 0.0),
            "total_headlines": side_data.get("total_headlines", 0),
            "most_uplifting": (
                {
                    "title": most_uplifting["title"],
                    "description": most_uplifting.get("description"),
                    "url": str(most_uplifting["url"]),
                    "source": most_uplifting["source"],
                    "uplift_score": most_uplifting["uplift_score"],
                    "final_score": most_uplifting["final_score"],
                    "published_at": (
                        most_uplifting["published_at"].isoformat()
                        if isinstance(most_uplifting["published_at"], datetime)
                        else str(most_uplifting["published_at"])
                    ),
                }
                if most_uplifting
                else None
            ),
            "score_distribution": side_data.get("score_distribution", {}),
            "avg_local_sentiment": side_data.get("avg_local_sentiment"),
            "local_positive_percentage": side_data.get("local_positive_percentage"),
        }
    except (KeyError, TypeError, AttributeError) as e:
        logger.error(
            f"Error converting side stats: {e}. Side data: {side_data}", exc_info=True
        )
        raise ValueError(f"Invalid side data structure: {str(e)}")
