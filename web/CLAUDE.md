# TradeBuilt SaaS — Claude Code Context

## What This Is
AI-powered SaaS that generates demo websites for local trade businesses (HVAC, plumbing, electrical, roofing, etc.) and manages cold outreach. The pitch: enter a business name + city, get a scored demo site and a one-click cold email — in under 5 seconds.

**Owner:** Pablo Rincon (@el8jefe)
**GitHub:** github.com/el8jefe/tradebuilt-saas (not yet pushed)

---

## Stack
- **Framework:** Next.js 16.2, React 19, TypeScript
- **Styling:** Tailwind CSS v4, Framer Motion
- **AI:** Anthropic SDK (claude-opus-4-6, adaptive thinking)
- **Scraping:** Firecrawl API
- **Database:** Supabase (PostgreSQL) — **pending setup**
- **Auth:** Supabase Auth — **pending setup**
- **Payments:** Stripe — **pending setup**
- **Email:** Resend API — **code exists, key not set**
- **Deploy:** Vercel

---

## Run the App
```bash
cd /Users/pablorincon/tradebuilt-saas
npm run dev        # http://localhost:3000
npm run build      # production build check
```

---

## Architecture — Generation Pipeline
```
User input (name + location)
    ↓
/api/generate-site (POST)
    ↓
[1] scraper.ts      → Firecrawl: scrape business web presence
    ↓
[2] normalizer.ts   → Standardize data, infer service type + tone
    ↓
[3] lead-quality.ts → Score lead 0-100, assign temperature (Burning Hot/Hot/Warm/Cold)
    ↓
BRANCH:
  template mode (free) → template.ts → 2000-line HTML
  AI mode (pro)        → generator.ts → Claude writes copy → template.ts → HTML
    ↓
[4] scorer.ts       → Score site quality (clarity/specificity/trust/conversion)
    ↓
RESPONSE: { business, content, score, cached, mode, html }
```

---

## What's Built
- [x] Full generation pipeline (scrape → score → generate → email)
- [x] Landing page (`/`)
- [x] Generator page (`/generate`)
- [x] CRM dashboard (`/dashboard`) — localStorage only
- [x] 9 trade-specific themes (HVAC, Plumbing, Electric, Roofing, Landscaping, Painting, Concrete, Pest, Cleaning)
- [x] Dual-layer lead scoring (website quality + lead temperature)
- [x] Email outreach via Resend (code complete, needs API key)
- [x] Dark industrial visual redesign (in progress)

## What's Pending
- [ ] Supabase setup (replace localStorage CRM with real DB)
- [ ] Supabase Auth (login/signup, protect /generate and /dashboard)
- [ ] Stripe payments (Free vs Pro, $49/mo)
- [ ] Enable AI mode (remove 403, gate behind Pro plan)
- [ ] Fix email (add RESEND_API_KEY to .env.local)
- [ ] Deploy to Vercel
- [ ] Custom domain: tradebuilt.io

---

## Key Files
| Path | Purpose |
|---|---|
| `app/page.tsx` | Landing page |
| `app/generate/page.tsx` | Generator form + results |
| `app/dashboard/page.tsx` | Lead CRM pipeline |
| `app/api/generate-site/route.ts` | Core generation API |
| `app/api/send-email/route.ts` | Email outreach API |
| `services/scraper.ts` | Firecrawl business scraping |
| `services/normalizer.ts` | Business data normalization |
| `services/generator.ts` | Claude AI copywriting |
| `services/template.ts` | HTML site generation |
| `services/scorer.ts` | Site quality scoring |
| `services/lead-quality.ts` | Lead temperature scoring |
| `services/emailer.ts` | Resend email delivery |
| `lib/crm.ts` | Lead storage (localStorage → Supabase) |
| `lib/types.ts` | All TypeScript interfaces |
| `lib/themes.ts` | 9 trade color themes |

---

## Environment Variables
```bash
# .env.local
ANTHROPIC_API_KEY=          # Required for AI mode — currently empty
FIRECRAWL_API_KEY=          # For scraping — currently set
RESEND_API_KEY=             # For email — currently empty
RESEND_FROM_EMAIL=          # Default: outreach@tradebuilt.io

# Pending (Supabase)
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Pending (Stripe)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
```

---

## Claude Rules for This Project
1. **Keep service files intact.** The pipeline in `services/` is solid. Don't refactor it unless explicitly asked.
2. **Use existing types.** All interfaces live in `lib/types.ts`. Don't create parallel types.
3. **UI theme is open for redesign.** Pablo no longer wants dark-only. New direction TBD — do not enforce the old dark industrial style.
4. **Tailwind v4.** This uses `@import "tailwindcss"` in globals.css, not a config file. Use inline styles or CSS vars for custom tokens.
5. **Framer Motion is available.** Use it for animations. Import from `framer-motion`.
6. **CRM function signatures must stay the same** when migrating from localStorage to Supabase so components don't break.
7. **Rate limit:** API has 20 requests/hour per IP. Don't remove this.
