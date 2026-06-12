"""
platform/whitelabel.py — FORGE White-Label Reseller System (Task 9)

DEPRECATED (Phase 1): Out of scope until FORGE has core revenue.
Do not enable in production. Scheduled for removal in Phase 3 backend consolidation.
See forge/docs/ARCHITECTURE.md.

Allows external freelancers to pay $300/month for API access to the FORGE
scraping, site-building, and outreach pipeline under their own brand.
"""

import os
import sys
import csv
import json
import uuid
import secrets
import hashlib
import datetime
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Blueprint, request, jsonify, render_template_string, redirect
from dotenv import load_dotenv
from system_logger import log

load_dotenv()

WHITELABEL_DIR = os.path.join(BASE_DIR, "whitelabel")
WHITELABEL_CLIENTS_CSV = os.path.join(BASE_DIR, "whitelabel_clients.csv")
WHITELABEL_USAGE_FILE = os.path.join(BASE_DIR, "whitelabel_usage.json")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
SIMULATION_MODE = STRIPE_SECRET_KEY.startswith("sk_test_placeholder")
MY_TEST_EMAIL = os.getenv("MY_TEST_EMAIL", "")
GMAIL_SENDER = os.getenv("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

DAILY_API_LIMIT = 100
WHITELABEL_PRICE_USD = 300

WHITELABEL_CLIENTS_FIELDS = [
    "freelancer_id", "name", "email", "business_name",
    "accent_color", "api_key", "created_date", "stripe_customer_id", "status"
]

whitelabel_bp = Blueprint("whitelabel", __name__)


# ─── DATA HELPERS ──────────────────────────────────────────────────────────────

def _read_clients() -> list:
    """Read whitelabel_clients.csv. Returns list of dicts."""
    if not os.path.exists(WHITELABEL_CLIENTS_CSV):
        return []
    with open(WHITELABEL_CLIENTS_CSV, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _append_client(data: dict):
    """Append a new reseller row to whitelabel_clients.csv."""
    file_exists = os.path.exists(WHITELABEL_CLIENTS_CSV)
    with open(WHITELABEL_CLIENTS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=WHITELABEL_CLIENTS_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: data.get(k, "") for k in WHITELABEL_CLIENTS_FIELDS})


def _find_client_by_key(api_key: str) -> dict:
    """
    Look up a reseller by their API key.

    Parameters:
        api_key (str): The X-TradeBuilt-Key header value.

    Returns:
        dict: Reseller record, or empty dict if not found or inactive.
    """
    for client in _read_clients():
        if client.get("api_key") == api_key and client.get("status") == "active":
            return client
    return {}


def _load_usage() -> dict:
    """Load whitelabel_usage.json."""
    if not os.path.exists(WHITELABEL_USAGE_FILE):
        return {}
    try:
        with open(WHITELABEL_USAGE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_usage(data: dict):
    """Write whitelabel_usage.json."""
    with open(WHITELABEL_USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _check_rate_limit(freelancer_id: str) -> bool:
    """
    Check and increment the daily API call counter for a reseller.
    Returns True if the call is allowed, False if the limit is exceeded.

    Parameters:
        freelancer_id (str): Reseller identifier.

    Returns:
        bool: True if within daily limit.
    """
    usage = _load_usage()
    today = datetime.date.today().isoformat()
    key = f"{freelancer_id}:{today}"
    count = usage.get(key, 0)
    if count >= DAILY_API_LIMIT:
        return False
    usage[key] = count + 1
    _save_usage(usage)
    return True


def _create_reseller_config(freelancer_id: str, data: dict, api_key: str):
    """
    Write the per-reseller config JSON file.

    Parameters:
        freelancer_id (str): Unique reseller ID.
        data (dict): Registration form data.
        api_key (str): Generated API key.
    """
    reseller_dir = os.path.join(WHITELABEL_DIR, freelancer_id)
    os.makedirs(reseller_dir, exist_ok=True)
    config = {
        "freelancer_id": freelancer_id,
        "business_name": data.get("business_name", ""),
        "email": data.get("email", ""),
        "accent_color": data.get("accent_color", "#c9a84c"),
        "daily_email_limit": 40,
        "api_key": api_key,
        "created_date": datetime.date.today().isoformat(),
    }
    with open(os.path.join(reseller_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2)


def _send_welcome_email(email: str, business_name: str, api_key: str):
    """
    Send a welcome email to the new reseller with their API key and docs.

    Parameters:
        email (str): Reseller email address.
        business_name (str): Their studio name.
        api_key (str): Generated API key.
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    if not all([GMAIL_SENDER, GMAIL_APP_PASSWORD]):
        return
    subject = f"Welcome to FORGE — Your API key is ready"
    body = f"""Welcome to FORGE White-Label, {business_name}.

Your API key: {api_key}

Include this key in all API requests as the header:
  X-TradeBuilt-Key: {api_key}

API Endpoints:
  POST /api/whitelabel/scrape  — Scrape leads for a city and business type
  POST /api/whitelabel/build   — Build a demo site for a lead
  POST /api/whitelabel/send    — Send outreach email for a lead

Rate limit: {DAILY_API_LIMIT} calls per day.

Request body format (JSON):
  scrape: {{"city": "Denver", "state": "CO", "business_type": "plumber"}}
  build:  {{"business_name": "...", "business_type": "...", "email": "..."}}
  send:   {{"business_name": "...", "email": "...", "demo_url": "..."}}

Your outreach emails must be sent from your own Gmail account.
FORGE does not send on your behalf.

Questions? Reply to this email.

-- FORGE Web Studio"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_SENDER
        msg["To"] = email
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, email, msg.as_string())
        server.quit()
        log("whitelabel_welcome", "SUCCESS", f"Sent to {email}")
    except Exception as e:
        log("whitelabel_welcome", "ERROR", str(e)[:120])


def _require_api_key():
    """
    Validate X-TradeBuilt-Key header and rate limit.

    Returns:
        tuple: (client_dict, None) on success, or (None, error_response) on failure.
    """
    api_key = request.headers.get("X-TradeBuilt-Key", "")
    if not api_key:
        return None, (jsonify({"error": "Missing X-TradeBuilt-Key header"}), 401)
    client = _find_client_by_key(api_key)
    if not client:
        return None, (jsonify({"error": "Invalid or inactive API key"}), 403)
    if not _check_rate_limit(client["freelancer_id"]):
        return None, (jsonify({"error": "Daily rate limit exceeded (100 calls/day)"}), 429)
    return client, None


# ─── REGISTRATION PAGE ─────────────────────────────────────────────────────────

_REGISTER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>FORGE — Reseller Access</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet"/>
  <style>
    *,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}
    body{background:#0a0a0a;color:#f5f5f0;font-family:'DM Sans',sans-serif;min-height:100vh;
         display:flex;align-items:center;justify-content:center;padding:24px;}
    .card{background:#111;border:1px solid rgba(255,255,255,0.07);padding:52px;max-width:500px;width:100%;}
    .brand{font-family:'DM Serif Display',serif;font-size:1.3rem;color:#c9a84c;margin-bottom:6px;}
    .brand-sub{font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;color:#8a8a8a;display:block;margin-bottom:36px;}
    h2{font-family:'DM Serif Display',serif;font-size:1.6rem;font-weight:400;margin-bottom:8px;}
    .subtitle{color:#8a8a8a;font-size:0.9rem;line-height:1.65;margin-bottom:36px;}
    .field{margin-bottom:18px;}
    label{display:block;font-size:0.62rem;letter-spacing:0.16em;text-transform:uppercase;color:#8a8a8a;margin-bottom:7px;}
    input{width:100%;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);
          color:#f5f5f0;padding:13px 16px;font-family:'DM Sans',sans-serif;font-size:0.9rem;}
    input:focus{outline:none;border-color:#c9a84c;}
    .color-row{display:flex;align-items:center;gap:12px;}
    input[type=color]{width:48px;height:48px;padding:4px;cursor:pointer;border:1px solid rgba(255,255,255,0.1);background:#111;}
    .price-note{background:rgba(201,168,76,0.07);border:1px solid rgba(201,168,76,0.2);
                padding:14px 18px;margin-bottom:28px;font-size:0.88rem;color:#c9a84c;}
    button{width:100%;background:#c9a84c;color:#0a0a0a;border:none;padding:16px;
           font-family:'DM Sans',sans-serif;font-size:0.8rem;font-weight:600;
           letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;margin-top:8px;}
    button:hover{opacity:0.85;}
    .features{margin-top:32px;border-top:1px solid rgba(255,255,255,0.06);padding-top:24px;}
    .feature{display:flex;gap:12px;margin-bottom:12px;font-size:0.85rem;color:#8a8a8a;}
    .feature span:first-child{color:#c9a84c;flex-shrink:0;}
    {% if message %}.alert{background:rgba(255,80,80,0.08);border:1px solid rgba(255,80,80,0.2);
    padding:12px 16px;margin-bottom:20px;font-size:0.85rem;color:#ff8080;}{% endif %}
  </style>
</head>
<body>
  <div class="card">
    <div class="brand">Forge</div>
    <span class="brand-sub">White-Label Reseller Access</span>
    <h2>Sell websites under your brand.</h2>
    <p class="subtitle">Get API access to the FORGE lead generation, site building, and outreach system.
    Everything runs under your business name and email.</p>
    {% if message %}<div class="alert">{{ message }}</div>{% endif %}
    <div class="price-note">${{ price }}/month &mdash; Cancel anytime. API key delivered instantly.</div>
    <form method="POST" action="/whitelabel/register">
      <input type="hidden" name="_csrf_token" value="{{ csrf_token }}"/>
      <div class="field">
        <label>Your Name</label>
        <input type="text" name="name" placeholder="Jane Smith" required/>
      </div>
      <div class="field">
        <label>Email Address</label>
        <input type="email" name="email" placeholder="jane@yourstudio.com" required/>
      </div>
      <div class="field">
        <label>Your Studio / Business Name</label>
        <input type="text" name="business_name" placeholder="Smith Web Studio" required/>
      </div>
      <div class="field">
        <label>Accent Color (for your reports)</label>
        <div class="color-row">
          <input type="color" name="accent_color" value="#c9a84c"/>
          <span style="font-size:0.82rem;color:#8a8a8a;">Shown on usage reports</span>
        </div>
      </div>
      <button type="submit">Continue to Payment &rarr;</button>
    </form>
    <div class="features">
      <div class="feature"><span>&#10003;</span><span>Scrape scored leads for any US city and business type</span></div>
      <div class="feature"><span>&#10003;</span><span>Build demo sites under your domain</span></div>
      <div class="feature"><span>&#10003;</span><span>100 API calls per day</span></div>
      <div class="feature"><span>&#10003;</span><span>Usage dashboard in admin panel</span></div>
      <div class="feature"><span>&#10003;</span><span>Outreach emails sent from your Gmail, not ours</span></div>
    </div>
  </div>
</body>
</html>"""


# ─── ROUTES — PUBLIC ───────────────────────────────────────────────────────────

@whitelabel_bp.route("/whitelabel", methods=["GET"])
def register_page():
    """Render the reseller registration page."""
    from .auth import generate_csrf_token
    return render_template_string(
        _REGISTER_HTML,
        price=WHITELABEL_PRICE_USD,
        csrf_token=generate_csrf_token(),
        message=request.args.get("msg", ""),
    )


@whitelabel_bp.route("/whitelabel/register", methods=["POST"])
def register():
    """
    Accept registration form. In simulation mode, provision the account immediately.
    In live mode, redirect to Stripe Checkout for $300/month.
    """
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    business_name = request.form.get("business_name", "").strip()
    accent_color = request.form.get("accent_color", "#c9a84c").strip()

    if not all([name, email, business_name]):
        return redirect("/whitelabel?msg=All+fields+are+required.")

    if SIMULATION_MODE:
        return _provision_reseller(name, email, business_name, accent_color, session_obj={})

    try:
        import stripe as stripe_lib
        stripe_lib.api_key = STRIPE_SECRET_KEY
        product = stripe_lib.Product.create(name="FORGE White-Label Access")
        price = stripe_lib.Price.create(
            product=product.id,
            unit_amount=WHITELABEL_PRICE_USD * 100,
            currency="usd",
            recurring={"interval": "month"},
        )
        base_url = request.host_url.rstrip("/")
        checkout_session = stripe_lib.checkout.Session.create(
            line_items=[{"price": price.id, "quantity": 1}],
            mode="subscription",
            success_url=f"{base_url}/whitelabel/confirm?n={name}&e={email}&b={business_name}&c={accent_color}",
            cancel_url=f"{base_url}/whitelabel",
            customer_email=email,
            metadata={"name": name, "email": email, "business_name": business_name, "accent_color": accent_color},
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        log("whitelabel_register", "ERROR", str(e)[:200])
        return redirect("/whitelabel?msg=Payment+unavailable.+Please+try+again.")


@whitelabel_bp.route("/whitelabel/confirm", methods=["GET"])
def confirm():
    """
    Post-payment confirmation page. Provisions the reseller account.
    In simulation mode this is reached directly from /register.
    """
    name = request.args.get("n", "")
    email = request.args.get("e", "")
    business_name = request.args.get("b", "")
    accent_color = request.args.get("c", "#c9a84c")
    return _provision_reseller(name, email, business_name, accent_color, session_obj={})


def _provision_reseller(name: str, email: str, business_name: str, accent_color: str, session_obj: dict):
    """
    Create the reseller account, config file, CSV record, and send welcome email.

    Parameters:
        name (str): Reseller's personal name.
        email (str): Reseller's email.
        business_name (str): Their studio name.
        accent_color (str): CSS hex color.
        session_obj (dict): Stripe session object (may be empty in simulation).

    Returns:
        Flask response: Confirmation HTML page.
    """
    try:
        freelancer_id = str(uuid.uuid4())[:8]
        api_key = secrets.token_urlsafe(32)

        _create_reseller_config(freelancer_id, {
            "business_name": business_name,
            "email": email,
            "accent_color": accent_color,
        }, api_key)

        _append_client({
            "freelancer_id": freelancer_id,
            "name": name,
            "email": email,
            "business_name": business_name,
            "accent_color": accent_color,
            "api_key": api_key,
            "created_date": datetime.date.today().isoformat(),
            "stripe_customer_id": session_obj.get("customer", ""),
            "status": "active",
        })

        _send_welcome_email(email, business_name, api_key)
        log("whitelabel_provision", "SUCCESS", f"{business_name} | {email}")

        return render_template_string(_CONFIRM_HTML, business_name=business_name, api_key=api_key)

    except Exception as e:
        log("whitelabel_provision", "ERROR", traceback.format_exc()[:300])
        return redirect("/whitelabel?msg=Provisioning+error.+Contact+support.")


_CONFIRM_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Welcome — FORGE Reseller</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet"/>
  <style>
    body{margin:0;background:#0a0a0a;color:#f5f5f0;font-family:'DM Sans',sans-serif;
    display:flex;align-items:center;justify-content:center;min-height:100vh;}
    .card{background:#111;border:1px solid rgba(255,255,255,0.07);padding:52px;max-width:520px;width:100%;}
    .brand{font-family:'DM Serif Display',serif;font-size:1.2rem;color:#c9a84c;margin-bottom:28px;}
    h2{font-family:'DM Serif Display',serif;font-size:1.7rem;font-weight:400;margin-bottom:12px;}
    p{color:#8a8a8a;line-height:1.7;margin-bottom:16px;font-size:0.9rem;}
    .key-box{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);
             padding:14px 18px;font-family:monospace;font-size:0.85rem;word-break:break-all;
             color:#c9a84c;margin:20px 0;}
    a{color:#c9a84c;text-decoration:none;font-size:0.8rem;letter-spacing:0.06em;text-transform:uppercase;}
  </style>
</head>
<body>
  <div class="card">
    <div class="brand">Forge</div>
    <h2>Welcome, {{ business_name }}.</h2>
    <p>Your reseller account is active. Your API key has been sent to your email.</p>
    <p>Your API key:</p>
    <div class="key-box">{{ api_key }}</div>
    <p>Include this as the <code>X-TradeBuilt-Key</code> header on every API request.
    A full API guide has been sent to your email.</p>
    <a href="/">Return to homepage</a>
  </div>
</body>
</html>"""


# ─── ROUTES — API (RESELLER) ───────────────────────────────────────────────────

@whitelabel_bp.route("/api/whitelabel/scrape", methods=["POST"],
                     endpoint="wl_scrape")
def wl_scrape():
    """
    Trigger a lead scrape for the reseller.
    Body: {city, state, business_type}
    """
    client, err = _require_api_key()
    if err:
        return err

    try:
        data = request.get_json(force=True) or {}
        city = (data.get("city") or "").strip()
        state = (data.get("state") or "").strip()
        btype = (data.get("business_type") or "").strip()
        if not all([city, state, btype]):
            return jsonify({"error": "city, state, and business_type are required"}), 400

        import subprocess
        result = subprocess.run(
            ["python3", "scraper.py", "--city", city, "--state", state,
             "--type", btype, "--limit", "10"],
            cwd=BASE_DIR, capture_output=True, text=True, timeout=120,
        )
        log("wl_scrape", "SUCCESS", f"{client['freelancer_id']} | {city},{state} | {btype}")
        return jsonify({
            "status": "completed",
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "returncode": result.returncode,
        })
    except Exception as e:
        log("wl_scrape", "ERROR", str(e)[:200])
        return jsonify({"error": str(e)}), 500


@whitelabel_bp.route("/api/whitelabel/build", methods=["POST"],
                     endpoint="wl_build")
def wl_build():
    """
    Build a demo site for a lead.
    Body: {business_name, business_type, email, phone, city, state}
    """
    client, err = _require_api_key()
    if err:
        return err

    try:
        data = request.get_json(force=True) or {}
        business_name = (data.get("business_name") or "").strip()
        business_type = (data.get("business_type") or "").strip()
        if not business_name:
            return jsonify({"error": "business_name is required"}), 400

        import sys as _sys
        if BASE_DIR not in _sys.path:
            _sys.path.insert(0, BASE_DIR)
        from site_builder import build_site

        lead = {
            "business_name": business_name,
            "business_type": business_type,
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
            "city": data.get("city", ""),
            "state": data.get("state", ""),
            "google_rating": data.get("google_rating", ""),
            "review_count": data.get("review_count", ""),
            "website_url": data.get("website_url", ""),
            "lead_tier": data.get("lead_tier", "WARM"),
        }
        site_url = build_site(lead)
        log("wl_build", "SUCCESS", f"{client['freelancer_id']} | {business_name}")
        return jsonify({"status": "ok", "demo_url": site_url})
    except Exception as e:
        log("wl_build", "ERROR", traceback.format_exc()[:300])
        return jsonify({"error": str(e)}), 500


@whitelabel_bp.route("/api/whitelabel/send", methods=["POST"],
                     endpoint="wl_send")
def wl_send():
    """
    Send outreach email for a lead (reseller must configure their own Gmail).
    Body: {business_name, email, demo_url, gmail_sender, gmail_app_password}
    Note: FORGE does not send on the reseller's behalf; this validates the request
    and logs it. The reseller's own Gmail credentials are used.
    """
    client, err = _require_api_key()
    if err:
        return err

    try:
        data = request.get_json(force=True) or {}
        business_name = (data.get("business_name") or "").strip()
        to_email = (data.get("email") or "").strip()
        demo_url = (data.get("demo_url") or "").strip()
        sender = (data.get("gmail_sender") or "").strip()
        app_password = (data.get("gmail_app_password") or "").strip()

        if not all([business_name, to_email, demo_url, sender, app_password]):
            return jsonify({
                "error": "business_name, email, demo_url, gmail_sender, and gmail_app_password are required"
            }), 400

        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        subject = f"We built {business_name} a free website"
        config = _load_reseller_config(client["freelancer_id"])
        studio_name = config.get("business_name", "our studio")

        body = (
            f"Hi,\n\n"
            f"We built a free demo website for {business_name}.\n"
            f"Take a look: {demo_url}\n\n"
            f"If you want to claim it and start getting more calls, reply to this email.\n\n"
            f"-- {studio_name}"
        )
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_email
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender, app_password)
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()

        log("wl_send", "SUCCESS", f"{client['freelancer_id']} | {to_email}")
        return jsonify({"status": "sent", "to": to_email})

    except Exception as e:
        log("wl_send", "ERROR", str(e)[:200])
        return jsonify({"error": str(e)}), 500


def _load_reseller_config(freelancer_id: str) -> dict:
    """Load a reseller's config.json file."""
    config_path = os.path.join(WHITELABEL_DIR, freelancer_id, "config.json")
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}
