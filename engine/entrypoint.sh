#!/bin/sh
set -e

ROLE="${FORGE_ROLE:-api}"
PORT="${FORGE_API_PORT:-8000}"

case "$ROLE" in
  worker)
    echo "[FORGE] Starting Celery worker..."
    exec celery -A celery_app worker --loglevel=info -Q forge
    ;;
  beat)
    echo "[FORGE] Starting Celery beat..."
    exec celery -A celery_app beat --loglevel=info
    ;;
  *)
    echo "[FORGE] Starting FastAPI on port $PORT..."
    exec uvicorn api:app --host 0.0.0.0 --port "$PORT"
    ;;
esac