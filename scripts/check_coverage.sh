#!/usr/bin/env bash
set -euo pipefail

uv run pytest lib/tests tests/normalize_test.py \
  --cov=contractor_lib \
  --cov-fail-under=90 \
  --cov-report=term-missing

uv run pytest api/tests \
  --cov=contractor_api \
  --cov-fail-under=90 \
  --cov-report=term-missing

uv run pytest importers/tests \
  --cov=contractor_importers \
  --cov=importers \
  --cov-fail-under=45 \
  --cov-report=term-missing
