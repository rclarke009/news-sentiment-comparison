"""
FastAPI application main file.
"""

import json
import os
import logging
import time
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from news_sentiment.config import get_config
from news_sentiment.api import routes

logger = logging.getLogger(__name__)
config = get_config()

# #region agent log
_DEBUG_LOG_PATH = Path(__file__).resolve().parents[3] / ".cursor" / "debug.log"


def _agent_log(payload: dict) -> None:
    try:
        with open(_DEBUG_LOG_PATH, "a") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass


# #endregion

# Allow enabling docs in production via ENABLE_DOCS environment variable
# Docs are disabled by default in production to reduce attack surface
_is_production = os.getenv("ENV") == "production" or os.getenv("RENDER") == "true"
_enable_docs = os.getenv("ENABLE_DOCS", "false").lower() == "true"
_docs_enabled = not _is_production or _enable_docs

app = FastAPI(
    title="News Sentiment Comparison API",
    description="API for comparing sentiment and uplift scores between conservative and liberal news sources",
    version="0.1.0",
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security-related HTTP headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS — restrict methods and headers (no wildcards)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "X-Cron-Secret"],
)


# #region agent log
class CORSDebugMiddleware(BaseHTTPMiddleware):
    """Log Origin vs allowlist and response status for /api/v1 to debug CORS."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/v1"):
            return await call_next(request)
        origin = request.headers.get("Origin") or "(none)"
        allowlist = config.api.cors_origins
        in_allowlist = origin in allowlist if origin != "(none)" else "n/a"
        _agent_log(
            {
                "sessionId": "debug-session",
                "hypothesisId": "H1",
                "location": "main.py:CORSDebug",
                "message": "request",
                "data": {
                    "path": path,
                    "origin": origin,
                    "in_allowlist": in_allowlist,
                    "allowlist": allowlist,
                },
                "timestamp": int(time.time() * 1000),
            }
        )
        response = await call_next(request)
        _agent_log(
            {
                "sessionId": "debug-session",
                "hypothesisId": "H3",
                "location": "main.py:CORSDebug",
                "message": "response",
                "data": {
                    "path": path,
                    "status": response.status_code,
                    "origin": origin,
                },
                "timestamp": int(time.time() * 1000),
            }
        )
        return response


app.add_middleware(CORSDebugMiddleware)
# #endregion

# Include routers
app.include_router(routes.router, prefix="/api/v1")


def _get_request_context(request: Request) -> str:
    """Extract request context for logging (path, method, client IP)."""
    path = request.url.path
    method = request.method
    # Get client IP, honoring X-Forwarded-For when behind a proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    return f"{method} {path} (IP: {client_ip})"


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure all errors return proper JSON responses.

    The CORS middleware will automatically add CORS headers to this response.
    """
    context = _get_request_context(request)
    logger.error(f"Unhandled exception - {context}: {exc}", exc_info=True)

    # Don't expose internal error details in production
    error_detail = "Internal server error"
    if not _is_production:
        error_detail = f"Internal server error: {str(exc)}"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": error_detail,
            "error_code": "INTERNAL_SERVER_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.get("/")
async def root():
    """Root endpoint - provides API information."""
    payload = {
        "message": "News Sentiment Comparison API",
        "version": "0.1.0",
        "api": "/api/v1",
    }
    if _docs_enabled:
        payload["docs"] = "/docs"
    return payload


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("News Sentiment Comparison API starting up...")
    # #region agent log
    _agent_log(
        {
            "sessionId": "debug-session",
            "hypothesisId": "H2",
            "location": "main.py:startup",
            "message": "CORS config at startup",
            "data": {
                "cors_origins": config.api.cors_origins,
                "count": len(config.api.cors_origins),
            },
            "timestamp": int(time.time() * 1000),
        }
    )
    # #endregion


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("News Sentiment Comparison API shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "news_sentiment.api.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=True,
    )
