#!/usr/bin/env bash
# Local dev Celery worker launcher — sources .env and overrides Docker
# hostnames with localhost equivalents for running outside Docker.
cd "$(dirname "$0")"

set -a
# shellcheck disable=SC1091
source ../.env
set +a

export DATABASE_URL="postgresql+asyncpg://freelanceradar:secret@127.0.0.1:5433/freelanceradar"
export REDIS_URL="redis://127.0.0.1:6379/0"
export CELERY_BROKER_URL="redis://127.0.0.1:6379/0"
export CELERY_RESULT_BACKEND="redis://127.0.0.1:6379/1"
export UPLOAD_DIR="/tmp/autolance_uploads"

exec linux_venv/bin/celery -A app.workers.celery_app worker \
    --concurrency=2 -Q default,scraping,matching,alerts --loglevel=info
