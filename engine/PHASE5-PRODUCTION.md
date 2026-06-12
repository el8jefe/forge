# Phase 5 — Production Hardening

## Email (Resend)

Engine pipeline (`emailer.py`, `followup.py`) uses `mail/sender.py`:

| Priority | Provider | Env |
|----------|----------|-----|
| 1 | **Resend** (production) | `RESEND_API_KEY`, `RESEND_FROM_EMAIL` |
| 2 | Gmail SMTP (dev) | `GMAIL_SENDER`, `GMAIL_APP_PASSWORD` |

Set `EMAIL_PROVIDER=resend|gmail|auto` (default: `auto`).

Web app (`web/services/emailer.ts`) already uses Resend for dashboard outreach.

## Postgres activation

1. Run migrations `001`, `002`, `003` in Supabase SQL editor
2. Set in `engine/.env`:
   ```
   SUPABASE_URL=...
   SUPABASE_SERVICE_KEY=...
   STORAGE_BACKEND=postgres
   ```
3. Import CSV: `python3 scripts/import_csv.py`
4. Verify: `curl localhost:8000/health` → `"storage": "postgres"`

## CI

GitHub Actions workflow: `.github/workflows/ci.yml`

- Engine: `python -m unittest discover -s tests`
- Web: `npm ci && npm run build`

## Archived code

Flask platform moved to `engine/_archive/platform/`. Do not run `python3 run.py`.

## Health check

`GET /health` returns:

```json
{
  "status": "ok",
  "version": "3.4",
  "storage": "csv|postgres",
  "email": "resend|gmail|none",
  "celery": true
}
```