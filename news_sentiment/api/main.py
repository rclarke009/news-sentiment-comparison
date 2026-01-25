"""
FastAPI application main file.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from news_sentiment.config import get_config
from news_sentiment.api import routes

logger = logging.getLogger(__name__)
config = get_config()

# Create FastAPI app
app = FastAPI(
    title="News Sentiment Comparison API",
    description="API for comparing sentiment and uplift scores between conservative and liberal news sources",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint - provides API information."""
    return {
        "message": "News Sentiment Comparison API",
        "version": "0.1.0",
        "docs": "/docs",
        "api": "/api/v1"
    }


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
