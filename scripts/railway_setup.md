# Railway setup (manual — requires `railway login`)

Run once when back at keyboard:

```bash
npm install -g @railway/cli
railway login
cd /path/to/forge
railway init --name forge
```

## Add Redis

Railway dashboard → **New** → **Database** → **Redis** → copy `REDIS_URL`

## Create 3 services from `engine/Dockerfile`

| Service | `FORGE_ROLE` | Public URL |
|---------|--------------|------------|
| forge-api | `api` | Yes (port 8000) |
| forge-worker | `worker` | No |
| forge-beat | `beat` | No (max 1 instance) |

## Shared variables (all 3 services)

Copy from `engine/.env` / `docs/PRODUCTION-LAUNCH.md`:

- `FORGE_API_KEY` (must match Vercel)
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
- `STORAGE_BACKEND=postgres`
- `TEST_MODE=false`
- `USE_CELERY=true`
- `REDIS_URL`
- `RESEND_API_KEY`, `RESEND_FROM_EMAIL`
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- `GOOGLE_PLACES_API_KEY`
- `FORGE_CORS_ORIGINS=https://tradebuilt-saas.vercel.app`
- `FORGE_DASHBOARD_ENABLED=false`

## After API is live

```bash
cd forge/web
printf '%s' 'https://YOUR-RAILWAY-API.up.railway.app' | vercel env add FORGE_API_URL production --force
vercel --prod
```

Stripe conversion webhook → `https://YOUR-RAILWAY-API.up.railway.app/webhook/stripe`