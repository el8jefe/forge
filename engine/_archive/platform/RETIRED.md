# Flask platform — archived (Phase 5)

The Flask SaaS under `engine/_archive/platform/` is **no longer deployed**. Do not start it in production.

## Replacements

| Flask route | Replacement |
|-------------|-------------|
| `/admin/*` | `web/app/admin` — pipeline ops via FORGE API |
| `/portal/*` | `web/app/dashboard` — CRM (Supabase) |
| `/webhook/stripe` | `POST /webhook/stripe` on FastAPI (`engine/api.py`) |
| `/checkout/*` | `web/app/api/stripe/checkout` — Pro subscription |
| `/api/booking/*` | `web/app/api/booking/*` |
| Site generation | `POST /build-site` on FastAPI (`site_builder.py`) |
| Pipeline runs | `POST /run-pipeline` on FastAPI (Celery) |

## Local development

```bash
# Terminal 1 — Engine API
cd forge/engine && python3 api.py

# Terminal 2 — Next.js
cd forge/web && npm run dev
```

## Archive

Code lives under `engine/_archive/platform/` for reference only. `python3 run.py` exits with an error message.