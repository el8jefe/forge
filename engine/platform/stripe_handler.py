"""
platform/stripe_handler.py — FORGE Stripe Checkout Handler
Supports simulation mode when STRIPE_SECRET_KEY is a placeholder.
Real mode: creates Checkout Sessions and verifies webhook signatures.
"""

import os
import csv
import json
import hashlib
import datetime
import traceback
from flask import Blueprint, request, redirect, render_template_string, jsonify, Response
from dotenv import load_dotenv
from system_logger import log

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS_CSV = os.path.join(SCRIPT_DIR, "leads.csv")
CONVERSIONS_CSV = os.path.join(SCRIPT_DIR, "conversions.csv")
PRODUCTS_FILE = os.path.join(SCRIPT_DIR, "stripe_products.json")
NOTIFICATIONS_FILE = os.path.join(SCRIPT_DIR, "notifications.json")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_placeholder")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")
GMAIL_SENDER = os.getenv("GMAIL_SENDER", "")
MY_TEST_EMAIL = os.getenv("MY_TEST_EMAIL", "")

SIMULATION_MODE = STRIPE_SECRET_KEY.startswith("sk_test_placeholder")

PLAN_DEFINITIONS = {
    "starter": {"name": "Starter", "amount": 200, "type": "one_time", "label": "One-time"},
    "growth": {"name": "Growth", "amount": 500, "type": "recurring", "label": "per month"},
    "autopilot": {"name": "Autopilot", "amount": 800, "type": "recurring", "label": "per month"},
}

stripe_bp = Blueprint("stripe", __name__)


# ─── STRIPE PRODUCT INITIALIZATION ────────────────────────────────────────────

def _load_products() -> dict:
    """Load stripe_products.json if it exists and is complete."""
    if not os.path.exists(PRODUCTS_FILE):
        return {}
    try:
        with open(PRODUCTS_FILE, "r") as f:
            data = json.load(f)
        if all(k in data and data[k].get("price_id") for k in PLAN_DEFINITIONS):
            return data
    except Exception:
        pass
    return {}


def _save_products(data: dict):
    """Write stripe_products.json atomically."""
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def ensure_stripe_products() -> dict:
    """
    Check stripe_products.json for all three price IDs.
    If any are missing, create via Stripe API and save.
    In simulation mode, creates placeholder IDs.

    Returns:
        dict: Products dict with price_ids for each plan.
    """
    existing = _load_products()
    if existing:
        return existing

    if SIMULATION_MODE:
        products = {
            tier: {
                "product_id": f"prod_sim_{tier}",
                "price_id": f"price_sim_{tier}",
                "amount": PLAN_DEFINITIONS[tier]["amount"],
                "type": PLAN_DEFINITIONS[tier]["type"],
            }
            for tier in PLAN_DEFINITIONS
        }
        _save_products(products)
        log("stripe_products", "INFO", "Simulation mode — using placeholder product IDs")
        return products

    try:
        import stripe as stripe_lib
        stripe_lib.api_key = STRIPE_SECRET_KEY
        products = {}
        for tier, defn in PLAN_DEFINITIONS.items():
            product = stripe_lib.Product.create(name=f"FORGE {defn['name']}")
            if defn["type"] == "one_time":
                price = stripe_lib.Price.create(
                    product=product.id,
                    unit_amount=defn["amount"] * 100,
                    currency="usd",
                )
            else:
                price = stripe_lib.Price.create(
                    product=product.id,
                    unit_amount=defn["amount"] * 100,
                    currency="usd",
                    recurring={"interval": "month"},
                )
            products[tier] = {
                "product_id": product.id,
                "price_id": price.id,
                "amount": defn["amount"],
                "type": defn["type"],
            }
        _save_products(products)
        log("stripe_products", "SUCCESS", "Created all three Stripe products")
        return products
    except Exception as e:
        log("stripe_products", "ERROR", str(e))
        return {}


# ─── CSV HELPERS ───────────────────────────────────────────────────────────────

