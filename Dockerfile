# Multi-stage Dockerfile for News Sentiment API
# Stage 1: Base image with dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Builder stage for installing Python dependencies
FROM base as builder

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 3: Production image
FROM base as production

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY news_sentiment/ /app/news_sentiment/
COPY scripts/ /app/scripts/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "news_sentiment.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 4: Development image with additional tools
FROM production as development

# Switch back to root to install dev dependencies
USER root

# Install development dependencies (requirements-dev.txt includes -r requirements.txt)
COPY requirements.txt requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Install additional dev tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Switch back to non-root user
USER appuser

# Enable hot reload for development
CMD ["uvicorn", "news_sentiment.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
