"""
notifications.py — FORGE Notification System
Handles: email summaries, Twilio SMS, dashboard push (notifications.json)
"""

import os
import json
import datetime
from dotenv import load_dotenv
from system_logger import log

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NOTIF_FILE = os.path.join(SCRIPT_DIR, "notifications.json")
MAX_STORED = 10

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM = os.getenv("TWILIO_FROM", "")
MY_PHONE = os.getenv("MY_PHONE", "")


def _load_notifications() -> list:
    if not os.path.exists(NOTIF_FILE):
        return []
    with open(NOTIF_FILE, "r") as f:
        return json.load(f)


def _save_notifications(items: list):
    with open(NOTIF_FILE, "w") as f:
        json.dump(items[-MAX_STORED:], f, indent=2)


def push_to_dashboard(message: str, level: str = "info"):
    """Store notification in notifications.json for dashboard display."""
    items = _load_notifications()
    items.append({
        "ts": datetime.datetime.now().isoformat(),
        "message": message,
        "level": level,
    })
    _save_notifications(items)


def send_sms(message: str):
    """Send SMS via Twilio. Silently skips if credentials not configured."""
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, MY_PHONE]):
        return  # Silently skip if keys missing
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(body=message, from_=TWILIO_FROM, to=MY_PHONE)
        log("send_sms", "SUCCESS", message[:60])
    except ImportError:
        log("send_sms", "SKIP", "twilio not installed")
    except Exception as e:
        log("send_sms", "ERROR", str(e))


def fire_notification(message: str, level: str = "info", sms: bool = False):
    """
    Broadcast a notification to all channels.
    level: "info" | "warning" | "critical"
    sms=True sends SMS (only for critical events)
    """
    push_to_dashboard(message, level)
    log(f"notification_{level}", "INFO", message[:80])

    if level == "critical" or sms:
        send_sms(f"FORGE: {message}")


def notify_reply_received(business_name: str):
    msg = f"{business_name} just replied to your email. Check your inbox!"
    fire_notification(msg, level="info", sms=True)


def notify_hot_lead(business_name: str, score: int):
    msg = f"New HOT lead: {business_name} (score {score})"
    fire_notification(msg, level="info")


def notify_daily_limit_reached():
    msg = "Daily email limit reached."
    fire_notification(msg, level="warning")


def notify_critical_error(step: str, detail: str):
    msg = f"CRITICAL error in {step}: {detail}"
    fire_notification(msg, level="critical", sms=True)
