"""
Stripe webhook + conversion handler (extracted from legacy Flask platform, Phase 5).
"""

import csv
import datetime
import json
import os
import re
import traceback

from config import settings
from mail.sender import send_message
from system_logger import log

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS_CSV = os.path.join(SCRIPT_DIR, "leads.csv")
CONVERSIONS_CSV = os.path.join(SCRIPT_DIR, "conversions.csv")
NOTIFICATIONS_FILE = os.path.join(SCRIPT_DIR, "notifications.json")

PLAN_DEFINITIONS = {
    "starter": {"name": "Starter", "amount": 200, "type": "one_time", "label": "One-time"},
    "growth": {"name": "Growth", "amount": 500, "type": "recurring", "label": "per month"},
    "autopilot": {"name": "Autopilot", "amount": 800, "type": "recurring", "label": "per month"},
}


def _read_leads() -> tuple:
    if not os.path.exists(LEADS_CSV):
        return [], []
    with open(LEADS_CSV, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    return rows, fieldnames


def _write_leads(rows: list, fieldnames: list) -> None:
    with open(LEADS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _append_conversion(data: dict) -> None:
    fieldnames = [
        "date", "business_name", "email", "tier", "amount",
        "stripe_session_id", "stripe_customer_id",
    ]
    file_exists = os.path.exists(CONVERSIONS_CSV)
    with open(CONVERSIONS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: data.get(k, "") for k in fieldnames})


def _push_notification(message: str, level: str = "info") -> None:
    items = []
    if os.path.exists(NOTIFICATIONS_FILE):
        try:
            with open(NOTIFICATIONS_FILE, "r") as f:
                items = json.load(f)
        except Exception:
            items = []
    items.append({"ts": datetime.datetime.now().isoformat(), "message": message, "level": level})
    with open(NOTIFICATIONS_FILE, "w") as f:
        json.dump(items[-10:], f, indent=2)


def _send_internal_email(subject: str, body: str) -> None:
    to = settings.my_test_email.strip()
    if not to:
        return
    try:
        send_message(to=to, subject=subject, html=f"<pre>{body}</pre>", plain=body)
    except Exception as e:
        log("stripe_email", "ERROR", str(e))


def _handle_conversion_postgres(slug: str, tier: str, session: dict) -> tuple:
    from repositories import leads_repo

    plan_def = PLAN_DEFINITIONS.get(tier, {})
    amount = plan_def.get("amount", 0)
    customer_id = session.get("customer", "")

    updated, business_name, business_email = leads_repo.update_by_slug(slug, {
        "status": "won",
        "notes": (
            f"Converted: {tier} (${amount}) | "
            f"stripe_customer={customer_id} | session={session.get('id', '')}"
        ),
    })
    return updated, business_name, business_email, amount


def handle_conversion(slug: str, tier: str, session: dict) -> None:
    """Post-payment conversion — updates leads storage and logs conversion."""
    try:
        from storage import use_postgres

        if use_postgres():
            updated, business_name, business_email, amount = _handle_conversion_postgres(
                slug, tier, session
            )
            if not updated:
                log("handle_conversion", "WARN", f"no postgres lead for slug={slug}")
            subject = f"FORGE: New client — {business_name} — {tier} — ${amount}"
            body = (
                f"New conversion\n\nBusiness: {business_name}\nEmail: {business_email}\n"
                f"Plan: {tier}\nAmount: ${amount}\nSession: {session.get('id', '')}\n"
            )
            _send_internal_email(subject, body)
            _push_notification(f"New client: {business_name} — {tier} — ${amount}", level="info")
            log("handle_conversion", "SUCCESS", f"{business_name} | {tier} | ${amount}")
            return

        rows, fieldnames = _read_leads()
        extra_cols = ["converted", "converted_date", "stripe_customer_id", "plan_tier"]
        for col in extra_cols:
            if col not in fieldnames:
                fieldnames.append(col)

        updated = False
        business_name = ""
        business_email = ""

        for row in rows:
            name = row.get("business_name", "")
            row_slug = re.sub(
                r"[^a-z0-9-]", "", name.lower().replace(" ", "-").replace("'", "").replace(",", "")
            )
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
            f"New conversion\n\nBusiness: {business_name}\nEmail: {business_email}\n"
            f"Plan: {tier}\nAmount: ${amount}\nSession: {session.get('id', '')}\n"
        )
        _send_internal_email(subject, body)
        _push_notification(f"New client: {business_name} — {tier} — ${amount}", level="info")
        log("handle_conversion", "SUCCESS", f"{business_name} | {tier} | ${amount}")

    except Exception:
        log("handle_conversion", "ERROR", f"slug={slug} tier={tier} | {traceback.format_exc()[:300]}")


def process_stripe_webhook(payload: bytes, sig_header: str) -> tuple:
    """Verify Stripe signature and process checkout.session.completed."""
    try:
        import stripe as stripe_lib
        stripe_lib.api_key = settings.stripe_secret_key
        event = stripe_lib.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except Exception as e:
        log("webhook_stripe", "ERROR", f"Signature verification failed: {e}")
        return 400, "Invalid signature"

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
    except Exception:
        log("webhook_stripe", "ERROR", f"handle_conversion failed: {traceback.format_exc()[:400]}")

    return 200, "OK"