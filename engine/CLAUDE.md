# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lead generation and sales automation system targeting blue collar service businesses (HVAC, plumbers, electricians, roofers, landscapers, pest control) with bad or no websites. The pipeline scrapes businesses via Google Places, scores their website quality, generates free demo sites, and sends cold outreach emails.

## Current Direction
- Owner: Juan Pablo Rincon (juanparinconr@gmail.com)
- Building this into a full AI agency app that can be sold as a service
- Target clients: blue collar businesses with bad/no websites in any US city
- Pitch: "more calls, not just a website" — ROI-based selling
- Goal: 5 paying clients by April, $500-800/month retainer each
- Stack: Python backend, GitHub Pages for client demos, Gmail SMTP for outreach

## Running the Pipeline

```bash
python3 scraper.py    # Scrape and score leads from Google Places → leads.csv, call_list.csv
python3 agent.py      # Build demo sites on GitHub Pages + send outreach emails
python3 followup.py   # Send 3-day follow-up emails to non-responders
```

No build step, test suite, or package manager config. Dependencies are installed directly via pip.

## Environment Variables (`.env`)

| Variable | Purpose |
|---|---|
| `GOOGLE_PLACES_API_KEY` | Google Maps Places API |
| `GMAIL_APP_PASSWORD` | Gmail app-specific password for SMTP |
| `GITHUB_TOKEN` | Personal access token for repo creation + GitHub Pages |

## Architecture

### Data Flow

```
scraper.py
  → leads.csv        (businesses with email → go to agent.py)
  → call_list.csv    (phone-only leads → manual follow-up)

agent.py
  reads leads.csv → site_builder.py → GitHub Pages demo URL → sends email → log.csv

followup.py
  reads log.csv → checks 3-day threshold → sends follow-up → followup_log.csv
```

### Module Responsibilities

- **scraper.py** — Queries Google Places Text Search across 15+ states and 4 business types. Scores each lead's website (0–9 points) based on: no website (+3), not mobile-friendly (+2), outdated design (+2), no online booking (+2), no social links (+1). Splits output into `leads.csv` (has email) and `call_list.csv` (phone only). Filters chain businesses via blacklist keywords and caps at review count < 150.

- **agent.py** — Orchestrates the outreach loop: reads unprocessed leads, calls `site_builder.py`, sends personalized email via Gmail SMTP with the demo URL, logs to `log.csv`.

- **site_builder.py** — Generates a single-page HTML demo site from a template matching the business type (see Design Templates below). Scrapes the business's existing site for info. Pushes to a new GitHub repo via subprocess git commands and enables GitHub Pages. Returns the live `github.io` URL.

- **followup.py** — Reads `log.csv`, identifies emails sent 3+ days ago without follow-up, sends a second outreach message, logs to `followup_log.csv`.

- **emailer.py** — Deprecated; functionality merged into `agent.py`.

### Design Templates

`site_builder.py` has templates keyed by business type. Existing (legacy):
- **barbershop**: dark `#0a0a0a`, gold accents `#c9a84c`
- **restaurant**: light `#fafaf8`, dark text
- **salon**: light, warm tones `#b8896e`
- **florist**: light, green accents `#8faa7e`

Needed (blue collar — not yet implemented):
- **hvac**: dark navy `#0d1b2a`, orange accents `#f97316`
- **plumber**: dark `#111827`, blue accents `#3b82f6`
- **electrician**: dark `#0f172a`, yellow accents `#eab308`
- **roofer**: dark `#1c1917`, red accents `#ef4444`
- **landscaper**: dark `#14532d`, green accents `#22c55e`

### CSV Schema

- `leads.csv` / `call_list.csv` — scraped lead data (name, address, phone, email, website, score)
- `log.csv` — processing history used by `followup.py` to detect already-contacted leads
- `call_list_ranked.csv` — manually curated ranked call priorities
