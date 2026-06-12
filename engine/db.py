"""
db.py — Supabase REST client for FORGE (uses requests, no supabase-py needed)
Calls Supabase PostgREST API directly so we avoid Python 3.9 package conflicts.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

_BASE_URL = None
_HEADERS = None


def _init():
    global _BASE_URL, _HEADERS
    if _BASE_URL:
        return
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    _BASE_URL = f"{url}/rest/v1"
    _HEADERS = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _get(table: str, params: dict = None) -> list:
    _init()
    res = requests.get(f"{_BASE_URL}/{table}", headers=_HEADERS, params=params or {})
    res.raise_for_status()
    return res.json()


def _post(table: str, data) -> list:
    _init()
    res = requests.post(f"{_BASE_URL}/{table}", headers=_HEADERS, json=data)
    res.raise_for_status()
    return res.json()


def _patch(table: str, match: dict, data: dict) -> list:
    _init()
    params = {k: f"eq.{v}" for k, v in match.items()}
    res = requests.patch(f"{_BASE_URL}/{table}", headers=_HEADERS, params=params, json=data)
    res.raise_for_status()
    return res.json()


def get_leads(filters: dict = None, limit: int = 100, offset: int = 0) -> list:
    params = {"limit": limit, "offset": offset, "order": "created_at.desc"}
    if filters:
        for k, v in filters.items():
            params[k] = f"eq.{v}"
    return _get("leads", params)


def upsert_leads(rows: list) -> list:
    _init()
    headers = {**_HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"}
    res = requests.post(f"{_BASE_URL}/leads", headers=headers, json=rows)
    res.raise_for_status()
    return res.json()


def update_lead(lead_id: str, data: dict) -> list:
    return _patch("leads", {"id": lead_id}, data)


def log_outreach(lead_id: str, email: str, name: str, demo_url: str, outreach_type: str = "initial"):
    try:
        _post("outreach_log", {
            "lead_id": lead_id,
            "type": outreach_type,
            "to_email": email,
            "to_name": name,
            "demo_url": demo_url,
            "success": True,
        })
    except Exception as e:
        print(f"[DB] outreach log error: {e}")


def get_stats() -> dict:
    leads = get_leads(limit=1000)
    counts = {"total": len(leads), "by_status": {}, "by_tier": {}, "by_source": {}}
    for row in leads:
        for key, field in [("by_status", "status"), ("by_tier", "lead_tier"), ("by_source", "source")]:
            val = row.get(field) or "unknown"
            counts[key][val] = counts[key].get(val, 0) + 1
    return counts


def leads_to_rows(leads: list) -> list:
    rows = []
    for lead in leads:
        rows.append({
            "business_name": lead.get("business_name", ""),
            "owner_name": lead.get("owner_name") or None,
            "email": lead.get("email") or None,
            "phone": lead.get("phone") or None,
            "city": lead.get("city"),
            "state": lead.get("state"),
            "business_type": lead.get("business_type"),
            "website_url": lead.get("website_url") or None,
            "website_status": lead.get("website_status"),
            "google_rating": _float_or_none(lead.get("google_rating")),
            "review_count": _int_or_none(lead.get("review_count")),
            "forge_score": _int_or_none(lead.get("score")),
            "lead_tier": lead.get("lead_tier"),
            "demo_url": lead.get("demo_site_path") or None,
            "status": _map_status(lead),
            "approved": str(lead.get("approved", "true")).lower() == "true",
            "source": "forge_scraper",
        })
    return rows


def _float_or_none(val):
    try:
        return float(val) if val not in (None, "", "0") else None
    except (ValueError, TypeError):
        return None


def _int_or_none(val):
    try:
        return int(val) if val not in (None, "") else None
    except (ValueError, TypeError):
        return None


def _map_status(lead: dict) -> str:
    if str(lead.get("email_sent", "")).lower() == "true":
        return "emailed"
    if lead.get("demo_site_path"):
        return "site_built"
    return "new"
