#!/usr/bin/env bash
# Run FORGE Supabase migrations 001 → 002 → 003
# Requires: supabase CLI logged in (supabase login) OR DATABASE_URL set
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MIGRATIONS=(
  "$ROOT/supabase/migrations/001_initial.sql"
  "$ROOT/supabase/migrations/002_rls_fix.sql"
  "$ROOT/supabase/migrations/003_phase2_pipeline.sql"
)

if [[ -n "${DATABASE_URL:-}" ]]; then
  echo "Applying migrations via psql (DATABASE_URL)..."
  for f in "${MIGRATIONS[@]}"; do
    echo "  → $(basename "$f")"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
  done
  echo "Done."
  exit 0
fi

if command -v supabase >/dev/null 2>&1 && supabase projects list >/dev/null 2>&1; then
  echo "Applying migrations via supabase db execute..."
  cd "$ROOT"
  for f in "${MIGRATIONS[@]}"; do
    echo "  → $(basename "$f")"
    supabase db execute -f "$f"
  done
  echo "Done."
  exit 0
fi

echo "ERROR: Cannot run migrations."
echo "  Option A: supabase login && supabase link --project-ref <ref> && re-run"
echo "  Option B: export DATABASE_URL=postgresql://postgres:PASSWORD@db.<ref>.supabase.co:5432/postgres && re-run"
echo "  Option C: Paste SQL files manually in Supabase dashboard → SQL editor"
exit 1