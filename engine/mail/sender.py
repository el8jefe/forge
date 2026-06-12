"""
Unified email delivery for the FORGE engine pipeline.

Priority (EMAIL_PROVIDER=auto):
  1. Resend when RESEND_API_KEY is set
  2. Gmail SMTP when GMAIL_APP_PASSWORD is set
"""

from typing import Optional, Tuple

import requests

from config import settings
from system_logger import log


def active_provider() -> str:
    """Return the provider that would be used: resend, gmail, or none."""
    mode = (settings.email_provider or "auto").lower()
    if mode == "resend" or (mode == "auto" and settings.resend_api_key.strip()):
        return "resend" if settings.resend_api_key.strip() else "none"
    if mode == "gmail" or (mode == "auto" and settings.gmail_app_password.strip()):
        return "gmail" if settings.gmail_app_password.strip() else "none"
    return "none"


def _resolve_provider() -> str:
    provider = active_provider()
    if provider == "none":
        raise RuntimeError(
            "No email provider configured. Set RESEND_API_KEY (production) "
            "or GMAIL_APP_PASSWORD (dev)."
        )
    return provider


def send_message(
    *,
    to: str,
    subject: str,
    html: str,
    plain: str,
    reply_to: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Send an email via Resend or Gmail.

    Returns:
        (success, error_message)
    """
    provider = _resolve_provider()
    if provider == "resend":
        return _send_resend(to=to, subject=subject, html=html, plain=plain, reply_to=reply_to)
    return _send_gmail(to=to, subject=subject, html=html, plain=plain, reply_to=reply_to)


def _send_resend(
    *,
    to: str,
    subject: str,
    html: str,
    plain: str,
    reply_to: Optional[str],
) -> Tuple[bool, str]:
    from_addr = settings.resend_from_email.strip() or settings.gmail_sender.strip()
    if not from_addr:
        return False, "RESEND_FROM_EMAIL or GMAIL_SENDER required"

    payload = {
        "from": from_addr,
        "to": [to],
        "subject": subject,
        "html": html,
        "text": plain,
    }
    if reply_to:
        payload["reply_to"] = reply_to

    try:
        res = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        if res.status_code >= 400:
            err = res.json() if res.text else {}
            msg = err.get("message", res.text[:200])
            log("mail_resend", "ERROR", msg)
            return False, msg
        log("mail_resend", "SUCCESS", f"to={to}")
        return True, ""
    except Exception as e:
        log("mail_resend", "ERROR", str(e))
        return False, str(e)


def _send_gmail(
    *,
    to: str,
    subject: str,
    html: str,
    plain: str,
    reply_to: Optional[str],
) -> Tuple[bool, str]:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    sender = settings.gmail_sender.strip()
    password = settings.gmail_app_password.strip()
    if not sender or not password:
        return False, "GMAIL_SENDER and GMAIL_APP_PASSWORD required"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    if reply_to:
        msg["Reply-To"] = reply_to
    else:
        msg["Reply-To"] = sender
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
        server.login(sender, password)
        server.sendmail(sender, to, msg.as_string())
        server.quit()
        log("mail_gmail", "SUCCESS", f"to={to}")
        return True, ""
    except Exception as e:
        log("mail_gmail", "ERROR", str(e))
        return False, str(e)