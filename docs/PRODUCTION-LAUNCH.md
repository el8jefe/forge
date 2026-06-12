# FORGE Production Launch Runbook

**Repo:** https://github.com/el8jefe/forge  
**Phase A code fixes:** committed on `main` (CRM `user_id`, admin guard, Postgres stripe/bounce, `TEST_MODE=false` default)

---

## Critical: Supabase project must exist first

Your env files reference:

```
https://iixtlxrwisdxloviamg.supabase.co
```

That hostname currently returns **NXDOMAIN** (project deleted, never created, or wrong ref). **CRM, auth, and Postgres storage will not work until this is fixed.**

### Fix Supabase (15 minutes)

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. **Create a new project** (or open the correct existing one)
3. Copy from **Settings → API**:
   - Project URL → `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL`
   - `anon` key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_KEY` / `SUPABASE_SERVICE_ROLE_KEY`
4. Run migrations (see [Run migrations](#run-migrations) below)
5. Update env files and redeploy Vercel + Railway

---

## Architecture (production)

```
Vercel (web/)  ──FORGE_API_KEY──►  Railway forge-api (engine/)
       │                                    │
       │                                    ├── Redis
       └── Supabase JWT ──► Supabase ◄────┘ (service role)
Stripe Pro webhook ──► Vercel /api/stripe/webhook
Stripe conversions ──► Railway /webhook/stripe
```

---

## 1. GitHub (done)

- Remote: `git@github.com:el8jefe/forge.git`
- Branch: `main`
- CI: engine tests + web build (green)

---

## 2. Run migrations

After Supabase project exists:

```bash
cd forge
./scripts/run_supabase_migrations.sh
```

Or paste into Supabase SQL editor in order:

1. `supabase/migrations/001_initial.sql`
2. `supabase/migrations/002_rls_fix.sql`
3. `supabase/migrations/003_phase2_pipeline.sql`

Then import pipeline CSV data:

```bash
cd engine
# Set STORAGE_BACKEND=postgres + SUPABASE_* in .env first
python3 scripts/import_csv.py
```

---

## 3. Generate shared API key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set the **same value** as `FORGE_API_KEY` on Railway (all services) and Vercel.

---

## 4. Admin access

1. Sign up / log in at your Vercel app
2. Supabase dashboard → **Authentication → Users** → copy your user **UUID**
3. Set on Vercel (and `web/.env.local`):

```
FORGE_ADMIN_USER_IDS=<your-uuid>
```

Without this, `/admin` returns 403.

---

## 5. Railway (engine)

Login once (requires browser):

```bash
railway login
```

### Create project + services

```bash
cd forge
railway init --name forge

# Add Redis plugin in Railway dashboard, copy REDIS_URL

# Service 1: API
railway up --service forge-api
# Set in Railway dashboard → forge-api → Variables:
#   FORGE_ROLE=api
#   REDIS_URL=redis://...
#   USE_CELERY=true
#   STORAGE_BACKEND=postgres
#   SUPABASE_URL=...
#   SUPABASE_SERVICE_KEY=...
#   FORGE_API_KEY=...
#   TEST_MODE=false
#   RESEND_API_KEY=...
#   RESEND_FROM_EMAIL=...
#   FORGE_CORS_ORIGINS=https://tradebuilt-saas.vercel.app
#   FORGE_DASHBOARD_ENABLED=false

# Service 2: Worker (same Dockerfile, new service)
#   FORGE_ROLE=worker
#   (same shared vars as API)

# Service 3: Beat (scale to exactly 1 instance)
#   FORGE_ROLE=beat
```

Health check: `https://<forge-api-url>/health`  
Expect: `"storage":"postgres"`, `"email":"resend"`, `"celery":true`

Point Stripe **conversion** webhook to: `https://<forge-api>/webhook/stripe`

---

## 6. Vercel (web)

Linked project: `tradebuilt-saas` → https://tradebuilt-saas.vercel.app

Set production env vars (Vercel dashboard or CLI):

| Variable | Source |
|----------|--------|
| `FORGE_API_KEY` | same as Railway |
| `FORGE_API_URL` | Railway API public URL |
| `FORGE_ROUTE_AUTH_ENABLED` | `true` |
| `FORGE_ADMIN_USER_IDS` | your Supabase user UUID |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role |
| `RESEND_API_KEY` | resend.com |
| `RESEND_FROM_EMAIL` | verified domain |
| `STRIPE_*` | Stripe dashboard (live when ready) |

Deploy:

```bash
cd forge/web
vercel --prod
```

Point Stripe **Pro subscription** webhook to: `https://tradebuilt-saas.vercel.app/api/stripe/webhook`

---

## 7. Smoke tests

- [ ] `curl https://<railway-api>/health` → postgres, resend, celery
- [ ] Sign up → `/generate` → lead in dashboard (has `user_id`)
- [ ] Admin user → `/admin` → scrape job completes
- [ ] `/api/send-email` sends via Resend
- [ ] Stripe test checkout → `user_profiles.plan = pro`

---

## 8. Rollback

- Vercel: redeploy previous deployment in dashboard
- Railway: revert env `STORAGE_BACKEND=csv` only if Postgres broken (not recommended)
- Supabase: do not drop tables without backup

---

## Phase A code changes (already merged)

| Fix | File(s) |
|-----|---------|
| CRM `user_id` | `web/lib/crm.ts` |
| Admin guard | `web/lib/api-guard.ts`, `web/app/api/forge/*` |
| Stripe → Postgres | `engine/integrations/stripe_conversions.py`, `leads_repo.py` |
| Bounce → Postgres | `engine/emailer.py` |
| `TEST_MODE=false` default | `engine/config.py` |
| Hide OpenAPI | `engine/api_auth.py`, `engine/api.py` |