"""
platform/client_portal.py — FORGE Client Portal
Passwordless magic code authentication for paying clients.
Clients identified by email in conversions.csv.
"""

import os
import csv
import json
import random
import datetime
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, session, redirect, render_template_string, url_for
from dotenv import load_dotenv
from system_logger import log

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONVERSIONS_CSV = os.path.join(SCRIPT_DIR, "conversions.csv")
LEADS_CSV = os.path.join(SCRIPT_DIR, "leads.csv")

GMAIL_SENDER = os.getenv("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
MY_TEST_EMAIL = os.getenv("MY_TEST_EMAIL", "")
MY_PHONE = os.getenv("MY_PHONE", "")
TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"

CODE_TTL_MINUTES = 15

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")


# ─── DATA HELPERS ──────────────────────────────────────────────────────────────

def _read_conversions() -> list:
    """Read conversions.csv. Returns list of dicts."""
    if not os.path.exists(CONVERSIONS_CSV):
        return []
    with open(CONVERSIONS_CSV, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _find_conversion_by_email(email: str) -> dict:
    """
    Find the most recent conversion record for a given email.

    Parameters:
        email (str): Client email address.

    Returns:
        dict: Conversion record, or empty dict if not found.
    """
    email_lower = email.strip().lower()
    records = [r for r in _read_conversions() if r.get("email", "").strip().lower() == email_lower]
    if not records:
        return {}
    return records[-1]


def _find_lead_by_name(business_name: str) -> dict:
    """Find a lead in leads.csv by business_name."""
    if not os.path.exists(LEADS_CSV):
        return {}
    with open(LEADS_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("business_name", "").strip().lower() == business_name.strip().lower():
                return row
    return {}


def _send_magic_code(to_email: str, code: str):
    """
    Send the magic code to the client's email.

    Parameters:
        to_email (str): Recipient email.
        code (str): Six-digit code.
    """
    send_to = MY_TEST_EMAIL if TEST_MODE else to_email
    subject = f"Your FORGE login code: {code}"
    body = (
        f"Your login code is: {code}\n\n"
        f"This code expires in {CODE_TTL_MINUTES} minutes.\n\n"
        f"If you did not request this, ignore this email.\n\n"
        f"-- Forge Web Studio"
    )
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_SENDER
        msg["To"] = send_to
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, send_to, msg.as_string())
        server.quit()
        log("magic_code", "SUCCESS", f"Code sent to {send_to}")
    except Exception as e:
        log("magic_code", "ERROR", str(e))


def _append_change_request(email: str, message: str):
    """Send a change request email to admin."""
    subject = f"FORGE: Change request from {email}"
    body = f"Client: {email}\n\nRequest:\n{message}\n"
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_SENDER
        msg["To"] = MY_TEST_EMAIL
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, MY_TEST_EMAIL, msg.as_string())
        server.quit()
        log("change_request", "SUCCESS", f"From {email}")
    except Exception as e:
        log("change_request", "ERROR", str(e))


# ─── TEMPLATES ─────────────────────────────────────────────────────────────────

_BASE_STYLE = """
<style>
  *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'DM Sans',system-ui,sans-serif; background:#0a0a0a; color:#f5f5f0; min-height:100vh; display:flex; align-items:center; justify-content:center; padding:24px; }
  .card { background:#111; border:1px solid rgba(255,255,255,0.07); padding:48px; max-width:480px; width:100%; }
  .brand { font-size:1.1rem; color:#c9a84c; margin-bottom:8px; font-family:'DM Serif Display',serif; }
  .brand-sub { font-size:0.68rem; letter-spacing:0.18em; text-transform:uppercase; color:#8a8a8a; margin-bottom:32px; display:block; }
  h2 { font-size:1.3rem; margin-bottom:8px; font-family:'DM Serif Display',serif; font-weight:400; }
  p.sub { color:#8a8a8a; font-size:0.9rem; margin-bottom:28px; line-height:1.6; }
  label { display:block; font-size:0.65rem; letter-spacing:0.14em; text-transform:uppercase; color:#8a8a8a; margin-bottom:6px; }
  input, textarea { width:100%; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); color:#f5f5f0; padding:13px 16px; font-family:'DM Sans',sans-serif; font-size:0.9rem; box-sizing:border-box; }
  input:focus, textarea:focus { outline:none; border-color:#c9a84c; }
  button, .btn { width:100%; background:#c9a84c; color:#0a0a0a; border:none; padding:15px; font-family:'DM Sans',sans-serif; font-size:0.78rem; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; cursor:pointer; margin-top:20px; display:block; text-align:center; text-decoration:none; }
  button:hover, .btn:hover { opacity:0.84; }
  .alert { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); padding:12px 16px; font-size:0.85rem; margin-bottom:20px; color:#8a8a8a; }
</style>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet"/>
"""

_EMAIL_FORM = _BASE_STYLE + """
<div class="card">
  <div class="brand">Forge</div>
  <span class="brand-sub">Client Portal</span>
  <h2>Sign In</h2>
  <p class="sub">Enter the email address on your account and we will send you a login code.</p>
  {% if message %}<div class="alert">{{ message }}</div>{% endif %}
  <form method="POST" action="/portal/request-code">
    <div style="margin-bottom:16px;">
      <label>Email Address</label>
      <input type="email" name="email" placeholder="you@example.com" required/>
    </div>
    <button type="submit">Send Login Code</button>
  </form>
</div>
"""

_VERIFY_FORM = _BASE_STYLE + """
<div class="card">
  <div class="brand">Forge</div>
  <span class="brand-sub">Client Portal</span>
  <h2>Enter Your Code</h2>
  <p class="sub">We sent a 6-digit code to your email. It expires in {{ ttl }} minutes.</p>
  {% if message %}<div class="alert">{{ message }}</div>{% endif %}
  <form method="POST" action="/portal/verify">
    <div style="margin-bottom:16px;">
      <label>Login Code</label>
      <input type="text" name="code" placeholder="000000" maxlength="6" pattern="[0-9]{6}" inputmode="numeric" required/>
    </div>
    <button type="submit">Verify Code</button>
  </form>
</div>
"""

_DASHBOARD_HTML = _BASE_STYLE + """
<style>
  body { align-items:flex-start; padding:48px 24px; }
  .dashboard { max-width:800px; width:100%; margin:0 auto; }
  .top-bar { display:flex; justify-content:space-between; align-items:center; margin-bottom:40px; padding-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.07); }
  .section-label { font-size:0.65rem; letter-spacing:0.18em; text-transform:uppercase; color:#8a8a8a; margin-bottom:8px; display:block; }
  .section-value { font-size:1.05rem; }
  .metric-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; margin-bottom:36px; }
  .metric { background:#111; border:1px solid rgba(255,255,255,0.07); padding:24px; }
  .metric-num { font-family:'DM Serif Display',serif; font-size:2.2rem; color:#c9a84c; }
  .metric-label { font-size:0.72rem; color:#8a8a8a; margin-top:4px; letter-spacing:0.1em; text-transform:uppercase; }
  .block { background:#111; border:1px solid rgba(255,255,255,0.07); padding:28px; margin-bottom:20px; }
  .block h3 { font-family:'DM Serif Display',serif; font-weight:400; font-size:1.1rem; margin-bottom:16px; }
  .timeline-item { padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05); font-size:0.88rem; color:#8a8a8a; display:flex; gap:16px; }
  .timeline-date { color:#c9a84c; white-space:nowrap; font-size:0.78rem; }
  textarea { height:90px; resize:vertical; }
  .sign-out { font-size:0.75rem; color:#8a8a8a; text-decoration:none; }
  .sign-out:hover { color:#f5f5f0; }
  a.demo-link { color:#c9a84c; text-decoration:none; font-size:0.88rem; }
  a.demo-link:hover { text-decoration:underline; }
</style>
<div class="dashboard">
  <div class="top-bar">
    <div class="brand">Forge</div>
    <a href="/portal/signout" class="sign-out">Sign out</a>
  </div>
  <h2 style="margin-bottom:28px; font-family:'DM Serif Display',serif; font-weight:400; font-size:1.6rem;">{{ business_name }}</h2>
  <div class="metric-grid">
    <div class="metric">
      <div class="metric-num">{{ plan_name }}</div>
      <div class="metric-label">Current Plan</div>
    </div>
    <div class="metric">
      <div class="metric-num">${{ amount }}</div>
      <div class="metric-label">{{ billing_label }}</div>
    </div>
    <div class="metric">
      <div class="metric-num">{{ demo_views }}</div>
      <div class="metric-label">Demo Page Views</div>
    </div>
  </div>
  {% if demo_url %}
  <div class="block">
    <h3>Your Site</h3>
    <a href="{{ demo_url }}" class="demo-link" target="_blank" rel="noopener">{{ demo_url }}</a>
  </div>
  {% endif %}
  <div class="block">
    <h3>Request a Change</h3>
    <form method="POST" action="/portal/change-request">
      <div style="margin-bottom:14px;">
        <label>Describe what you would like updated</label>
        <textarea name="message" placeholder="I would like to update my phone number..." required></textarea>
      </div>
      <button type="submit" style="width:auto;padding:12px 32px;">Submit Request</button>
    </form>
  </div>
  <div class="block">
    <h3>Account Timeline</h3>
    {% for item in timeline %}
    <div class="timeline-item">
      <span class="timeline-date">{{ item.date }}</span>
      <span>{{ item.event }}</span>
    </div>
    {% endfor %}
    {% if not timeline %}<p style="color:#8a8a8a;font-size:0.88rem;">No events yet.</p>{% endif %}
  </div>
</div>
"""


# ─── ROUTES ────────────────────────────────────────────────────────────────────

@portal_bp.route("/", methods=["GET"])
def portal_home():
    """Render the email input form."""
    return render_template_string(_EMAIL_FORM, message=request.args.get("msg", ""))


@portal_bp.route("/request-code", methods=["POST"])
def request_code():
    """
    Accept email, verify it's in conversions.csv, generate and send magic code.
    """
    email = request.form.get("email", "").strip().lower()
    if not email:
        return redirect(url_for("portal.portal_home", msg="Please enter an email address."))

    record = _find_conversion_by_email(email)
    if not record:
        return render_template_string(_EMAIL_FORM, message="No account found for that email address.")

    code = str(random.randint(100000, 999999))
    expires_at = (datetime.datetime.now() + datetime.timedelta(minutes=CODE_TTL_MINUTES)).isoformat()

    session["magic_code"] = code
    session["magic_email"] = email
    session["magic_expires_at"] = expires_at

    _send_magic_code(email, code)
    log("portal_request_code", "INFO", f"Code sent for {email}")
    return redirect(url_for("portal.verify_form"))


@portal_bp.route("/verify", methods=["GET"])
def verify_form():
    """Render the code input form."""
    return render_template_string(_VERIFY_FORM, message=request.args.get("msg", ""), ttl=CODE_TTL_MINUTES)


@portal_bp.route("/verify", methods=["POST"])
def verify_code():
    """
    Validate submitted code against session. Set authenticated flag on success.
    """
    submitted = request.form.get("code", "").strip()
    stored_code = session.get("magic_code", "")
    stored_email = session.get("magic_email", "")
    expires_at_str = session.get("magic_expires_at", "")

    if not stored_code or not stored_email:
        session.clear()
        return redirect(url_for("portal.portal_home", msg="Session expired. Please request a new code."))

    try:
        expires_at = datetime.datetime.fromisoformat(expires_at_str)
        if datetime.datetime.now() > expires_at:
            session.clear()
            return redirect(url_for("portal.portal_home", msg="Code expired. Request a new one."))
    except Exception:
        session.clear()
        return redirect(url_for("portal.portal_home", msg="Code expired. Request a new one."))

    if submitted != stored_code:
        session.clear()
        return redirect(url_for("portal.portal_home", msg="Invalid code. Request a new one."))

    session["authenticated"] = True
    session["client_email"] = stored_email
    session.pop("magic_code", None)
    session.pop("magic_expires_at", None)
    log("portal_auth", "SUCCESS", f"Authenticated {stored_email}")
    return redirect(url_for("portal.dashboard"))


@portal_bp.route("/dashboard", methods=["GET"])
def dashboard():
    """
    Client dashboard. Requires authentication.
    """
    if not session.get("authenticated"):
        return redirect(url_for("portal.portal_home", msg="Please sign in to access your account."))

    email = session.get("client_email", "")
    record = _find_conversion_by_email(email)
    if not record:
        session.clear()
        return redirect(url_for("portal.portal_home", msg="Account not found. Please sign in again."))

    business_name = record.get("business_name", "")
    tier = record.get("tier", "")
    amount = record.get("amount", "")
    converted_date = record.get("date", "")

    plan_labels = {"starter": "Starter", "growth": "Growth", "autopilot": "Autopilot"}
    billing_labels = {"starter": "one-time", "growth": "per month", "autopilot": "per month"}
    plan_name = plan_labels.get(tier, tier.title())
    billing_label = billing_labels.get(tier, "")

    lead = _find_lead_by_name(business_name)
    demo_url = lead.get("demo_site_path", "") or ""

    # Demo views from SQLite if available
    demo_views = 0
    try:
        import sqlite3
        db_path = os.path.join(SCRIPT_DIR, "forge.db")
        if os.path.exists(db_path):
            import re
            slug = re.sub(r'[^a-z0-9-]', '', business_name.lower().replace(" ", "-").replace("'", "").replace(",", ""))
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM demo_visits WHERE slug=?", (slug,))
            demo_views = cursor.fetchone()[0]
            conn.close()
    except Exception:
        pass

    # Timeline
    timeline = []
    scraped_date = lead.get("date_scraped", "")
    if scraped_date:
        timeline.append({"date": scraped_date, "event": "Lead identified and site built"})
    email_sent_date = lead.get("email_sent_date", "")
    if email_sent_date:
        timeline.append({"date": email_sent_date, "event": "Outreach email sent"})
    if converted_date:
        timeline.append({"date": converted_date, "event": f"Converted to {plan_name} plan"})

    return render_template_string(
        _DASHBOARD_HTML,
        business_name=business_name,
        plan_name=plan_name,
        amount=amount,
        billing_label=billing_label,
        demo_views=demo_views,
        demo_url=demo_url,
        timeline=sorted(timeline, key=lambda x: x["date"]),
    )


@portal_bp.route("/change-request", methods=["POST"])
def change_request():
    """Submit a change request from the client dashboard."""
    if not session.get("authenticated"):
        return redirect(url_for("portal.portal_home"))

    email = session.get("client_email", "")
    message = request.form.get("message", "").strip()
    if message and email:
        try:
            _append_change_request(email, message)
        except Exception as e:
            log("change_request", "ERROR", str(e))

    return redirect(url_for("portal.dashboard"))


@portal_bp.route("/signout", methods=["GET"])
def signout():
    """Clear session and redirect to portal home."""
    session.clear()
    return redirect(url_for("portal.portal_home"))
