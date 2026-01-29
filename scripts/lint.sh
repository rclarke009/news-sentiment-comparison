#!/usr/bin/env bash
# Run the same lint checks as GitLab CI (black + ruff).
# Usage: ./scripts/lint.sh   or from repo root: scripts/lint.sh

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Running code formatting check (black)..."
black --check news_sentiment/ scripts/

echo "Running linting (ruff)..."
ruff check news_sentiment/ scripts/

echo "Lint passed."
