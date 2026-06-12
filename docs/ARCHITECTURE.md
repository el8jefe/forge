# FORGE Architecture

Last updated: Phase 1 (foundation cleanup)

## Overview

FORGE is an AI business automation platform: lead discovery, website analysis, demo site generation, and outreach. The codebase is a monorepo migrating from a split MVP to a production SaaS stack.

```
forge/
├── engine/          Python pipeline + API (from lead-agent)
├── web/             Next.js SaaS UI (from tradebuilt-saas)
├── supabase/        PostgreSQL migrations
└── docs/            Architecture and runbooks
```

## Current state (Phase 1)

| Layer | Technology | Status |
|-------|------------|--------|
| Frontend | Next.js 16 (`web/`) | Active — TradeBuilt UI |
| API | FastAPI (`engine/api.py`) | Active — auth required |
| Legacy platform | Flask (`engine/platform/`) | Deprecated — admin/Stripe only |
| Pipeline scheduler | `agent.py` + `schedule` | Active — CSV-backed |
| Database | Supabase Postgres | Partial — `db.py` + CSV fallback |
| Jobs | In-process BackgroundTasks | Fragile — Celery in Phase 3 |
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
| `scraper.py` | Google Places discovery + scoring | CSV / Supabase |
| `site_builder.py` | Demo HTML + deploy | `sites/`, GitHub Pages |
| `logo_generator.py` | Trade SVG logos/icons | — |
| `emailer.py` | Outreach + warmup | JSON logs, CSV |
| `agent.py` | Pipeline orchestration | CSV |
| `api.py` | HTTP API for web app | Supabase, jobs dict |
| `platform/` | Legacy Flask SaaS | CSV, JSON |
| `db.py` | Supabase REST client | Postgres |

## Web modules

| Path | Responsibility |
|------|----------------|
| `app/api/forge/*` | BFF proxy to engine API (auth required) |
| `app/api/generate-site` | Site generation (auth required) |
| `app/api/send-email` | Outreach (auth required) |
| `app/dashboard` | CRM UI |
| `lib/crm.ts` | Supabase lead store |

## Authentication

| Surface | Method |
|---------|--------|
| FastAPI | `X-FORGE-API-Key` or `Bearer` token |
| TradeBuilt API | Supabase JWT in `Authorization` header |
| Flask admin | Session + `ADMIN_PASSWORD` |

See `engine/PHASE0-SECURITY.md` for setup.

## Deprecated (do not extend)

- `engine/platform/whitelabel.py` — white-label reseller
- `engine/pipeline_dashboard.py` — local dev dashboard only
- `engine/dashboard.py` — superseded by admin portal
- `web/services/template.ts` + `generator.ts` — duplicate generator (remove Phase 4)

## Configuration

All engine settings: `engine/config.py` (`Settings` via pydantic-settings).

Environment templates:
- `engine/.env.example`
- `web/.env.local.example`

## Local development

```bash
# Terminal 1 — Redis (optional, for Phase 3 prep)
cd forge && docker compose up -d redis

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
| 2 | Postgres as sole source of truth | Pending |
| 3 | FastAPI + Celery, retire Flask | Pending |
| 4 | Next.js only UI | Pending |
| 5 | Production email, tests, CI | Pending |

## Changelog

### Phase 1
- Created `forge/` monorepo (`engine/` + `web/`)
- Pinned `requirements.txt` (fastapi, uvicorn, bs4, celery, redis, structlog)
- Centralized config via pydantic-settings
- Structured JSON logging to stdout (preserves `system_log.txt`; structlog deferred until `platform/` rename)
- Fixed `api.py` `send_batch` signature bug
- Marked whitelabel + Flask platform as legacy