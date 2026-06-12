# FORGE Architecture

Last updated: Phase 4 (Next.js-only UI)

## Overview

FORGE is an AI business automation platform: lead discovery, website analysis, demo site generation, and outreach. The codebase is a monorepo migrating from a split MVP to a production SaaS stack.

```
forge/
├── engine/          Python pipeline + API (from lead-agent)
├── web/             Next.js SaaS UI (from tradebuilt-saas)
├── supabase/        PostgreSQL migrations
└── docs/            Architecture and runbooks
```

## Current state (Phase 4)

| Layer | Technology | Status |
|-------|------------|--------|
| Frontend | Next.js 16 (`web/`) | Active — sole UI (`/generate`, `/admin`, `/dashboard`) |
| API | FastAPI (`engine/api.py`) | Active — auth, Stripe, `POST /build-site` |
| Legacy platform | Flask (`engine/platform/`) | Retired — `run.py` exits; see `RETIRED.md` |
| Pipeline scheduler | Celery beat + `agent.py` | Beat @ 00/06/12/18 UTC |
| Database | Supabase Postgres | `STORAGE_BACKEND=csv\|postgres` |
| Jobs | Celery + `pipeline_jobs` | Redis broker, in-memory fallback |
| Email | Gmail SMTP | Dev only — Resend in Phase 5 |

## Target state (post-migration)

```
web (Vercel)  →  FastAPI (Railway)  →  Supabase Postgres
                      ↓
               Celery workers + Redis
                      ↓
         Scout → Analyst → Scorer → Designer → Sales → Followup
```

## Engine modules

| Module | Responsibility | Data |
|--------|----------------|------|
| `scraper.py` | Google Places discovery + scoring | `storage/leads_storage` |
| `site_builder.py` | Demo HTML + deploy | `sites/`, GitHub Pages |
| `logo_generator.py` | Trade SVG logos/icons | — |
| `emailer.py` | Outreach + warmup | `storage/counters_storage` |
| `agent.py` | Pipeline orchestration | storage layer |
| `api.py` | HTTP API for web app | Celery dispatch + `pipeline_jobs` |
| `celery_app.py` | Worker configuration | Redis |
| `tasks/pipeline.py` | Async job definitions | Celery |
| `job_dispatcher.py` | Celery or BackgroundTasks | Redis fallback |
| `platform/` | Legacy Flask SaaS | CSV, JSON (legacy) |
| `db.py` | Supabase REST client | `repositories/` |
| `storage/` | CSV ↔ Postgres facade | `STORAGE_BACKEND` |
| `repositories/` | PostgREST data access | Supabase |

## Web modules

| Path | Responsibility |
|------|----------------|
| `app/api/forge/*` | BFF proxy to engine API (auth required) |
| `app/api/generate-site` | Proxies to FORGE `POST /build-site` (site_builder.py) |
| `app/admin` | Pipeline ops — scrape, agent, run-pipeline |
| `app/api/send-email` | Outreach (auth required) |
| `app/dashboard` | CRM UI |
| `lib/crm.ts` | Supabase lead store |

## Authentication

| Surface | Method |
|---------|--------|
| FastAPI | `X-FORGE-API-Key` or `Bearer` token |
| TradeBuilt API | Supabase JWT in `Authorization` header |
| Web admin (`/admin`) | Supabase JWT (same as other routes) |

See `engine/PHASE0-SECURITY.md` for setup.

## Deprecated (do not extend)

- `engine/platform/whitelabel.py` — white-label reseller
- `engine/pipeline_dashboard.py` — local dev dashboard only
- `engine/dashboard.py` — superseded by admin portal
- `web/services/template.ts` + `generator.ts` — removed Phase 4 (use `site_builder.py`)

## Configuration

All engine settings: `engine/config.py` (`Settings` via pydantic-settings).

Key Phase 2 variable:

| Variable | Values | Default |
|----------|--------|---------|
| `STORAGE_BACKEND` | `csv` \| `postgres` | `csv` |

When `postgres`: set `SUPABASE_URL` + `SUPABASE_SERVICE_KEY`, run migration `003_phase2_pipeline.sql`, then import existing CSV data with `python scripts/import_csv.py`.

Phase 3 variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `REDIS_URL` | Celery broker | `redis://localhost:6379/0` |
| `USE_CELERY` | Enable worker queue | `true` |
| `FORGE_ROLE` | `api` / `worker` / `beat` | `api` |

See `engine/PHASE3-WORKERS.md` for Railway multi-service setup.

Environment templates:
- `engine/.env.example`
- `web/.env.local.example`

## Local development

```bash
# Terminal 1 — Redis + workers (or redis only)
cd forge && docker compose up -d redis
# Full stack: docker compose up -d

# Terminal 2 — Engine API
cd forge/engine
pip install -r requirements.txt
python api.py

# Terminal 3 — Web
cd forge/web
npm install
npm run dev

# Terminal 4 — Pipeline (optional)
cd forge/engine
python agent.py --once
```

## Migration phases

| Phase | Focus | Status |
|-------|-------|--------|
| 0 | Emergency security | Done |
| 1 | Monorepo + foundation | Done |
| 2 | Postgres as sole source of truth | Done |
| 3 | FastAPI + Celery, retire Flask | Done |
| 4 | Next.js only UI | Done |
| 5 | Production email, tests, CI | Pending |

## Changelog

### Phase 4
- `POST /build-site` on FastAPI — canonical `site_builder.py` generator
- TradeBuilt `/api/generate-site` proxies to FORGE; removed `template.ts` + `generator.ts`
- `web/app/admin` — pipeline operations UI (replaces Flask admin)
- Flask platform retired (`run.py` exits, `platform/RETIRED.md`)
- See `engine/PHASE4-UI.md`

### Phase 3
- Celery app + Redis broker (`celery_app.py`, `tasks/pipeline.py`)
- Job persistence via `pipeline_jobs` (`repositories/jobs_repo.py`)
- `job_dispatcher.py` — Celery with BackgroundTasks fallback
- Stripe webhook on FastAPI (`POST /webhook/stripe`)
- `POST /run-pipeline` endpoint; Docker Compose api/worker/beat services
- Flask platform marked frozen; see `engine/PHASE3-WORKERS.md`

### Phase 2
- Added `STORAGE_BACKEND` flag (`csv` default, `postgres` for Supabase)
- Storage facade: `engine/storage/` (leads, outreach, counters)
- Repositories: `engine/repositories/` (PostgREST client, lead mapper, upserts on `dedup_key`)
- Migration `003_phase2_pipeline.sql` (pipeline columns, `email_send_counters`, `pipeline_jobs`)
- Wired `agent.py`, `scraper.py`, `emailer.py`, `api.py`, `db.py` through storage layer
- CSV import script: `engine/scripts/import_csv.py`
- Unit tests: `engine/tests/test_lead_mapper.py`

### Phase 1
- Created `forge/` monorepo (`engine/` + `web/`)
- Pinned `requirements.txt` (fastapi, uvicorn, bs4, celery, redis, structlog)
- Centralized config via pydantic-settings
- Structured JSON logging to stdout (preserves `system_log.txt`; structlog deferred until `platform/` rename)
- Fixed `api.py` `send_batch` signature bug
- Marked whitelabel + Flask platform as legacy