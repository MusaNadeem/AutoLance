#!/usr/bin/env bash
# Local dev backend launcher — sources .env and overrides Docker hostnames
# with localhost equivalents for running outside Docker.
set -euo pipefail
cd "$(dirname "$0")"

set -a
# shellcheck disable=SC1091
source ../.env
set +a

export DATABASE_URL="postgresql+asyncpg://autolance:secret@127.0.0.1:5433/autolance"
export REDIS_URL="redis://127.0.0.1:6379/0"
export CELERY_BROKER_URL="redis://127.0.0.1:6379/0"
export CELERY_RESULT_BACKEND="redis://127.0.0.1:6379/1"
export UPLOAD_DIR="/tmp/autolance_uploads"

mkdir -p "$UPLOAD_DIR"
exec linux_venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
