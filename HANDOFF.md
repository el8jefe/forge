# FORGE Migration Hand-Off

**Date:** June 12, 2026  
**Repo:** `/Users/pablorincon/forge`  
**Branch:** `main`  
**Status:** Phases 0–5 complete

---

## Executive summary

FORGE was migrated from a split MVP (`lead-agent` Python pipeline + `tradebuilt-saas` Next.js UI + legacy Flask platform) into a unified monorepo. The active stack is:

| Layer | Technology | Location |
|-------|------------|----------|
| Frontend | Next.js 16 | `web/` |
| API | FastAPI v3.4 | `engine/api.py` |
| Workers | Celery + Redis | `engine/celery_app.py`, `tasks/` |
| Database | Supabase Postgres (optional) | `supabase/migrations/` |
| Email | Resend (prod) / Gmail (dev) | `engine/mail/sender.py` |
| CI | GitHub Actions | `.github/workflows/ci.yml` |

The legacy Flask SaaS is archived at `engine/_archive/platform/` and must not be deployed.

---

## Git history (all phase commits)

| Commit | Phase | Summary |
|--------|-------|---------|
| `2eae2b6` | 1 | Monorepo foundation cleanup |
| `1671bb2` | 2 | Postgres storage layer with CSV rollback |
| `c2ae1c6` | 3 | Celery workers, persistent jobs, FastAPI consolidation |
| `179cca0` | 4 | Next.js-only UI, canonical site_builder generator |
| `73c229a` | 5 | Production hardening — Resend email, CI, Flask archive |

**Note:** Phase 0 (security) was implemented as part of the initial monorepo import (`PHASE0-SECURITY.md`); it predates the numbered phase commits.

**Remote:** No GitHub remote is configured on this repo yet. CI will not run until a remote is added and `main` is pushed.

---

## Phase 0 — Emergency security

**Doc:** `engine/PHASE0-SECURITY.md`

### Changes

1. **FastAPI auth** — all routes except `/health` require `X-FORGE-API-Key` or `Authorization: Bearer <key>` (`api_auth.py`)
2. **Flask platform** — test-mode API routes require admin session
3. **Pipeline dashboard** — deprecated, localhost-only
4. **TradeBuilt API routes** — `/api/generate-site`, `/api/send-email`, `/api/forge/*` require Supabase session
5. **Supabase RLS** — removed permissive `USING (true)` policies (`supabase/migrations/002_rls_fix.sql`)

### Key env vars

```
FORGE_API_KEY=...
FORGE_AUTH_ENABLED=true
FORGE_ROUTE_AUTH_ENABLED=true   # web/.env.local
```

---

## Phase 1 — Monorepo + foundation

**Commit:** `2eae2b6`

### Changes

- Created `forge/` monorepo combining `engine/` (Python) and `web/` (Next.js)
- Pinned `engine/requirements.txt` (fastapi, uvicorn, bs4, celery, redis, structlog)
- Centralized config via `pydantic-settings` in `engine/config.py`
- Structured JSON logging to stdout (`system_logger.py`; `system_log.txt` preserved)
- Fixed `api.py` `send_batch` `demo_urls` signature bug
- Marked `dashboard.py`, `whitelabel.py`, and Flask `platform/` as legacy
- Added `docs/ARCHITECTURE.md`, `docker-compose.yml`, `railway.toml`
- Added Supabase migrations `001_initial.sql`, `002_rls_fix.sql`
- Imported full web app (auth, dashboard, generate, billing, booking, stripe, forge proxy routes)

### New / key files

```
forge/
├── README.md
├── docker-compose.yml
├── docs/ARCHITECTURE.md
├── engine/          (full pipeline from lead-agent)
├── web/             (full SaaS from tradebuilt-saas)
└── supabase/migrations/
```

---

## Phase 2 — Postgres storage layer

**Commit:** `1671bb2`  
**Doc:** `docs/ARCHITECTURE.md` (Phase 2 section)

### Changes

