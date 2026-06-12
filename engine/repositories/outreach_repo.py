"""Outreach / email event logging."""

import datetime
from typing import Optional, Set

from repositories import postgres_client as pg
from system_logger import log


def log_send(
    *,
    lead_id: Optional[str],
    to_email: str,
    to_name: str,
    demo_url: str,
    outreach_type: str = "initial",
    success: bool = True,
    error_message: str = "",
) -> None:
    resolved_id = lead_id or find_lead_id_by_name(to_name)
    if not resolved_id:
        log("outreach_repo", "WARNING", f"skipping outreach_log — no lead_id for {to_name}")
        return
    row = {
        "lead_id": resolved_id,
        "type": outreach_type,
        "to_email": to_email,
        "to_name": to_name,
        "demo_url": demo_url,
        "success": success,
        "error_message": error_message or None,
    }
    pg.post("outreach_log", row)


def find_lead_id_by_name(business_name: str) -> Optional[str]:
    rows = pg.get("leads", {
        "business_name": f"ilike.{business_name.strip()}",
        "source": "eq.forge_scraper",
        "limit": "1",
        "select": "id",
    })
    return rows[0]["id"] if rows else None


def contacted_business_names() -> Set[str]:
    """Business names already successfully emailed (from leads.email_sent)."""
    rows = pg.get("leads", {
        "source": "eq.forge_scraper",
        "email_sent": "eq.true",
        "select": "business_name",
        "limit": "5000",
    })
    return {(r.get("business_name") or "").strip().lower() for r in rows if r.get("business_name")}


def followed_business_names() -> Set[str]:
    rows = pg.get("outreach_log", {
        "type": "eq.followup",
        "success": "eq.true",
        "select": "to_name",
        "limit": "5000",
    })
    return {(r.get("to_name") or "").strip().lower() for r in rows if r.get("to_name")}


def list_followup_candidates(days: int = 3) -> list:
    """Initial sends at least `days` old without a successful followup."""
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat() + "Z"
    initial = pg.get("outreach_log", {
        "type": "eq.initial",
        "success": "eq.true",
        "sent_at": f"lt.{cutoff}",
        "select": "lead_id,to_email,to_name,demo_url,sent_at",
        "limit": "500",
        "order": "sent_at.asc",
    })
    followed = followed_business_names()
    candidates = []
    seen = set()

    for row in initial:
        name = (row.get("to_name") or "").strip()
        email = (row.get("to_email") or "").strip()
        demo_url = (row.get("demo_url") or "").strip()
        key = email.lower()
        if not email or not demo_url or not name:
            continue
        if name.lower() in followed or key in seen:
            continue
        seen.add(key)
        candidates.append({
            "name": name,
            "email": email,
            "demo_url": demo_url,
            "lead_id": row.get("lead_id") or "",
        })
    return candidates


def sync_demos_from_failed_sends() -> int:
    """
    Back-fill demo_url on leads from outreach_log rows where send failed but demo_url exists.
    Returns number of leads updated.
    """
    rows = pg.get("outreach_log", {
        "success": "eq.false",
        "demo_url": "not.is.null",
        "select": "lead_id,demo_url",
        "limit": "500",
    })
    updated = 0
    for row in rows:
        lead_id = row.get("lead_id")
        demo_url = (row.get("demo_url") or "").strip()
        if not lead_id or not demo_url:
            continue
        existing = pg.get("leads", {"id": f"eq.{lead_id}", "select": "demo_url", "limit": "1"})
        if existing and (existing[0].get("demo_url") or "").strip():
            continue
        pg.patch("leads", {"id": lead_id}, {"demo_url": demo_url, "status": "site_built"})
        updated += 1
    return updated