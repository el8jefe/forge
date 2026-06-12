# FORGE System Documentation

## File Reference

| File | Purpose |
|---|---|
| `scraper.py` | Queries Google Places API, scores leads, writes leads.csv and call_list.csv |
| `site_builder.py` | Generates HTML demo sites for leads, pushes to GitHub Pages |
| `agent.py` | Orchestrates the full outreach pipeline: scrape → build → email |
| `followup.py` | Sends 3-day follow-up emails to non-responders |
| `emailer.py` | Gmail SMTP sender with warmup schedule and burst protection |
| `system_logger.py` | Centralized log() utility, writes to system_log.txt |
| `notifications.py` | Dashboard push notifications and Twilio SMS alerts |
| `dashboard.py` | Legacy dashboard — superseded by platform/admin_portal.py |
| `config.py` | Reads all environment variables from .env |
| `run.py` | Entry point — starts the Flask platform server |
| `platform/app.py` | Central Flask application factory, registers all blueprints |
| `platform/auth.py` | Admin session management and CSRF token helpers |
| `platform/stripe_handler.py` | Stripe Checkout sessions, webhook handler, conversion logging |
| `platform/client_portal.py` | Client login (magic code), dashboard, change requests |
| `platform/admin_portal.py` | Admin dashboard — leads, clients, bookings, resellers, log |
| `platform/booking_agent.py` | AI booking widget API (Claude-powered), session management |
| `platform/whitelabel.py` | White-label reseller registration, API access control |
| `CHECKPOINT.md` | Task completion log for interrupted sessions |
| `SYSTEM_README.md` | This file |

## Starting the Platform

```bash
# Install dependencies (first time only)
pip3 install -r requirements.txt

# Start the platform server
python3 run.py
```

The server starts on port 8080 by default. Set `PORT` in .env to change.

## Starting the Lead Pipeline

```bash
python3 agent.py        # Scrape, build sites, send outreach (runs once)
python3 followup.py     # Send follow-ups to non-responders
```

## URL Map

| URL | Description |
|---|---|
| `http://localhost:8080/` | Public marketing landing page |
| `http://localhost:8080/demo/<slug>` | Demo claim page for a specific lead |
| `http://localhost:8080/checkout/<tier>/<slug>` | Stripe Checkout (starter/growth/autopilot) |
| `http://localhost:8080/webhook/stripe` | Stripe webhook endpoint |
| `http://localhost:8080/success` | Post-payment success page |
| `http://localhost:8080/portal/` | Client portal login |
| `http://localhost:8080/portal/dashboard` | Client dashboard (authenticated) |
| `http://localhost:8080/admin/` | Admin login |
| `http://localhost:8080/admin/dashboard` | Admin dashboard (authenticated) |
| `http://localhost:8080/whitelabel` | Reseller registration page |
| `http://localhost:8080/api/booking/chat` | Booking agent chat API (POST) |
| `http://localhost:8080/api/booking/widget.js?slug=<slug>` | Booking widget script |
| `http://localhost:8080/api/test-mode` | Get current TEST_MODE status |
| `http://localhost:8080/api/toggle-test-mode` | Toggle TEST_MODE in .env (POST) |
| `http://localhost:8080/api/whitelabel/scrape` | Reseller scrape API (POST, requires key) |
| `http://localhost:8080/api/whitelabel/build` | Reseller build API (POST, requires key) |
| `http://localhost:8080/api/whitelabel/send` | Reseller send API (POST, requires key) |
| `http://localhost:8080/health` | Health check — returns JSON status |

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `GOOGLE_PLACES_API_KEY` | Yes | Google Maps Places API for lead scraping |
| `GMAIL_SENDER` | Yes | Gmail address used for outreach |
| `GMAIL_APP_PASSWORD` | Yes | Gmail app-specific password (not your real password) |
| `MY_TEST_EMAIL` | Yes | Internal notification address; all emails go here in TEST_MODE |
| `STRIPE_SECRET_KEY` | Yes | Stripe secret key (use sk_test_... for test mode) |
| `STRIPE_PUBLISHABLE_KEY` | Yes | Stripe publishable key |
| `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret |
| `FLASK_SECRET_KEY` | Yes | Flask session encryption key — change in production |
| `ADMIN_PASSWORD` | Yes | Admin dashboard password |
| `TEST_MODE` | Yes | true/false — when true, all emails go to MY_TEST_EMAIL |
| `PORT` | No | Server port (default: 8080) |
| `ANTHROPIC_API_KEY` | No | Claude API key for AI booking agent (Autopilot tier) |
| `UNSPLASH_ACCESS_KEY` | No | Unsplash API key for HOT-tier site hero images |
| `GITHUB_TOKEN` | No | GitHub personal access token for Pages deployment |
| `GITHUB_USERNAME` | No | GitHub username for Pages deployment |
| `TWILIO_ACCOUNT_SID` | No | Twilio account SID for SMS notifications |
| `TWILIO_AUTH_TOKEN` | No | Twilio auth token |
| `TWILIO_FROM` | No | Twilio phone number (E.164 format) |
| `MY_PHONE` | No | Owner's phone for SMS alerts |

## Going Live (TEST_MODE → Production)

1. Add real Stripe keys from dashboard.stripe.com to `.env`
2. Update `STRIPE_WEBHOOK_SECRET` from the Stripe webhook dashboard
3. Set `TEST_MODE=false` in `.env` (or toggle via admin dashboard)
4. Set `FLASK_SECRET_KEY` to a strong random value
5. Add `ANTHROPIC_API_KEY` for the AI booking agent (Autopilot tier)
6. Point your domain DNS to this server
7. Run behind a reverse proxy (nginx + gunicorn recommended)
8. Apply for Stripe production access when the first client pays

## Revenue Streams

| Stream | Price | Handled by |
|---|---|---|
| Starter website | $200 one-time | stripe_handler.py |
| Growth retainer | $500/month | stripe_handler.py |
| Autopilot retainer | $800/month | stripe_handler.py + booking_agent.py |
| White-label reseller | $300/month | whitelabel.py |

## Booking Agent Widget

Embed the AI booking widget on any Autopilot-tier client's site with one script tag:

```html
<script src="https://your-domain.com/api/booking/widget.js?slug=business-slug"></script>
```

Create a client profile at `client_profiles/<slug>.json` using the schema in
`client_profiles/example.json` to configure the agent's business knowledge.

## White-Label API

Resellers authenticate with the `X-TradeBuilt-Key` header (100 calls/day limit):

```bash
# Scrape leads
curl -X POST https://your-domain.com/api/whitelabel/scrape \
  -H "X-TradeBuilt-Key: <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"city": "Denver", "state": "CO", "business_type": "plumber"}'

# Build a demo site
curl -X POST https://your-domain.com/api/whitelabel/build \
  -H "X-TradeBuilt-Key: <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"business_name": "...", "business_type": "plumber", "email": "..."}'
```

## Known Limitations and Next Steps

- `emailer.send_outreach_email` must be called from agent.py which manages
  the warmup schedule. The admin "Send Now" button calls it directly, bypassing
  warmup state. Use with care.
- The booking agent session store is in-memory — sessions are lost on server restart.
  A future version should use Redis or SQLite for persistence.
- White-label scraping calls `scraper.py` as a subprocess, which blocks for 60-120s.
  A job queue (Celery/RQ) would improve this for high-volume reseller use.
- The demo frame on the claim page uses an iframe which may not load GitHub Pages
  URLs in all browsers due to X-Frame-Options headers. Consider a screenshot approach.
- Testimonials on the landing page are placeholders — replace with real client quotes.