- Added `STORAGE_BACKEND` flag (`csv` default, `postgres` for Supabase)
- Storage facade: `engine/storage/` (`leads_storage`, `outreach_storage`, `counters_storage`)
- Repositories: `engine/repositories/` (PostgREST client, lead mapper, upserts on `dedup_key`)
- Migration `003_phase2_pipeline.sql` — pipeline columns, `email_send_counters`, `pipeline_jobs`
- Wired `agent.py`, `scraper.py`, `emailer.py`, `api.py`, `db.py` through storage layer
- CSV import script: `engine/scripts/import_csv.py`
- Unit tests: `engine/tests/test_lead_mapper.py`

### Key env vars

```
STORAGE_BACKEND=csv          # or postgres
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
```

### Postgres activation (ops — not yet run in prod)

1. Run migrations `001`, `002`, `003` in Supabase SQL editor
2. Set `STORAGE_BACKEND=postgres` in `engine/.env`
3. Run `python3 scripts/import_csv.py`
4. Verify: `curl localhost:8000/health` → `"storage": "postgres"`

---

## Phase 3 — Celery workers + FastAPI consolidation

**Commit:** `c2ae1c6`  
**Doc:** `engine/PHASE3-WORKERS.md`

### Changes

- **Celery + Redis** for scrape, agent, followup, and scheduled pipeline cycles
- **`pipeline_jobs`** persistence via `repositories/jobs_repo.py` (replaces in-memory `_jobs` dict)
- **`job_dispatcher.py`** — Celery with automatic `BackgroundTasks` fallback
- **`pipeline_runners.py`** — shared execution logic for workers and fallback
- **Stripe webhook** on FastAPI: `POST /webhook/stripe` (`routes/stripe.py`)
- **New endpoint:** `POST /run-pipeline` — full agent cycle via job queue
- **Docker Compose** — api / worker / beat services + Redis
- **Railway** — multi-service deploy via `FORGE_ROLE` (`api` / `worker` / `beat`)
- Flask platform marked frozen (not extended)
- Tests: `engine/tests/test_jobs_repo.py`

### Job API

| Endpoint | Job type |
|----------|----------|
| `POST /scrape` | `scrape` |
| `POST /run-agent` | `agent` |
| `POST /followup` | `followup` |
| `POST /run-pipeline` | `pipeline_cycle` |
| `GET /jobs/{id}` | status |
| `GET /jobs` | list recent |

### Key env vars

```
REDIS_URL=redis://localhost:6379/0
USE_CELERY=true
FORGE_ROLE=api              # api | worker | beat
```

---

## Phase 4 — Next.js-only UI

**Commit:** `179cca0`  
**Doc:** `engine/PHASE4-UI.md`

### Changes

- **Canonical site generator:** `POST /build-site` on FastAPI wraps `site_builder.py` (`routes/build.py`)
- **TradeBuilt** `/api/generate-site` proxies to FORGE — removed duplicate `web/services/template.ts` and `web/services/generator.ts`
- **Admin UI:** `web/app/admin` — pipeline ops (replaces Flask `/admin`)
- **New forge proxy routes:** `/api/forge/health`, `/api/forge/jobs/list`, `/api/forge/run-agent`, `/api/forge/run-pipeline`
- **Flask retired:** `run.py` exits with instructions; `platform/RETIRED.md` added
- Updated `web/lib/forge-client.ts`, dashboard, generate pages

### Route map

| User-facing | Backend |
|-------------|---------|
| `/generate` | `POST /api/generate-site` → `POST /build-site` |
| `/admin` | `POST /api/forge/*` → FastAPI |
| `/dashboard` | Supabase CRM |
| Stripe | `web/app/api/stripe/*` + FastAPI `/webhook/stripe` |

---

## Phase 5 — Production hardening

**Commit:** `73c229a`  
**Doc:** `engine/PHASE5-PRODUCTION.md`

### Changes

