"""
followup.py — FORGE 3-Day Follow-Up Sender
Reads log.csv, finds emails sent 3+ days ago without a follow-up,
and sends a second outreach via Gmail SMTP.
"""

import csv
import os
import datetime
import smtplib
import random
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from system_logger import log

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_CSV = os.path.join(SCRIPT_DIR, "log.csv")
FOLLOWUP_LOG = os.path.join(SCRIPT_DIR, "followup_log.csv")
LEADS_CSV = os.path.join(SCRIPT_DIR, "leads.csv")

GMAIL_SENDER = os.getenv("GMAIL_SENDER", "juanparinconr@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
MY_TEST_EMAIL = os.getenv("MY_TEST_EMAIL", "juanparinconr@gmail.com")
MY_PHONE = os.getenv("MY_PHONE", "(203) 609-4807")
TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"


def send_followup(lead_name: str, email: str, demo_url: str) -> bool:
    to_address = MY_TEST_EMAIL if TEST_MODE else email
    if TEST_MODE:
        print(f"  TEST MODE — routing follow-up for {lead_name} → {MY_TEST_EMAIL}")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Quick follow-up — did you see your free demo site?"
    msg["From"] = GMAIL_SENDER
    msg["To"] = to_address
    msg["Reply-To"] = GMAIL_SENDER

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:32px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:4px;overflow:hidden;max-width:600px;width:100%;">
      <tr><td style="background:#0f0f0f;padding:28px 40px;">
        <span style="font-size:22px;font-weight:bold;color:#c9a84c;font-family:Georgia,serif;">Forge</span>
        <span style="color:#ffffff;font-size:11px;display:block;margin-top:4px;opacity:0.5;letter-spacing:0.15em;text-transform:uppercase;">Web Studio &mdash; Greenwich, CT</span>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="font-size:16px;color:#222;margin:0 0 20px;">Hey <strong>{lead_name}</strong>,</p>
        <p style="font-size:15px;color:#444;line-height:1.7;margin:0 0 20px;">
          I sent you a note a few days ago &mdash; I built a free website mockup for your business
          and wanted to make sure you had a chance to see it.
        </p>
        <table cellpadding="0" cellspacing="0" width="100%" style="margin:28px 0;">
          <tr><td align="center">
            <a href="{demo_url}" style="display:inline-block;background:#FFD700;color:#000;padding:16px 40px;text-decoration:none;font-weight:bold;font-size:15px;border-radius:3px;">
              View Your Free Site &rarr;
            </a>
          </td></tr>
        </table>
        <p style="font-size:15px;color:#444;line-height:1.7;margin:0 0 20px;">
          I know you're busy running your business &mdash; that&rsquo;s exactly why I built this.
          Get your site live on your domain within 24 hours for <strong>$200 flat</strong>.
          No monthly fees, no contracts.
        </p>
        <p style="font-size:15px;color:#444;line-height:1.7;margin:0 0 28px;">
          If you&rsquo;re not interested, no worries &mdash; just reply and let me know.
          But if you want to chat, hit reply or call/text me at {MY_PHONE}.
        </p>
        <p style="font-size:15px;color:#222;line-height:1.8;margin:0;">
          &ndash; Juan Pablo Rincon Rios<br>
          <strong>Founder, Forge</strong><br>
          Greenwich, CT &nbsp;|&nbsp; {MY_PHONE}
        </p>
      </td></tr>
      <tr><td style="background:#f9f9f9;padding:18px 40px;border-top:1px solid #eee;">
        <p style="font-size:11px;color:#aaa;margin:0;">Reply STOP to opt out.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""

    plain = (
        f"Hey {lead_name},\n\n"
        f"I sent you a note a few days ago — I built a free website mockup for your business "
        f"and wanted to make sure you had a chance to see it.\n\n"
        f"View it here: {demo_url}\n\n"
        f"Get it live on your domain within 24 hours for $200 flat. No monthly fees, no contracts.\n\n"
        f"If you're not interested, no worries — just reply and let me know.\n\n"
        f"- Juan Pablo Rincon Rios\n"
        f"Founder, Forge | {MY_PHONE}\n\n"
        f"Reply STOP to opt out."
    )

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, to_address, msg.as_string())
        server.quit()
        log("send_followup", "SUCCESS", f"{lead_name} -> {to_address}")
        print(f"  Follow-up sent: {lead_name} -> {to_address}")
        return True
    except Exception as e:
        log("send_followup", "ERROR", f"{lead_name} — {e}")
        print(f"  Follow-up failed for {lead_name}: {e}")
        return False


def log_followup(name: str, email: str, demo_url: str):
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


def main():
    if not os.path.exists(LOG_CSV):
        print("No log.csv found — run agent.py first.")
        return

    already_followed = set()
    if os.path.exists(FOLLOWUP_LOG):
        with open(FOLLOWUP_LOG, "r") as f:
            for line in f.readlines()[1:]:
                parts = line.strip().split(",")
                if parts:
                    already_followed.add(parts[1].strip().lower())

    now = datetime.datetime.now()
    count = 0
    suppressed_emails = set()
    if os.path.exists(LEADS_CSV):
        with open(LEADS_CSV, "r") as f:
            for row in csv.DictReader(f):
                status = (row.get("reply_status") or "").strip().lower()
                if status in {"bounced", "stop", "stopped", "unsubscribe", "unsubscribed", "do_not_contact"}:
                    e = (row.get("email") or "").strip().lower()
                    if e:
                        suppressed_emails.add(e)

    with open(LOG_CSV, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        name = (row.get("business_name") or row.get("name", "")).strip()
        email = row.get("email", "").strip()
        demo_url = row.get("demo_url", "").strip()
        email_sent = row.get("email_sent", "").strip()
        date_str = row.get("date", "").strip()

        if not email:
            continue
        if email.lower() in suppressed_emails:
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

        sent = send_followup(name, email, demo_url)
        if sent:
            log_followup(name, email, demo_url)
            count += 1
            # Stagger sends
            delay = random.randint(25, 45)
            print(f"  Waiting {delay}s...")
            time.sleep(delay)

    log("followup_run", "SUCCESS", f"{count} follow-ups sent")
    print(f"\nFollow-up done. {count} follow-ups sent.")
    if count == 0:
        print("No follow-ups needed yet — check back in a few days.")


if __name__ == "__main__":
    main()
