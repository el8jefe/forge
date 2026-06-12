"""Postgres lead repository."""

from typing import Dict, List, Optional

from repositories.lead_mapper import csv_row_to_db, db_row_to_csv, updates_csv_to_db
from repositories import postgres_client as pg
from system_logger import log

DEDUP_CONFLICT = "dedup_key"


def upsert_csv_rows(email_leads: List[dict], call_leads: List[dict]) -> int:
    rows = [csv_row_to_db(r, is_call_only=False) for r in email_leads]
    rows += [csv_row_to_db(r, is_call_only=True) for r in call_leads]
    if not rows:
        return 0
    pg.upsert("leads", rows, on_conflict=DEDUP_CONFLICT)
    log("leads_repo", "SUCCESS", f"upserted {len(rows)} leads to postgres")
    return len(rows)


def list_all(*, email_only: bool = False, limit: int = 5000) -> List[dict]:
    params: Dict[str, str] = {
        "select": "*",
        "source": "eq.forge_scraper",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    if email_only:
        params["is_call_only"] = "eq.false"
    rows = pg.get("leads", params)
    return [db_row_to_csv(r) for r in rows]


def list_email_leads(limit: int = 5000) -> List[dict]:
    return list_all(email_only=True, limit=limit)


def update_by_business_name(business_name: str, updates: dict) -> bool:
    name = business_name.strip()
    if not name:
        return False
    existing = pg.get("leads", {
        "business_name": f"eq.{name}",
        "source": "eq.forge_scraper",
        "limit": "1",
    })
    if not existing:
        log("leads_repo", "WARNING", f"no lead found for update: {name}")
        return False
    lead_id = existing[0]["id"]
    pg.patch("leads", {"id": lead_id}, updates_csv_to_db(updates))
    return True


def get_by_id(lead_id: str) -> Optional[dict]:
    rows = pg.get("leads", {"id": f"eq.{lead_id}", "limit": "1"})
    return db_row_to_csv(rows[0]) if rows else None


def get_stats() -> dict:
    leads = pg.get("leads", {"source": "eq.forge_scraper", "limit": "1000"})
    counts = {"total": len(leads), "by_status": {}, "by_tier": {}, "by_source": {}}
    for row in leads:
        for key, field in [
            ("by_status", "status"),
            ("by_tier", "lead_tier"),
            ("by_source", "source"),
        ]:
            val = row.get(field) or "unknown"
            counts[key][val] = counts[key].get(val, 0) + 1
    return counts