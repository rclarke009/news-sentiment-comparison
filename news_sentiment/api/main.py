"""
FastAPI application main file.
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from news_sentiment.config import get_config
from news_sentiment.api import routes

logger = logging.getLogger(__name__)
config = get_config()

# Disable interactive docs in production to reduce attack surface
_is_production = os.getenv("ENV") == "production" or os.getenv("RENDER") == "true"

app = FastAPI(
    title="News Sentiment Comparison API",
    description="API for comparing sentiment and uplift scores between conservative and liberal news sources",
    version="0.1.0",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
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
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.get("/")
async def root():
    """Root endpoint - provides API information."""
    payload = {
        "message": "News Sentiment Comparison API",
        "version": "0.1.0",
        "api": "/api/v1",
    }
    if not _is_production:
        payload["docs"] = "/docs"
    return payload


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("News Sentiment Comparison API starting up...")


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
        reload=True
    )
