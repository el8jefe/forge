#!/usr/bin/env bash
# Push web/.env.local values to Vercel production (run from forge/web after vercel link)
set -euo pipefail

cd "$(dirname "$0")/../web"

if [[ ! -f .env.local ]]; then
  echo "Missing web/.env.local"
  exit 1
fi

# Keys required for production (add FORGE_API_URL after Railway deploy)
KEYS=(
  FORGE_API_KEY
  FORGE_API_URL
  FORGE_ROUTE_AUTH_ENABLED
  FORGE_ADMIN_USER_IDS
  NEXT_PUBLIC_SUPABASE_URL
  NEXT_PUBLIC_SUPABASE_ANON_KEY
  SUPABASE_SERVICE_ROLE_KEY
  RESEND_API_KEY
  RESEND_FROM_EMAIL
  STRIPE_SECRET_KEY
  STRIPE_WEBHOOK_SECRET
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
  STRIPE_PRO_PRICE_ID
  ANTHROPIC_API_KEY
  FIRECRAWL_API_KEY
)

for key in "${KEYS[@]}"; do
  val="$(grep -E "^${key}=" .env.local 2>/dev/null | head -1 | cut -d= -f2- || true)"
  if [[ -z "$val" ]]; then
    echo "skip $key (empty)"
    continue
  fi
  echo "set $key"
  printf '%s' "$val" | vercel env add "$key" production --force 2>/dev/null || \
    printf '%s' "$val" | vercel env add "$key" production
done

echo "Done. Run: vercel --prod"