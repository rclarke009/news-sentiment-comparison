#!/usr/bin/env python3
"""
Production smoke test for the News Sentiment Comparison API.

Hits health, sources, today, and history endpoints to verify the deployed API
is up and returning expected shapes. Use this after deploys to catch regressions
before users do.

How to use:
  From project root (with venv activated):

    python scripts/smoke_test_production.py
    python scripts/smoke_test_production.py --base-url https://your-api.onrender.com
    python scripts/smoke_test_production.py -v

  Use --base-url when your Render service has a different URL than the blueprint
  default (e.g. sentiment-lens.onrender.com). Base URL is the API origin with
  no path (no /api/v1).

When to use:
  - After pushing code and Render finishes deploying (API and/or frontend).
  - After changing env vars in Render and redeploying.
  - Periodically (e.g. from CI or a cron) to detect production outages.
  - When debugging "production works" vs "local works" — run against prod URL.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Callable

import requests

DEFAULT_BASE_URL = "https://news-sentiment-api.onrender.com"
TIMEOUT_SEC = 30


def check(
    base_url: str,
    path: str,
    expect_status: int | tuple[int, ...],
    validate: Callable[[Any], bool] | None = None,
    name: str | None = None,
    verbose: bool = False,
) -> tuple[bool, str]:
    """Request GET path, check status and optional JSON validation. Returns (ok, message)."""
    url = f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
    name = name or path
    try:
        r = requests.get(url, timeout=TIMEOUT_SEC)
    except requests.RequestException as e:
        return False, f"{name}: request failed — {e}"

    ok_status = expect_status if isinstance(expect_status, tuple) else (expect_status,)
    if r.status_code not in ok_status:
        return False, f"{name}: expected status {ok_status}, got {r.status_code}"

    if validate is None:
        return True, f"{name}: {r.status_code} OK"

    try:
        data = r.json()
    except Exception as e:
        return False, f"{name}: invalid JSON — {e}"

    if not validate(data):
        return False, f"{name}: validation failed (unexpected response shape)"

    if verbose:
        return True, f"{name}: {r.status_code} OK — {data!r}"
    return True, f"{name}: {r.status_code} OK"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test production News Sentiment API (health, sources, today, history)."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API origin, no path (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print response details on success",
    )
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    verbose = args.verbose

    print(f"Smoke testing {base}/api/v1 ...")
    results: list[tuple[bool, str]] = []

    results.append(
        check(
            base,
            "health",
            expect_status=200,
            validate=lambda d: isinstance(d.get("status"), str) and "healthy" in str(d.get("status")).lower(),
            name="health",
            verbose=verbose,
        )
    )
    results.append(
        check(
            base,
            "sources",
            expect_status=200,
            validate=lambda d: "conservative" in d and "liberal" in d,
            name="sources",
            verbose=verbose,
        )
    )
    results.append(
        check(
            base,
            "today",
            expect_status=(200, 404),
            validate=None,
            name="today",
            verbose=verbose,
        )
    )
    results.append(
        check(
            base,
            "history",
            expect_status=200,
            validate=lambda d: "comparisons" in d and "days" in d,
            name="history",
            verbose=verbose,
        )
    )

    for ok, msg in results:
        prefix = "✓" if ok else "✗"
        print(f"  {prefix} {msg}")

    failed = sum(1 for ok, _ in results if not ok)
    if failed:
        print(f"\nSmoke test failed ({failed} check(s) failed).")
        return 1
    print("\nSmoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
