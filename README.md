# FORGE

AI business automation platform — lead generation, demo websites, and outreach for local trade businesses.

## Repository structure

```
forge/
├── engine/     Python pipeline + FastAPI (lead-agent)
├── web/        Next.js SaaS UI (tradebuilt-saas)
├── supabase/   Database migrations
└── docs/       Architecture documentation
```

## Quick start

1. Copy environment files:
   ```bash
   cp engine/.env.example engine/.env
   cp web/.env.local.example web/.env.local
   ```

2. Set a shared `FORGE_API_KEY` in both files (see `engine/PHASE0-SECURITY.md`).

3. Install and run:
   ```bash
   cd engine && pip install -r requirements.txt && python api.py
   cd web && npm install && npm run dev
   ```

4. Open http://localhost:3000 (web) and http://localhost:8000/health (API).

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Phase 0 security setup](engine/PHASE0-SECURITY.md)

## Legacy directories

The original `~/lead-agent` and `~/tradebuilt-saas` folders remain as snapshots. **Active development is in `forge/`.** Delete the old directories once you verify the monorepo works.