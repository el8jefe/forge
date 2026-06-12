"""
db.py — Supabase REST client for FORGE (uses requests, no supabase-py needed)
Calls Supabase PostgREST API directly so we avoid Python 3.9 package conflicts.

Phase 2: delegates to repositories when STORAGE_BACKEND=postgres.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _require_supabase():
    from repositories.postgres_client import is_configured
    if not is_configured():
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")


def get_leads(filters: dict = None, limit: int = 100, offset: int = 0) -> list:
    _require_supabase()
    from repositories import postgres_client as pg

    params = {"limit": limit, "offset": offset, "order": "created_at.desc"}
    if filters:
        for k, v in filters.items():
            params[k] = f"eq.{v}"
    return pg.get("leads", params)


def upsert_leads(rows: list) -> list:
    _require_supabase()
    from repositories import postgres_client as pg
    from repositories.lead_mapper import make_dedup_key

    enriched = []
    for row in rows:
        r = dict(row)
        if not r.get("dedup_key") and r.get("business_name"):
            r["dedup_key"] = make_dedup_key(r)
        enriched.append(r)
    return pg.upsert("leads", enriched, on_conflict="dedup_key")


def update_lead(lead_id: str, data: dict) -> list:
    _require_supabase()
    from repositories import postgres_client as pg
    from repositories.lead_mapper import updates_csv_to_db
    from storage import use_postgres

    payload = updates_csv_to_db(data) if use_postgres() else data
    return pg.patch("leads", {"id": lead_id}, payload)


def log_outreach(lead_id: str, email: str, name: str, demo_url: str, outreach_type: str = "initial"):
    try:
        from repositories import outreach_repo
        outreach_repo.log_send(
            lead_id=lead_id,
            to_email=email,
            to_name=name,
            demo_url=demo_url,
            outreach_type=outreach_type,
            success=True,
        )
    except Exception as e:
        print(f"[DB] outreach log error: {e}")


def get_stats() -> dict:
    _require_supabase()
    from storage import use_postgres

    if use_postgres():
        from repositories import leads_repo
        return leads_repo.get_stats()

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