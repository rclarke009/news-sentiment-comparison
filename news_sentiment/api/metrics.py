"""
Prometheus metrics for the News Sentiment API.

Exposes http_requests_total (Counter) and http_request_duration_seconds (Histogram)
with normalized path labels to keep cardinality low.
"""

from prometheus_client import (
    REGISTRY,
    Counter,
    Histogram,
    generate_latest,
)

# Normalized path label: e.g. /api/v1/today -> api_v1_today
_PATH_PREFIX = "/api/v1/"
_KNOWN_PATHS = frozenset(
    {"today", "health", "history", "sources", "stats", "most_uplifting", "collect", "model_comparison"}
)


def _normalize_path(path: str) -> str:
    """Map request path to a low-cardinality label."""
    if path == "/":
        return "root"
    if path == "/metrics":
        return "metrics"
    if path.startswith(_PATH_PREFIX):
        suffix = path[len(_PATH_PREFIX) :].strip("/") or "index"
        if suffix in _KNOWN_PATHS:
            return f"api_v1_{suffix}"
        return "api_v1_other"
    return "other"


_http_requests_total: Counter | None = None
_http_request_duration_seconds: Histogram | None = None


def register_metrics() -> None:
    """Register Prometheus metrics. Call once at startup."""
    global _http_requests_total, _http_request_duration_seconds
    if _http_requests_total is not None:
        return
    _http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status_code"],
    )
    _http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "path"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    )


def record_request(
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    """Record one HTTP request for Prometheus."""
    if _http_requests_total is None or _http_request_duration_seconds is None:
        return
    norm_path = _normalize_path(path)
    status_str = str(status_code)
    _http_requests_total.labels(method=method, path=norm_path, status_code=status_str).inc()
    _http_request_duration_seconds.labels(method=method, path=norm_path).observe(duration_seconds)


def get_metrics_output() -> bytes:
    """Return Prometheus exposition format for the default registry."""
    return generate_latest(REGISTRY)
