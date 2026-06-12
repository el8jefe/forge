"""
followup.py — FORGE 3-Day Follow-Up Sender (Phase 5)
Uses storage layer + Resend/Gmail mail.sender.
"""

import csv
import datetime
import os
import random
import time

from dotenv import load_dotenv
from system_logger import log

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_CSV = os.path.join(SCRIPT_DIR, "log.csv")
FOLLOWUP_LOG = os.path.join(SCRIPT_DIR, "followup_log.csv")

MY_TEST_EMAIL = os.getenv("MY_TEST_EMAIL", "juanparinconr@gmail.com")
MY_PHONE = os.getenv("MY_PHONE", "(203) 609-4807")
TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"
GMAIL_SENDER = os.getenv("GMAIL_SENDER", "")


def _build_followup_bodies(lead_name: str, demo_url: str) -> tuple:
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:32px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:4px;overflow:hidden;max-width:600px;width:100%;">
      <tr><td style="background:#0f0f0f;padding:28px 40px;">
        <span style="font-size:22px;font-weight:bold;color:#c9a84c;font-family:Georgia,serif;">Forge</span>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="font-size:16px;color:#222;margin:0 0 20px;">Hey <strong>{lead_name}</strong>,</p>
        <p style="font-size:15px;color:#444;line-height:1.7;margin:0 0 20px;">
          I sent you a note a few days ago — I built a free website mockup for your business
          and wanted to make sure you had a chance to see it.
        </p>
        <table cellpadding="0" cellspacing="0" width="100%" style="margin:28px 0;">
          <tr><td align="center">
            <a href="{demo_url}" style="display:inline-block;background:#FFD700;color:#000;padding:16px 40px;text-decoration:none;font-weight:bold;font-size:15px;border-radius:3px;">
              View Your Free Site &rarr;
            </a>
          </td></tr>
        </table>
        <p style="font-size:15px;color:#444;line-height:1.7;margin:0 0 28px;">
          If you&rsquo;re not interested, no worries — just reply and let me know.
          But if you want to chat, hit reply or call/text me at {MY_PHONE}.
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""
    plain = (
        f"Hey {lead_name},\n\n"
        f"I sent you a note a few days ago about a free website mockup I built for your business.\n\n"
        f"View it here: {demo_url}\n\n"
        f"- Juan Pablo Rincon Rios\nFounder, Forge | {MY_PHONE}\n\nReply STOP to opt out."
    )
    return html, plain


def send_followup(lead_name: str, email: str, demo_url: str) -> bool:
    to_address = MY_TEST_EMAIL if TEST_MODE else email
    if TEST_MODE:
        print(f"  TEST MODE — routing follow-up for {lead_name} → {MY_TEST_EMAIL}")

    html, plain = _build_followup_bodies(lead_name, demo_url)
    subject = "Quick follow-up — did you see your free demo site?"

    try:
        from mail.sender import send_message
        ok, err = send_message(
            to=to_address,
            subject=subject,
            html=html,
            plain=plain,
            reply_to=GMAIL_SENDER or None,
        )
        if not ok:
            log("send_followup", "ERROR", f"{lead_name} — {err}")
            return False
        log("send_followup", "SUCCESS", f"{lead_name} -> {to_address}")
        print(f"  Follow-up sent: {lead_name} -> {to_address}")
        return True
    except Exception as e:
        log("send_followup", "ERROR", f"{lead_name} — {e}")
        return False


def _log_followup_csv(name: str, email: str, demo_url: str) -> None:
    file_exists = os.path.exists(FOLLOWUP_LOG)
    with open(FOLLOWUP_LOG, "a", newline="") as f:
        fieldnames = ["date", "name", "email", "demo_url"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "name": name,
            "email": email,
            "demo_url": demo_url,
        })


def _log_followup(name: str, email: str, demo_url: str, lead_id: str = "") -> None:
    from storage import use_postgres
    if use_postgres():
        from repositories import outreach_repo
        outreach_repo.log_send(
            lead_id=lead_id or None,
            to_email=email,
            to_name=name,
            demo_url=demo_url,
            outreach_type="followup",
            success=True,
        )
        return
    _log_followup_csv(name, email, demo_url)


def _suppressed_emails() -> set:
    from storage import use_postgres
    suppressed = set()
    if use_postgres():
        from repositories import leads_repo
        for lead in leads_repo.list_all(limit=5000):
            status = (lead.get("reply_status") or "").strip().lower()
            if status in {"bounced", "stop", "stopped", "unsubscribe", "unsubscribed", "do_not_contact"}:
                e = (lead.get("email") or "").strip().lower()
                if e:
                    suppressed.add(e)
        return suppressed

    if not os.path.exists(os.path.join(SCRIPT_DIR, "leads.csv")):
        return suppressed
    with open(os.path.join(SCRIPT_DIR, "leads.csv"), "r") as f:
        for row in csv.DictReader(f):
            status = (row.get("reply_status") or "").strip().lower()
            if status in {"bounced", "stop", "stopped", "unsubscribe", "unsubscribed", "do_not_contact"}:
                e = (row.get("email") or "").strip().lower()
                if e:
                    suppressed.add(e)
    return suppressed


def _already_followed() -> set:
    from storage import use_postgres
    if use_postgres():
        from repositories import outreach_repo
        return outreach_repo.followed_business_names()

    followed = set()
    if not os.path.exists(FOLLOWUP_LOG):
        return followed
    with open(FOLLOWUP_LOG, "r") as f:
        for line in f.readlines()[1:]:
            parts = line.strip().split(",")
            if parts:
                followed.add(parts[1].strip().lower())
    return followed


def _candidates_for_followup() -> list:
    """Return list of dicts: name, email, demo_url, lead_id."""
    from storage import use_postgres

    if use_postgres():
        from repositories import outreach_repo
        return outreach_repo.list_followup_candidates(days=3)

    if not os.path.exists(LOG_CSV):
        return []

    already_followed = _already_followed()
    suppressed = _suppressed_emails()
    now = datetime.datetime.now()
    candidates = []

    with open(LOG_CSV, "r") as f:
        for row in csv.DictReader(f):
            name = (row.get("business_name") or row.get("name", "")).strip()
            email = row.get("email", "").strip()
            demo_url = row.get("demo_url", "").strip()
            email_sent = row.get("email_sent", "").strip()
            date_str = row.get("date", "").strip()

            if not email or email.lower() in suppressed:
                continue
            if email_sent.lower() != "true":
                continue
            if name.lower() in already_followed:
                continue
            try:
                sent_date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                if (now - sent_date).days < 3:
                    continue
            except Exception:
                continue
            candidates.append({"name": name, "email": email, "demo_url": demo_url, "lead_id": ""})

    return candidates


def run_followup() -> int:
    """Send 3-day follow-ups. Returns count sent."""
    candidates = _candidates_for_followup()
    count = 0

    for item in candidates:
        sent = send_followup(item["name"], item["email"], item["demo_url"])
        if sent:
            _log_followup(item["name"], item["email"], item["demo_url"], item.get("lead_id", ""))
            count += 1
            delay = random.randint(25, 45)
            print(f"  Waiting {delay}s...")
            time.sleep(delay)

    log("followup_run", "SUCCESS", f"{count} follow-ups sent")
    print(f"\nFollow-up done. {count} follow-ups sent.")
    return count


def main():
    run_followup()


if __name__ == "__main__":
    main()