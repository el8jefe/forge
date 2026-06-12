# Phase 4 — Next.js Only UI

## What changed

- **Canonical generator**: `POST /build-site` on FastAPI wraps `site_builder.py`
- **TradeBuilt** `/api/generate-site` proxies to FORGE — removed `template.ts` and `generator.ts`
- **Admin UI**: `web/app/admin` — pipeline ops (replaces Flask `/admin`)
- **Flask retired**: `python3 run.py` exits with instructions; see `platform/RETIRED.md`

## Routes

| User-facing | Backend |
|-------------|---------|
| `/generate` | `POST /api/generate-site` → `POST /build-site` |
| `/admin` | `POST /api/forge/*` → FastAPI |
| `/dashboard` | Supabase CRM |
| Stripe | `web/app/api/stripe/*` + FastAPI `/webhook/stripe` |

## Required env (web)

```
FORGE_API_URL=http://localhost:8000
FORGE_API_KEY=<same as engine>
```

## Required env (engine)

Unchanged from Phase 3. Site builder may use `GITHUB_TOKEN`, `UNSPLASH_ACCESS_KEY` for deploy/HOT tiers.