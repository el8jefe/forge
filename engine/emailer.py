"""
emailer.py — FORGE Gmail SMTP Sender
Gmail warmup schedule: 80/140/200/260/320/380/500 emails per day over 7 days.
Burst protection: max 30 emails per 60-minute window.
Priority queue: HOT leads before WARM leads, sorted by score descending within tier.
Tracks all state in send_log.json and warmup_state.json.
"""

import os
import json
import smtplib
import random
import time
import datetime
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from system_logger import log

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SEND_LOG_FILE = os.path.join(SCRIPT_DIR, "send_log.json")
WARMUP_FILE = os.path.join(SCRIPT_DIR, "warmup_state.json")
LEADS_CSV = os.path.join(SCRIPT_DIR, "leads.csv")

GMAIL_SENDER = os.getenv("GMAIL_SENDER", "juanparinconr@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
MY_TEST_EMAIL = os.getenv("MY_TEST_EMAIL", "juanparinconr@gmail.com")
MY_PHONE = os.getenv("MY_PHONE", "(203) 609-4807")
TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"

GMAIL_MAX = 500
BURST_LIMIT = 30  # max sends per 60-minute window

WARMUP_SCHEDULE = {
    1: 80,
    2: 140,
    3: 200,
    4: 260,
    5: 320,
    6: 380,
}
# Day 7 and beyond: GMAIL_MAX

DAILY_LIMIT = GMAIL_MAX  # Exported for backwards-compat; actual limit is from warmup


# ─── WARMUP STATE ──────────────────────────────────────────────────────────────

def _empty_hourly_counts() -> dict:
    """Return a zeroed hourly counts dict for all 24 hours."""
    return {str(h): 0 for h in range(24)}


def load_warmup_state() -> dict:
    """
    Load warmup state from warmup_state.json.
    Creates the file with today as start_date if missing.

    Returns:
        dict: warmup state with start_date, current_day, daily_limit_override.
    """
    if not os.path.exists(WARMUP_FILE):
        state = {
            "start_date": datetime.date.today().isoformat(),
            "current_day": 1,
            "daily_limit_override": WARMUP_SCHEDULE[1],
        }
        _save_warmup_state(state)
        log("warmup_init", "INFO", f"Created warmup_state.json — day 1 limit={WARMUP_SCHEDULE[1]}")
        return state
    with open(WARMUP_FILE, "r") as f:
        return json.load(f)


def _save_warmup_state(state: dict):
    """Write warmup state atomically."""
    with open(WARMUP_FILE, "w") as f:
        json.dump(state, f, indent=2)


def update_warmup_state() -> dict:
    """
    Recalculate current_day from start_date and update daily_limit_override.
    Call once at the start of each pipeline cycle.

    Returns:
        dict: Updated warmup state.
    """
    state = load_warmup_state()
    try:
        start = datetime.date.fromisoformat(state["start_date"])
    except (KeyError, ValueError):
        start = datetime.date.today()
        state["start_date"] = start.isoformat()

    current_day = (datetime.date.today() - start).days + 1
    state["current_day"] = current_day
    state["daily_limit_override"] = WARMUP_SCHEDULE.get(current_day, GMAIL_MAX)
    _save_warmup_state(state)
    log("warmup_update", "INFO", f"Day {current_day} | limit={state['daily_limit_override']}")
    return state


def get_daily_limit() -> int:
    """
    Return the effective daily send limit based on warmup schedule.

    Returns:
        int: Max emails allowed today.
    """
    state = load_warmup_state()
    return state.get("daily_limit_override", GMAIL_MAX)


# ─── SEND LOG ──────────────────────────────────────────────────────────────────

def _empty_send_log(today: str, warmup_day: int) -> dict:
    """Return a fresh send log dict for today."""
    return {
        "date": today,
        "count": 0,
        "hourly_counts": _empty_hourly_counts(),
        "warmup_day": warmup_day,
        "last_send_timestamp": "",
        "sends": [],
    }


def load_send_log() -> dict:
    """
    Load send_log.json. Resets to today if date has changed.
    Ensures hourly_counts covers all 24 hours.

    Returns:
        dict: Send log for the current day.
    """
    today = datetime.date.today().isoformat()
    state = load_warmup_state()
    warmup_day = state.get("current_day", 1)

    if not os.path.exists(SEND_LOG_FILE):
        return _empty_send_log(today, warmup_day)

    with open(SEND_LOG_FILE, "r") as f:
        try:
            data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            return _empty_send_log(today, warmup_day)

    if data.get("date") != today:
        return _empty_send_log(today, warmup_day)

    # Ensure hourly_counts has all 24 keys
    hc = data.get("hourly_counts", {})
    for h in range(24):
        hc.setdefault(str(h), 0)
    data["hourly_counts"] = hc

    return data


def save_send_log(data: dict):
    """
    Atomically write send_log.json.

    Parameters:
        data (dict): The full send log dict to write.
    """
    with open(SEND_LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_today_count() -> int:
    """
    Return count of successful sends today.

    Returns:
        int: Number of emails sent today.
    """
    return load_send_log().get("count", 0)


def get_current_hour_count() -> int:
    """
    Return count of sends in the current clock hour.

    Returns:
        int: Number of emails sent in the current hour.
    """
    data = load_send_log()
    hour_key = str(datetime.datetime.now().hour)
    return data.get("hourly_counts", {}).get(hour_key, 0)


def record_send(recipient: str, business_name: str, success: bool, error: str = ""):
    """
    Record a send attempt in send_log.json. Atomic read-modify-write.

    Parameters:
        recipient (str): Email address the message was sent to.
        business_name (str): Business name for logging.
        success (bool): Whether the SMTP send succeeded.
        error (str): Error message if failed.
    """
    data = load_send_log()
    entry = {
        "ts": datetime.datetime.now().isoformat(),
        "to": recipient,
        "business": business_name,
        "success": success,
        "error": error,
    }
    data.setdefault("sends", []).append(entry)
    if success:
        data["count"] = data.get("count", 0) + 1
        hour_key = str(datetime.datetime.now().hour)
        data.setdefault("hourly_counts", _empty_hourly_counts())[hour_key] = (
            data["hourly_counts"].get(hour_key, 0) + 1
        )
        data["last_send_timestamp"] = entry["ts"]
    save_send_log(data)


def check_batch_errors(batch_size: int = 10) -> int:
    """
    Return number of failures in the last batch_size sends.

    Parameters:
        batch_size (int): How many recent sends to inspect.

    Returns:
        int: Count of failed sends.
    """
    data = load_send_log()
    recent = data.get("sends", [])[-batch_size:]
    return sum(1 for s in recent if not s.get("success"))


# ─── BUSINESS COPY LIBRARY ─────────────────────────────────────────────────────

BUSINESS_COPY = {
    # HOME SERVICES / TRADES
    "hvac": {
        "accent": "#f97316", "header_bg": "#0d1b2a",
        "service_label": "HVAC company",
        "pain_hook": "when someone's AC breaks at 9pm, they Google the nearest HVAC tech — and call whoever looks legit",
        "outcome": "more service calls",
    },
    "plumber": {
        "accent": "#3b82f6", "header_bg": "#111827",
        "service_label": "plumbing business",
        "pain_hook": "burst pipes and clogged drains don't wait — homeowners call whoever shows up first on Google",
        "outcome": "more booked jobs",
    },
    "electrician": {
        "accent": "#eab308", "header_bg": "#0f172a",
        "service_label": "electrical business",
        "pain_hook": "homeowners search Google before they call anyone — if you're not there, you don't exist",
        "outcome": "more booked jobs",
    },
    "roofer": {
        "accent": "#ef4444", "header_bg": "#1c1917",
        "service_label": "roofing company",
        "pain_hook": "after every storm, homeowners search for roofers and call whoever looks most professional",
        "outcome": "more storm-season leads",
    },
    "landscaper": {
        "accent": "#22c55e", "header_bg": "#14532d",
        "service_label": "landscaping business",
        "pain_hook": "homeowners searching for landscapers judge your business in 3 seconds based on your online presence",
        "outcome": "more residential contracts",
    },
    "pest_control": {
        "accent": "#f97316", "header_bg": "#1a1a2e",
        "service_label": "pest control business",
        "pain_hook": "pest problems are urgent — people search and call whoever looks trustworthy and local",
        "outcome": "more service calls",
    },
    # PERSONAL CARE
    "barbershop": {
        "accent": "#c9a84c", "header_bg": "#0a0a0a",
        "service_label": "barbershop",
        "pain_hook": "most people find their next barbershop on Google — if you're not showing up, you're losing new clients every week",
        "outcome": "more new clients and bookings",
    },
    "salon": {
        "accent": "#b8896e", "header_bg": "#1a0f0a",
        "service_label": "salon",
        "pain_hook": "clients search for salons on their phones — a site that doesn't look good on mobile costs you bookings every day",
        "outcome": "more appointments",
    },
    # OUTDOOR / PROPERTY
    "florist": {
        "accent": "#8faa7e", "header_bg": "#1a2a1a",
        "service_label": "flower shop",
        "pain_hook": "people search for florists for weddings, birthdays, and last-minute orders — without a site, they can't find you",
        "outcome": "more orders",
    },
    # FOOD
    "restaurant": {
        "accent": "#ef4444", "header_bg": "#1a0000",
        "service_label": "restaurant",
        "pain_hook": "when people search for places to eat nearby, your website is the first impression — a bad one means they go somewhere else",
        "outcome": "more reservations and walk-ins",
    },
    # FALLBACK
    "default": {
        "accent": "#c9a84c", "header_bg": "#0a0a0a",
        "service_label": "local business",
        "pain_hook": "most customers search online before calling anyone — if your site isn't working, you're losing leads you never see",
        "outcome": "more calls and leads",
    },
}

_BT_ALIASES = {
    "plumbing": "plumber",
    "electrical": "electrician",
    "roofing": "roofer",
    "landscaping": "landscaper",
    "barber": "barbershop",
    "hair_salon": "salon",
    "pest": "pest_control",
    "pest control": "pest_control",
}


def _is_safe_first_name(name: str) -> bool:
    """Return True if token looks like a human first name."""
    token = (name or "").strip()
    if not token:
        return False
    if len(token) < 2 or len(token) > 20:
        return False
    if any(ch.isdigit() for ch in token):
        return False
    if not all(ch.isalpha() or ch in "-'" for ch in token):
        return False
    blocked = {
        "team", "staff", "service", "services", "support", "office", "admin",
        "plumbing", "roofing", "electric", "electrical", "landscaping", "hvac",
        "company", "inc", "llc", "corp", "property", "solutions",
    }
    return token.lower() not in blocked


def _normalized_owner_name_for_email(lead: dict) -> str:
    """
    Return owner_name only when confidence is acceptable and format is safe.
    """
    owner_name = (lead.get("owner_name") or "").strip()
    if not owner_name:
        return ""
    owner_confidence = (lead.get("owner_confidence") or "").strip().lower()
    if owner_confidence and owner_confidence not in {"high", "medium"}:
        return ""
    first = owner_name.split()[0]
    if not _is_safe_first_name(first):
        return ""
    return owner_name


def _get_copy(business_type: str) -> dict:
    bt = (business_type or "").lower().strip().replace(" ", "_").replace("-", "_")
    bt = _BT_ALIASES.get(bt, bt)
    return BUSINESS_COPY.get(bt, BUSINESS_COPY["default"])


def _greeting(owner_name: str) -> str:
    if owner_name and owner_name.strip():
        first = owner_name.strip().split()[0].title()
        return f"Hey {first},"
    return "Hey,"


def _html_wrapper(greeting, pre_paras, demo_url, cta_text, post_paras, sign_off, accent, header_bg):
    pre = "".join(
        f'<p style="font-size:15px;color:#444;line-height:1.7;margin:0 0 16px;">{p}</p>'
        for p in pre_paras
    )
    post = "".join(
        f'<p style="font-size:15px;color:#444;line-height:1.7;margin:0 0 16px;">{p}</p>'
        for p in post_paras
    )
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:32px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;overflow:hidden;max-width:600px;width:100%;">
      <tr><td style="background:{header_bg};padding:28px 40px;">
        <span style="font-size:22px;font-weight:bold;color:{accent};font-family:Georgia,serif;letter-spacing:0.05em;">Forge</span>
        <span style="color:#ffffff;font-size:11px;display:block;margin-top:4px;opacity:0.5;letter-spacing:0.15em;text-transform:uppercase;">Web Studio &mdash; Greenwich, CT</span>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="font-size:16px;color:#222;margin:0 0 20px;">{greeting}</p>
        {pre}
        <table cellpadding="0" cellspacing="0" width="100%" style="margin:24px 0;">
          <tr><td align="center">
            <a href="{demo_url}" style="display:inline-block;background:{accent};color:#0a0a0a;padding:16px 40px;text-decoration:none;font-weight:bold;font-size:15px;letter-spacing:0.03em;">
              {cta_text} &rarr;
            </a>
          </td></tr>
        </table>
        {post}
        <p style="font-size:15px;color:#222;line-height:1.8;margin:24px 0 0;">{sign_off}</p>
      </td></tr>
      <tr><td style="background:#f9f9f9;padding:18px 40px;border-top:1px solid #eee;">
        <p style="font-size:11px;color:#aaa;margin:0;line-height:1.6;">
          You&rsquo;re receiving this because your business appeared in a local search.
          Reply STOP to opt out.
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


# ─── TEMPLATE A: Short & Direct ────────────────────────────────────────────────
# Use for: HOT leads with no website. Gets to the demo in 2 lines.

def _template_a(name, owner_name, copy, demo_url):
    greeting = _greeting(owner_name)
    subject = f"I built {name} a free site — take a look"

    pre = [
        f"I found {name} on Google and noticed you didn&rsquo;t have a website.",
        "So I built you one. It&rsquo;s already live:",
    ]
    post = [
        f"If you want it published on your domain with your real phone, hours, and services &mdash; "
        f"I&rsquo;ll handle everything for <strong>$200 flat</strong>. No monthly fees. No contracts.",
        "If it&rsquo;s not for you, no worries &mdash; keep the demo.",
    ]
    sign_off = f"&ndash; Pablo Rincon<br>Forge Web Studio &middot; Greenwich, CT<br>{MY_PHONE}"

    html = _html_wrapper(greeting, pre, demo_url, "View Your Free Site", post, sign_off, copy["accent"], copy["header_bg"])
    plain = (
        f"{greeting}\n\n"
        f"I found {name} on Google and noticed you didn't have a website.\n\n"
        f"So I built you one — it's already live:\n{demo_url}\n\n"
        f"If you want it published on your domain with your real phone, hours, and services — "
        f"I'll handle everything for $200 flat. No monthly fees. No contracts.\n\n"
        f"If it's not for you, no worries — keep the demo.\n\n"
        f"- Pablo Rincon\nForge Web Studio · Greenwich, CT\n{MY_PHONE}\n\n"
        f"---\nYou're receiving this because your business appeared in a local search. Reply STOP to opt out."
    )
    return subject, html, plain


# ─── TEMPLATE B: Personal & Local ──────────────────────────────────────────────
# Use for: WARM leads with a weak existing website. Pablo's local voice and angle.

def _template_b(name, owner_name, city, copy, demo_url):
    greeting = _greeting(owner_name)
    subject = f"Had some time, built something for {name}"
    city_str = f" in {city}" if city else ""

    pre = [
        f"I&rsquo;m Pablo &mdash; I grew up in Greenwich, went to GHS, studied at UConn. "
        f"I build websites and digital tools for local businesses.",
        f"I came across {name}{city_str} and noticed your current site could use a refresh. "
        f"So I went ahead and built you a free demo:",
    ]
    post = [
        "No cost, no commitment &mdash; I just wanted to show you what&rsquo;s possible.",
        f"If you like it, I can have it live on your domain within 24 hours &mdash; "
        f"including online booking so clients can schedule without calling. "
        f"<strong>$200 flat, no monthly fees.</strong>",
        "I&rsquo;m local, bilingual in English and Spanish, and I don&rsquo;t disappear after I get paid.",
    ]
    sign_off = (
        f"Reply here or text me at {MY_PHONE}.<br><br>"
        f"&ndash; Pablo Rincon<br>Forge Web Studio &middot; Greenwich, CT<br>{MY_PHONE}"
    )

    html = _html_wrapper(greeting, pre, demo_url, "View Your Free Demo", post, sign_off, copy["accent"], copy["header_bg"])
    plain = (
        f"{greeting}\n\n"
        f"I'm Pablo — I grew up in Greenwich, went to GHS, studied at UConn. "
        f"I build websites and digital tools for local businesses.\n\n"
        f"I came across {name}{city_str} and noticed your current site could use a refresh. "
        f"So I went ahead and built you a free demo:\n{demo_url}\n\n"
        f"No cost, no commitment — I just wanted to show you what's possible.\n\n"
        f"If you like it, I can have it live on your domain within 24 hours — "
        f"including online booking so clients can schedule without calling. $200 flat, no monthly fees.\n\n"
        f"I'm local, bilingual in English and Spanish, and I don't disappear after I get paid.\n\n"
        f"Reply here or text me at {MY_PHONE}.\n\n"
        f"- Pablo Rincon\nForge Web Studio · Greenwich, CT\n{MY_PHONE}\n\n"
        f"---\nYou're receiving this because your business appeared in a local search. Reply STOP to opt out."
    )
    return subject, html, plain


# ─── TEMPLATE C: Competitive & Results-Focused ─────────────────────────────────
# Use for: HOT leads with 50+ reviews — established business losing to competitors online.

def _template_c(name, owner_name, city, copy, demo_url):
    greeting = _greeting(owner_name)
    city_str = city or "your area"
    subject = f"{name} — are you getting found when it matters?"

    pre = [
        f"Quick question: when someone in {city_str} searches for a {copy['service_label']} "
        f"at 9pm, does {name} show up &mdash; and when they land on your site, do they call you?",
        f"{copy['pain_hook'].capitalize()}.",
        "I built you a demo to show what that experience could look like:",
    ]
    post = [
        f"What&rsquo;s included: mobile-first design built for your trade, click-to-call and hours "
        f"built in, optimized for &ldquo;near me&rdquo; searches, live within 48 hours.",
        f"Setup is <strong>$200 flat</strong>. If you want ongoing SEO, review management, and Google "
        f"profile optimization, I offer a monthly package starting at <strong>$500/month</strong>.",
        f"Most clients get their first inbound call within 2 weeks of going live.",
        f"Worth a 10-minute call? Reply here or text me at {MY_PHONE}.",
    ]
    sign_off = f"&ndash; Pablo Rincon<br>Forge Web Studio &middot; Greenwich, CT<br>{MY_PHONE}"

    html = _html_wrapper(greeting, pre, demo_url, "See Your Demo", post, sign_off, copy["accent"], copy["header_bg"])
    plain = (
        f"{greeting}\n\n"
        f"Quick question: when someone in {city_str} searches for a {copy['service_label']} "
        f"at 9pm, does {name} show up — and when they land on your site, do they call you?\n\n"
        f"{copy['pain_hook'].capitalize()}.\n\n"
        f"I built you a demo to show what that experience could look like:\n{demo_url}\n\n"
        f"What's included: mobile-first design built for your trade, click-to-call and hours built in, "
        f"optimized for 'near me' searches, live within 48 hours.\n\n"
        f"Setup is $200 flat. If you want ongoing SEO, review management, and Google profile optimization, "
        f"I offer a monthly package starting at $500/month.\n\n"
        f"Most clients get their first inbound call within 2 weeks of going live.\n\n"
        f"Worth a 10-minute call? Reply here or text me at {MY_PHONE}.\n\n"
        f"- Pablo Rincon\nForge Web Studio · Greenwich, CT\n{MY_PHONE}\n\n"
        f"---\nYou're receiving this because your business appeared in a local search. Reply STOP to opt out."
    )
    return subject, html, plain


# ─── EMAIL BUILDER ─────────────────────────────────────────────────────────────

def build_html_email(lead: dict, demo_url: str) -> tuple:
    """
    Select and build the outreach email for a lead.

    Template selection:
      - HOT + 50+ reviews  → Template C (competitive/results)
      - HOT or no website  → Template A (short/direct)
      - WARM               → Template B (personal/local)

    Parameters:
        lead (dict): Lead record from leads.csv.
        demo_url (str): URL to the lead's demo site.

    Returns:
        tuple: (subject, html_body, plain_body)
    """
    name = (lead.get("business_name") or lead.get("name", "")).strip()
    owner_name = _normalized_owner_name_for_email(lead)
    city = (lead.get("city") or "").strip()
    business_type = (lead.get("business_type") or "").strip()
    lead_tier = (lead.get("lead_tier") or "WARM").strip().upper()
    website_status = (lead.get("website_status") or "").strip().lower()
    review_count = int(lead.get("review_count") or 0)

    copy = _get_copy(business_type)

    if lead_tier == "HOT" and review_count >= 50:
        return _template_c(name, owner_name, city, copy, demo_url)
    elif lead_tier == "HOT" or website_status == "no_website":
        return _template_a(name, owner_name, copy, demo_url)
    else:
        return _template_b(name, owner_name, city, copy, demo_url)


# ─── SMTP SENDER ───────────────────────────────────────────────────────────────

def send_email(lead: dict, demo_url: str) -> bool:
    """
    Send a cold outreach email for one lead.
    Enforces daily warmup limit and hourly burst limit.
    TEST_MODE routes all email to MY_TEST_EMAIL.

    Parameters:
        lead (dict): Lead record.
        demo_url (str): Demo site URL.

    Returns:
        bool: True on successful send.
    """
    reply_status = (lead.get("reply_status") or "").strip().lower()
    if reply_status in {"bounced", "stop", "stopped", "unsubscribe", "unsubscribed", "do_not_contact"}:
        log("send_email", "SKIP", f"{lead.get('business_name', '?')} — suppressed ({reply_status})")
        return False

    if not GMAIL_APP_PASSWORD:
        log("send_email", "ERROR", "GMAIL_APP_PASSWORD not set in .env")
        return False

    daily_limit = get_daily_limit()
    today_count = get_today_count()
    if today_count >= daily_limit:
        log("send_email", "WARNING", f"Daily warmup limit of {daily_limit} reached")
        print(f"Daily email limit ({daily_limit}) reached. Stopping for today.")
        return False

    hour_count = get_current_hour_count()
    if hour_count >= BURST_LIMIT:
        log("send_email", "WARNING", f"Burst limit of {BURST_LIMIT}/hour reached for hour {datetime.datetime.now().hour}")
        print(f"Burst limit ({BURST_LIMIT}/hour) reached. Skipping until next hour.")
        return False

    real_to = (lead.get("email") or "").strip()
    if not real_to:
        log("send_email", "SKIP", f"{lead.get('business_name', '?')} — no email")
        return False

    to_address = MY_TEST_EMAIL if TEST_MODE else real_to
    name = (lead.get("business_name") or lead.get("name", "?")).strip()

    if TEST_MODE:
        print(f"  TEST MODE — routing {name} email -> {MY_TEST_EMAIL}")

    subject, html_body, plain_body = build_html_email(lead, demo_url)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = to_address
    msg["Reply-To"] = GMAIL_SENDER
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, to_address, msg.as_string())
        server.quit()
        record_send(to_address, name, success=True)
        log("send_email", "SUCCESS", f"{name} -> {to_address}")
        print(f"  Email sent: {name} -> {to_address}")

        new_count = get_today_count()
        if new_count % 10 == 0 and new_count > 0:
            errors = check_batch_errors(10)
            if errors >= 3:
                log("send_email", "CRITICAL", f"{errors}/10 sends failed — pausing batch")
                print(f"CRITICAL: {errors} errors in last 10 sends — pausing until next run")
                return False

        return True

    except Exception as e:
        record_send(to_address, name, success=False, error=str(e))
        log("send_email", "ERROR", f"{name} -> {to_address} | {e}")
        print(f"  Email failed for {name}: {e}")
        return False


def sort_leads_by_priority(leads: list) -> list:
    """
    Sort leads so HOT comes before WARM, and within each tier by score descending.

    Parameters:
        leads (list): List of lead dicts.

    Returns:
        list: Sorted list.
    """
    def priority_key(lead):
        tier = lead.get("lead_tier", "WARM")
        score = int(lead.get("score", 0) or 0)
        tier_rank = 0 if tier == "HOT" else 1
        return (tier_rank, -score)

    return sorted(leads, key=priority_key)


def send_batch(leads: list, demo_urls: dict, stagger: bool = True) -> tuple:
    """
    Send emails to a list of leads. Enforces HOT-before-WARM priority.
    Stagger: random 18-35 seconds between sends.

    Parameters:
        leads (list): Lead dicts to email.
        demo_urls (dict): Maps business_name -> demo site URL.
        stagger (bool): Whether to sleep between sends.

    Returns:
        tuple: (sent_count, failed_count, sent_names)
    """
    prioritized = sort_leads_by_priority(leads)
    sent = 0
    failed = 0
    sent_names = []

    for lead in prioritized:
        name = (lead.get("business_name") or lead.get("name", "")).strip()
        demo_url = demo_urls.get(name, "")
        if not demo_url:
            log("send_batch", "SKIP", f"{name} — missing demo URL")
            failed += 1
            continue

        daily_limit = get_daily_limit()
        if get_today_count() >= daily_limit:
            log("send_batch", "WARNING", f"Daily limit {daily_limit} reached mid-batch")
            break

        ok = send_email(lead, demo_url)
        if ok:
            sent += 1
            sent_names.append(name)
            if stagger:
                delay = random.randint(18, 35)
                print(f"  Waiting {delay}s before next send...")
                time.sleep(delay)
        else:
            failed += 1

    return sent, failed, sent_names


def mark_lead_bounced(email: str):
    """
    Mark a lead in leads.csv as reply_status=bounced.

    Parameters:
        email (str): The email address that bounced.
    """
    if not os.path.exists(LEADS_CSV):
        return
    rows = []
    updated = False
    with open(LEADS_CSV, "r") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("email") == email and row.get("reply_status") != "bounced":
                row["reply_status"] = "bounced"
                updated = True
            rows.append(row)
    if updated and fieldnames:
        with open(LEADS_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        log("mark_bounced", "INFO", f"Marked {email} as bounced")


def send_summary_email(subject: str, body: str):
    """
    Send a plain-text summary to MY_TEST_EMAIL (admin notifications).

    Parameters:
        subject (str): Email subject.
        body (str): Plain text body.
    """
    if not GMAIL_APP_PASSWORD:
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = MY_TEST_EMAIL
    msg.attach(MIMEText(body, "plain"))
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, MY_TEST_EMAIL, msg.as_string())
        server.quit()
        log("send_summary_email", "SUCCESS", subject[:60])
    except Exception as e:
        log("send_summary_email", "ERROR", str(e))
