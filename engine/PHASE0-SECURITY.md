# Phase 0 Security — Setup & Rollback

## What changed

1. **FastAPI** (`api.py`) — all routes except `/health` require `X-FORGE-API-Key` or `Authorization: Bearer <key>`
2. **Flask platform** — `/api/test-mode` and `/api/toggle-test-mode` require admin session
3. **Pipeline dashboard** — deprecated, localhost-only, API routes require API key when `FORGE_API_KEY` is set
4. **TradeBuilt API routes** — `/api/generate-site`, `/api/send-email`, `/api/forge/*` require Supabase session
5. **Supabase RLS** — removed permissive `USING (true)` policies (run `supabase-rls-fix.sql` if already deployed)

## Required setup

### lead-agent `.env`

```bash
# Generate: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
FORGE_API_KEY=your_key_here
FORGE_AUTH_ENABLED=true
ADMIN_PASSWORD=strong_password_here
FLASK_SECRET_KEY=another_random_string
```

### tradebuilt-saas `.env.local`

```bash
FORGE_API_KEY=same_value_as_lead_agent
FORGE_API_URL=http://localhost:8000
FORGE_ROUTE_AUTH_ENABLED=true
```

### Supabase (if project already live)

Run [`tradebuilt-saas/supabase-rls-fix.sql`](../tradebuilt-saas/supabase-rls-fix.sql) in the SQL editor.

## Key rotation (manual)

Rotate these keys if they may have been exposed:

- `FORGE_API_KEY`
- `FLASK_SECRET_KEY`
- `ADMIN_PASSWORD`
- `GMAIL_APP_PASSWORD`
- `GITHUB_TOKEN`
- `SUPABASE_SERVICE_ROLE_KEY`
- All keys in `.env` / `.env.local`

## Local debug bypass (dev only)

```bash
# lead-agent
FORGE_AUTH_ENABLED=false

# tradebuilt-saas
FORGE_ROUTE_AUTH_ENABLED=false
```

Never disable in production.

## Rollback

1. Set `FORGE_AUTH_ENABLED=false` in lead-agent `.env`
2. Set `FORGE_ROUTE_AUTH_ENABLED=false` in tradebuilt `.env.local`
3. Re-apply old RLS policies only if you understand the cross-user data leak risk

## Disable pipeline dashboard

```bash
FORGE_DASHBOARD_ENABLED=false
```