#### Production email
- **`engine/mail/sender.py`** — unified Resend (HTTP) + Gmail SMTP fallback
- **`engine/config.py`** — `EMAIL_PROVIDER`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`
- **`engine/emailer.py`** — outreach uses `mail.sender.send_message`
- **`engine/followup.py`** — rewritten; `run_followup()` returns count (fixes Celery bug where `pipeline_runners` expected `run_followup` but only `main()` existed)

#### Postgres wiring (carryover from Phase 2)
- **`engine/scraper.py`** — `load_existing_leads()` uses `leads_repo` when `use_postgres()`
- **`engine/repositories/outreach_repo.py`** — `followed_business_names()`, `list_followup_candidates(days=3)`

#### Stripe (no Flask dependency)
- **`engine/integrations/stripe_conversions.py`** — `process_stripe_webhook`, `handle_conversion` extracted from legacy Flask
- **`engine/routes/stripe.py`** — imports from `integrations.stripe_conversions` (not `platform.stripe_handler`)

#### Flask archive
- **`engine/platform/`** → **`engine/_archive/platform/`**
- **`engine/_archive/README.md`** — archive index
- **`engine/run.py`** — exits with pointer to `_archive`
- **`engine/requirements.txt`** — Flask deps removed; `structlog` added (not yet wired into logger)

#### CI & tests
- **`.github/workflows/ci.yml`** — engine `unittest discover` + web `npm ci && npm run build`
- **New tests:**
  - `engine/tests/test_mail_sender.py`
  - `engine/tests/test_job_dispatcher.py`
  - `engine/tests/test_stripe_webhook.py`
- **17 engine tests passing** locally; **web build passing**

#### Health endpoint (v3.4)
`GET /health` now returns:
```json
{
  "status": "ok",
  "version": "3.4",
  "storage": "csv|postgres",
  "email": "resend|gmail|none",
  "celery": true
}
```

#### Docs / env
- **`engine/PHASE5-PRODUCTION.md`** — production runbook
- **`engine/.env.example`** — Resend vars added, Flask block removed
- **`docs/ARCHITECTURE.md`** — updated for Phase 5

---

## This session — additional changes

Beyond the Phase 5 commit, these edits were made in the final session:

1. **Committed Phase 5** — all uncommitted work staged and committed as `73c229a`
2. **Doc path fixes:**
   - `engine/_archive/platform/RETIRED.md` — removed circular "MOVED" header; updated archive paths
   - `engine/PHASE4-UI.md` — `platform/RETIRED.md` → `_archive/platform/RETIRED.md`
   - `docs/ARCHITECTURE.md` — same path correction in Phase 4 changelog
3. **Verification run:**
   - `python3 -m unittest discover -s tests -v` → 17 tests OK
   - `npm run build` → success
4. **Created this hand-off document** (`HANDOFF.md`)

---

## Current architecture

```
forge/
├── engine/                    Python pipeline + FastAPI API
│   ├── api.py                 HTTP API (v3.4)
│   ├── agent.py               Pipeline orchestration
│   ├── scraper.py             Lead discovery
│   ├── site_builder.py        Demo site generation
│   ├── emailer.py             Outreach + warmup
│   ├── followup.py            3-day follow-up sender
│   ├── celery_app.py          Worker config
│   ├── job_dispatcher.py      Celery / BackgroundTasks dispatch
│   ├── pipeline_runners.py    Shared worker logic
│   ├── mail/sender.py         Resend + Gmail
│   ├── integrations/          Stripe conversions
│   ├── storage/               CSV ↔ Postgres facade
│   ├── repositories/          PostgREST data access
│   ├── routes/                build.py, stripe.py
│   ├── tasks/                 Celery task definitions
│   ├── tests/                 17 unit tests
│   └── _archive/platform/     Retired Flask (reference only)
├── web/                       Next.js 16 SaaS UI
│   ├── app/admin/             Pipeline ops
│   ├── app/generate/          Site generation
│   ├── app/dashboard/         CRM
│   └── app/api/forge/*        BFF proxy to engine
├── supabase/migrations/       001, 002, 003
├── docs/ARCHITECTURE.md
└── .github/workflows/ci.yml
```

---

## How to run locally

```bash
# Redis (optional — needed for Celery)
cd forge && docker compose up -d redis

# Engine API
cd forge/engine
pip install -r requirements.txt
python3 api.py                    # http://localhost:8000

# Celery worker (optional)
celery -A celery_app worker --loglevel=info -Q forge

# Web
cd forge/web
npm install && npm run dev        # http://localhost:3000

# Health check
curl http://localhost:8000/health
```

---

## Environment variables (quick reference)

### Engine (`engine/.env`)

| Variable | Purpose | Default |
|----------|---------|---------|
| `FORGE_API_KEY` | API authentication | required in prod |
| `FORGE_AUTH_ENABLED` | Enable API key check | `true` |
| `STORAGE_BACKEND` | `csv` or `postgres` | `csv` |
| `SUPABASE_URL` | Postgres via PostgREST | — |
| `SUPABASE_SERVICE_KEY` | Service role key | — |
| `REDIS_URL` | Celery broker | `redis://localhost:6379/0` |
| `USE_CELERY` | Enable worker queue | `true` |
| `EMAIL_PROVIDER` | `auto`, `resend`, `gmail` | `auto` |
| `RESEND_API_KEY` | Production email | — |
| `RESEND_FROM_EMAIL` | Sender address | — |
| `GMAIL_SENDER` | Dev email fallback | — |
| `GMAIL_APP_PASSWORD` | Dev email fallback | — |
| `STRIPE_SECRET_KEY` | Stripe API | — |
| `STRIPE_WEBHOOK_SECRET` | Webhook verification | — |
| `TEST_MODE` | Route emails to test inbox | `true` |

### Web (`web/.env.local`)

| Variable | Purpose |
|----------|---------|
| `FORGE_API_URL` | Engine API URL (`http://localhost:8000`) |
| `FORGE_API_KEY` | Same key as engine |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side Supabase access |

Templates: `engine/.env.example`, `web/.env.local.example`

---

## Verification checklist

| Check | Command | Expected |
|-------|---------|----------|
| Engine tests | `cd engine && python3 -m unittest discover -s tests -v` | 17 tests OK |
| Web build | `cd web && npm run build` | Compiled successfully |
| Health | `curl localhost:8000/health` | `version: 3.4`, `email`, `storage`, `celery` |
| Flask retired | `cd engine && python3 run.py` | Exit 1 with instructions |
| CI | Push to GitHub `main` | Engine + web jobs green |

---

## Outstanding ops (not automated)

These require your credentials and manual steps:

1. **Add GitHub remote** and push `main` to trigger CI
2. **Resend production email** — set `RESEND_API_KEY` + `RESEND_FROM_EMAIL` in `engine/.env`
3. **Activate Postgres** — run migrations, set `STORAGE_BACKEND=postgres`, import CSV
4. **Railway deploy** — three services (api, worker, beat) per `PHASE3-WORKERS.md`
5. **Stripe webhook** — point to `https://<forge-api>/webhook/stripe`
6. **Key rotation** — if any keys were exposed; see `PHASE0-SECURITY.md`

---

## Known gaps / tech debt

| Item | Status | Notes |
|------|--------|-------|
| Stripe `handle_conversion` | CSV only | Still writes `leads.csv` / `conversions.csv`; not wired to Postgres `leads_repo` |
| `structlog` | In requirements, not wired | `system_logger.py` still uses stdlib JSON logging |
| Integration tests | None | No live Supabase/Resend test suite |
| Engine lint/typecheck | Not in CI | Only unittest + web build |
| Legacy docs | Partially stale | `SYSTEM_README.md`, `CHECKPOINT.md` still reference old `platform/` paths |
| Postgres in prod | Not activated | `STORAGE_BACKEND` still defaults to `csv` |

---

## Deprecated — do not extend

- `engine/_archive/platform/` — retired Flask SaaS
- `engine/dashboard.py` — superseded by `web/app/admin`
- `engine/pipeline_dashboard.py` — local dev only
- `engine/run.py` — exits immediately
- `web/services/template.ts` + `generator.ts` — deleted Phase 4

---

## Phase-specific runbooks

| Phase | Doc |
|-------|-----|
| 0 Security | `engine/PHASE0-SECURITY.md` |
| 3 Workers | `engine/PHASE3-WORKERS.md` |
| 4 UI | `engine/PHASE4-UI.md` |
| 5 Production | `engine/PHASE5-PRODUCTION.md` |
| Architecture | `docs/ARCHITECTURE.md` |

---

## Suggested next steps

1. Add GitHub remote, push `main`, confirm CI green
2. Set Resend credentials and verify `"email": "resend"` on `/health`
3. Run Supabase migrations and flip `STORAGE_BACKEND=postgres`
4. Wire Stripe `handle_conversion` to `leads_repo` when on Postgres
5. Deploy Railway api + worker + beat services