def _read_leads() -> tuple:
    """Read leads.csv, return (rows, fieldnames)."""
    if not os.path.exists(LEADS_CSV):
        return [], []
    with open(LEADS_CSV, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    return rows, fieldnames


def _write_leads(rows: list, fieldnames: list):
    """Write leads.csv atomically."""
    with open(LEADS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _find_lead_by_slug(slug: str) -> dict:
    """
    Find a lead in leads.csv by slug match.
    Slug is derived from business_name: lowercase, spaces to dashes, non-alphanum removed.

    Parameters:
        slug (str): URL slug.

    Returns:
        dict: Lead row, or empty dict if not found.
    """
    rows, _ = _read_leads()
    import re
    for row in rows:
        name = row.get("business_name", "")
        row_slug = re.sub(r'[^a-z0-9-]', '', name.lower().replace(" ", "-").replace("'", "").replace(",", ""))
        if row_slug == slug:
            return row
    return {}


def _append_conversion(data: dict):
    """Append a row to conversions.csv. Creates the file with headers if missing."""
    fieldnames = ["date", "business_name", "email", "tier", "amount", "stripe_session_id", "stripe_customer_id"]
    file_exists = os.path.exists(CONVERSIONS_CSV)
    with open(CONVERSIONS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: data.get(k, "") for k in fieldnames})


def _push_notification(message: str, level: str = "info"):
    """Append a notification to notifications.json."""
    items = []
    if os.path.exists(NOTIFICATIONS_FILE):
        try:
            with open(NOTIFICATIONS_FILE, "r") as f:
                items = json.load(f)
        except Exception:
            items = []
    items.append({"ts": datetime.datetime.now().isoformat(), "message": message, "level": level})
    items = items[-10:]
    with open(NOTIFICATIONS_FILE, "w") as f:
        json.dump(items, f, indent=2)


def _send_internal_email(subject: str, body: str):
    """Send a plain-text internal notification email."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    app_password = os.getenv("GMAIL_APP_PASSWORD", "")
    if not app_password or not GMAIL_SENDER or not MY_TEST_EMAIL:
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_SENDER
        msg["To"] = MY_TEST_EMAIL
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_SENDER, app_password)
        server.sendmail(GMAIL_SENDER, MY_TEST_EMAIL, msg.as_string())
        server.quit()
    except Exception as e:
        log("stripe_email", "ERROR", str(e))


# ─── CONVERSION HANDLER ────────────────────────────────────────────────────────

def handle_conversion(slug: str, tier: str, session: dict):
    """
    Post-payment conversion handler. Updates leads.csv, writes conversions.csv,
    sends internal notification, pushes dashboard notification.

    Parameters:
        slug (str): Business slug from Stripe metadata.
        tier (str): Plan tier from Stripe metadata.
        session (dict): Stripe Checkout Session object or simulation dict.
    """
    try:
        rows, fieldnames = _read_leads()

        # Ensure conversion columns exist
        extra_cols = ["converted", "converted_date", "stripe_customer_id", "plan_tier"]
        for col in extra_cols:
            if col not in fieldnames:
                fieldnames.append(col)

        import re
        updated = False
        business_name = ""
        business_email = ""

        for row in rows:
            name = row.get("business_name", "")
            row_slug = re.sub(r'[^a-z0-9-]', '', name.lower().replace(" ", "-").replace("'", "").replace(",", ""))
            if row_slug == slug:
                row.setdefault("converted", "false")
                row.setdefault("converted_date", "")
                row.setdefault("stripe_customer_id", "")
                row.setdefault("plan_tier", "")
                row["converted"] = "true"
                row["converted_date"] = datetime.date.today().isoformat()
                row["stripe_customer_id"] = session.get("customer", "")
                row["plan_tier"] = tier
                business_name = name
                business_email = row.get("email", "")
                updated = True

        if updated:
            _write_leads(rows, fieldnames)

        plan_def = PLAN_DEFINITIONS.get(tier, {})
        amount = plan_def.get("amount", 0)

        _append_conversion({
            "date": datetime.date.today().isoformat(),
            "business_name": business_name,
            "email": business_email,
            "tier": tier,
            "amount": amount,
            "stripe_session_id": session.get("id", ""),
            "stripe_customer_id": session.get("customer", ""),
        })

        subject = f"FORGE: New client — {business_name} — {tier} — ${amount}"
        body = (
            f"New conversion\n\n"
            f"Business: {business_name}\n"
            f"Email: {business_email}\n"
            f"Plan: {tier}\n"
            f"Amount: ${amount}\n"
            f"Session: {session.get('id', '')}\n"
            f"Customer: {session.get('customer', '')}\n"
            f"Date: {datetime.datetime.now().isoformat()}\n"
        )
        _send_internal_email(subject, body)
        _push_notification(f"New client: {business_name} — {tier} — ${amount}", level="info")
        log("handle_conversion", "SUCCESS", f"{business_name} | {tier} | ${amount}")

    except Exception as e:
        log("handle_conversion", "ERROR", f"slug={slug} tier={tier} | {traceback.format_exc()[:300]}")


# ─── SIMULATION CHECKOUT PAGE ──────────────────────────────────────────────────

_SIM_CHECKOUT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>FORGE Checkout — Simulation</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet"/>
  <style>
    body { margin:0; background:#0a0a0a; color:#f5f5f0; font-family:'DM Sans',sans-serif; display:flex; align-items:center; justify-content:center; min-height:100vh; }
    .card { background:#111; border:1px solid rgba(255,255,255,0.07); padding:48px; max-width:440px; width:100%; }
    .brand { font-size:1.1rem; color:#c9a84c; margin-bottom:8px; }
    .sim-badge { font-size:0.65rem; letter-spacing:0.15em; text-transform:uppercase; color:#8a8a8a; border:1px solid rgba(255,255,255,0.1); padding:3px 8px; display:inline-block; margin-bottom:28px; }
    h2 { font-size:1.4rem; margin-bottom:4px; }
    .price { font-size:2.4rem; color:#c9a84c; margin:16px 0 28px; }
    .price span { font-size:0.85rem; color:#8a8a8a; }
    .field-group { margin-bottom:16px; }
    label { display:block; font-size:0.68rem; letter-spacing:0.14em; text-transform:uppercase; color:#8a8a8a; margin-bottom:6px; }
    input { width:100%; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); color:#f5f5f0; padding:12px 14px; font-family:'DM Sans',sans-serif; font-size:0.9rem; box-sizing:border-box; }
    input:focus { outline:none; border-color:#c9a84c; }
    .row { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
    button { width:100%; background:#c9a84c; color:#0a0a0a; border:none; padding:15px; font-family:'DM Sans',sans-serif; font-size:0.82rem; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; cursor:pointer; margin-top:24px; }
    button:hover { opacity:0.88; }
    .note { font-size:0.72rem; color:#8a8a8a; margin-top:14px; text-align:center; }
  </style>
</head>
<body>
  <div class="card">
    <div class="brand">Forge</div>
    <div class="sim-badge">Simulation Mode</div>
    <h2>{{ plan_name }}</h2>
    <div class="price">${{ amount }} <span>{{ billing_label }}</span></div>
    <form method="POST" action="/webhook/stripe/simulate">
      <input type="hidden" name="slug" value="{{ slug }}"/>
      <input type="hidden" name="tier" value="{{ tier }}"/>
      <div class="field-group">
        <label>Email</label>
        <input type="email" name="email" placeholder="you@example.com" required/>
      </div>
      <div class="field-group">
        <label>Card Number</label>
        <input type="text" placeholder="4242 4242 4242 4242" maxlength="19"/>
      </div>
      <div class="row">
        <div class="field-group">
          <label>Expiry</label>
          <input type="text" placeholder="MM / YY" maxlength="7"/>
        </div>
        <div class="field-group">
          <label>CVC</label>
          <input type="text" placeholder="123" maxlength="4"/>
        </div>
      </div>
      <button type="submit">Complete Purchase</button>
    </form>
    <p class="note">This is a simulation. No real payment is processed.</p>
  </div>
</body>
</html>"""


# ─── ROUTES ────────────────────────────────────────────────────────────────────

@stripe_bp.route("/checkout/<tier>/<slug>", methods=["GET"])
def checkout(tier: str, slug: str):
    """
    Initiate checkout for a lead and plan tier.
    Simulation mode renders a fake checkout form.
    Live mode creates a Stripe Checkout Session and redirects.

    Parameters:
        tier (str): One of starter, growth, autopilot.
        slug (str): Business slug.
    """
    if tier not in PLAN_DEFINITIONS:
        return jsonify({"error": "Invalid tier. Must be starter, growth, or autopilot."}), 400

    plan = PLAN_DEFINITIONS[tier]
    lead = _find_lead_by_slug(slug)

    if SIMULATION_MODE:
        billing_label = "one-time" if plan["type"] == "one_time" else "/ month"
        return render_template_string(
            _SIM_CHECKOUT_HTML,
            plan_name=plan["name"],
            amount=plan["amount"],
            billing_label=billing_label,
            slug=slug,
            tier=tier,
        )

    # Live Stripe mode
    try:
        import stripe as stripe_lib
        stripe_lib.api_key = STRIPE_SECRET_KEY
        products = ensure_stripe_products()
        price_id = products.get(tier, {}).get("price_id")
        if not price_id:
            log("checkout", "ERROR", f"No price_id for tier {tier}")
            return jsonify({"error": "Plan configuration error."}), 500

        base_url = request.host_url.rstrip("/")
        session = stripe_lib.checkout.Session.create(
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment" if plan["type"] == "one_time" else "subscription",
            success_url=f"{base_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/demo/{slug}",
            customer_email=lead.get("email") or None,
            metadata={"slug": slug, "tier": tier},
        )
        return redirect(session.url, code=303)

    except Exception as e:
        log("checkout", "ERROR", str(e))
        return jsonify({"error": "Checkout unavailable. Please try again."}), 500


@stripe_bp.route("/webhook/stripe/simulate", methods=["POST"])
def webhook_simulate():
    """
    Simulation webhook endpoint. Processes the fake checkout form submission
    using the same handle_conversion logic as the real webhook.
    """
    slug = request.form.get("slug", "")
    tier = request.form.get("tier", "")
    email = request.form.get("email", "")

    if not slug or not tier or tier not in PLAN_DEFINITIONS:
        return jsonify({"error": "Invalid simulation parameters."}), 400

    fake_session = {
        "id": f"cs_sim_{hashlib.sha256(f'{slug}{tier}'.encode()).hexdigest()[:16]}",
        "customer": f"cus_sim_{hashlib.sha256(email.encode()).hexdigest()[:12]}",
        "customer_email": email,
    }

    try:
        handle_conversion(slug, tier, fake_session)
    except Exception as e:
        log("webhook_simulate", "ERROR", str(e))

    plan = PLAN_DEFINITIONS[tier]
    return render_template_string("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Payment Complete — FORGE</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet"/>
  <style>
    body { margin:0; background:#0a0a0a; color:#f5f5f0; font-family:'DM Sans',sans-serif; display:flex; align-items:center; justify-content:center; min-height:100vh; }
    .card { background:#111; border:1px solid rgba(255,255,255,0.07); padding:48px; max-width:440px; width:100%; text-align:center; }
    .brand { font-size:1.1rem; color:#c9a84c; margin-bottom:28px; }
    h2 { margin-bottom:12px; }
    p { color:#8a8a8a; font-size:0.95rem; line-height:1.7; }
    a { color:#c9a84c; text-decoration:none; }
  </style>
</head>
<body>
  <div class="card">
    <div class="brand">Forge</div>
    <h2>Welcome aboard.</h2>
    <p>Your {{ plan_name }} plan is active. We will be in touch within 24 hours to get started.</p>
    <p style="margin-top:24px;"><a href="/">Return to homepage</a></p>
  </div>
</body>
</html>""", plan_name=plan["name"])


@stripe_bp.route("/webhook/stripe", methods=["POST"])
def webhook_stripe():
    """
    Stripe webhook endpoint. Verifies signature and processes checkout.session.completed.
    Always returns HTTP 200 to Stripe after signature verification succeeds.
    """
    payload = request.get_data(as_text=False)
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        import stripe as stripe_lib
        stripe_lib.api_key = STRIPE_SECRET_KEY
        event = stripe_lib.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        log("webhook_stripe", "ERROR", f"Signature verification failed: {e}")
        return Response("Invalid signature", status=400)

    # Always return 200 after verification — Stripe expects this
    try:
        if event.get("type") == "checkout.session.completed":
            session = event["data"]["object"]
            metadata = session.get("metadata", {})
            slug = metadata.get("slug", "")
            tier = metadata.get("tier", "")
            if slug and tier:
                handle_conversion(slug, tier, session)
            else:
                log("webhook_stripe", "WARN", f"Missing metadata in session {session.get('id', '')}")
    except Exception as e:
        log("webhook_stripe", "ERROR", f"handle_conversion failed: {traceback.format_exc()[:400]}")

    return Response("OK", status=200)


@stripe_bp.route("/success", methods=["GET"])
def success():
    """Post-payment success page."""
    return render_template_string("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Payment Complete — FORGE</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet"/>
  <style>
    body { margin:0; background:#0a0a0a; color:#f5f5f0; font-family:'DM Sans',sans-serif; display:flex; align-items:center; justify-content:center; min-height:100vh; }
    .card { background:#111; border:1px solid rgba(255,255,255,0.07); padding:56px; max-width:480px; width:100%; text-align:center; }
    .brand { font-family:'DM Serif Display',serif; font-size:1.4rem; color:#c9a84c; margin-bottom:32px; }
    h2 { font-family:'DM Serif Display',serif; font-size:1.8rem; font-weight:400; margin-bottom:16px; }
    p { color:#8a8a8a; font-size:0.95rem; line-height:1.75; }
    a { display:inline-block; margin-top:28px; color:#c9a84c; text-decoration:none; font-size:0.8rem; letter-spacing:0.08em; text-transform:uppercase; }
  </style>
</head>
<body>
  <div class="card">
    <div class="brand">Forge</div>
    <h2>Welcome aboard.</h2>
    <p>Your plan is active. We will reach out within 24 hours to get your site live.</p>
    <a href="/">Return to homepage</a>
  </div>
</body>
</html>""")
