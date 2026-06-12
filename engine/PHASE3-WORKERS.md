# Phase 3 — Celery Workers & FastAPI Consolidation

## What changed

- **Celery + Redis** for scrape, agent, followup, and scheduled pipeline cycles
- **`pipeline_jobs`** table (or in-memory fallback) replaces `_jobs` dict in `api.py`
- **Stripe webhook** moved to FastAPI: `POST /webhook/stripe`
- **New endpoint**: `POST /run-pipeline` — full agent cycle via job queue
- **Flask platform** frozen — do not extend; retire in Phase 4

## Local development

### Option A — Redis only (API on host)

```bash
cd forge && docker compose up -d redis

cd engine
export REDIS_URL=redis://localhost:6379/0
export USE_CELERY=true

# Terminal 1 — API (falls back to BackgroundTasks if worker not running)
python3 api.py

# Terminal 2 — Worker
celery -A celery_app worker --loglevel=info -Q forge

# Terminal 3 — Beat (optional — 6h scheduled cycles)
celery -A celery_app beat --loglevel=info
```

### Option B — Full Docker stack

```bash
cd forge
docker compose up -d
curl http://localhost:8000/health
```

`health` reports `celery: true` when `USE_CELERY=true` and `REDIS_URL` is set.

## Railway deployment

Deploy **three services** from the same `engine/Dockerfile`, differing only by env:

| Service | `FORGE_ROLE` | Notes |
|---------|--------------|-------|
| `forge-api` | `api` | Public HTTP, port 8000 |
| `forge-worker` | `worker` | No public port |
| `forge-beat` | `beat` | Single instance only |

Shared env on all services:

```
REDIS_URL=redis://<railway-redis>:6379/0
USE_CELERY=true
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
STORAGE_BACKEND=postgres
FORGE_API_KEY=...
```

Point Stripe webhook to: `https://<forge-api>/webhook/stripe`

## Job API

| Endpoint | Job type |
|----------|----------|
| `POST /scrape` | `scrape` |
| `POST /run-agent` | `agent` |
| `POST /followup` | `followup` |
| `POST /run-pipeline` | `pipeline_cycle` |
| `GET /jobs/{id}` | status |
| `GET /jobs` | list recent |

## Fallback behavior

- `USE_CELERY=false` → FastAPI `BackgroundTasks` (no Redis required)
- Celery enqueue failure → automatic fallback to `BackgroundTasks`
- Supabase not configured → jobs stored in memory (dev only)