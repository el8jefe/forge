"""Map between CSV-style lead dicts and Postgres rows."""

import datetime
from typing import Any, Dict, Optional


def _int_or_none(val: Any) -> Optional[int]:
    try:
        return int(val) if val not in (None, "", "0") else None
    except (ValueError, TypeError):
        return None


def _float_or_none(val: Any) -> Optional[float]:
    try:
        return float(val) if val not in (None, "", "0") else None
    except (ValueError, TypeError):
        return None


def _bool_from_csv(val: Any) -> bool:
    return str(val or "").strip().lower() in ("true", "1", "yes")


def make_dedup_key(row: dict) -> str:
    name = (row.get("business_name") or row.get("name") or "").strip().lower()
    city = (row.get("city") or "").strip().lower()
    state = (row.get("state") or "").strip().lower()
    return f"{name}|{city}|{state}"


def csv_row_to_db(row: dict, *, is_call_only: bool = False) -> dict:
    """Convert a scraper CSV row to a leads table insert dict."""
    email_sent = _bool_from_csv(row.get("email_sent"))
    status = "emailed" if email_sent else ("site_built" if row.get("demo_site_path") else "new")

    db_row: Dict[str, Any] = {
        "dedup_key": make_dedup_key(row),
        "business_name": (row.get("business_name") or row.get("name") or "").strip(),
        "owner_name": row.get("owner_name") or None,
        "owner_confidence": row.get("owner_confidence") or None,
        "owner_source": row.get("owner_source") or None,
        "email": (row.get("email") or "").strip() or None,
        "email_confidence": row.get("email_confidence") or None,
        "phone": row.get("phone") or None,
        "city": row.get("city") or None,
        "state": row.get("state") or None,
        "business_type": row.get("business_type") or None,
        "website_url": row.get("website_url") or None,
        "website_status": row.get("website_status") or None,
        "google_rating": _float_or_none(row.get("google_rating")),
        "review_count": _int_or_none(row.get("review_count")),
        "forge_score": _int_or_none(row.get("score")),
        "lead_tier": row.get("lead_tier") or None,
        "site_tier": row.get("site_tier") or None,
        "demo_url": (row.get("demo_site_path") or row.get("demo_url") or "").strip() or None,
        "status": status,
        "reply_status": row.get("reply_status") or None,
        "email_sent": email_sent,
        "approved": _bool_from_csv(row.get("approved", "true")),
        "approved_flag": str(row.get("approved", "true")),
        "is_call_only": is_call_only,
        "source": "forge_scraper",
        "user_id": None,
    }

    if row.get("date_scraped"):
        try:
            db_row["date_scraped"] = row["date_scraped"]
        except Exception:
            pass

    if row.get("email_sent_date"):
        try:
            db_row["email_sent_date"] = row["email_sent_date"]
        except Exception:
            pass

    notes = row.get("notes")
    if notes:
        db_row["analysis_notes"] = {"notes": notes}

    return {k: v for k, v in db_row.items() if v is not None or k in (
        "email_sent", "approved", "is_call_only", "user_id", "status", "source"
    )}


def db_row_to_csv(row: dict) -> dict:
    """Convert a Postgres leads row to CSV-compatible dict for pipeline code."""
    email_sent = row.get("email_sent", False)
    return {
        "id": str(row.get("id", "")),
        "business_name": row.get("business_name", ""),
        "owner_name": row.get("owner_name") or "",
        "owner_confidence": row.get("owner_confidence") or "",
        "owner_source": row.get("owner_source") or "",
        "email": row.get("email") or "",
        "email_confidence": row.get("email_confidence") or "",
        "phone": row.get("phone") or "",
        "city": row.get("city") or "",
        "state": row.get("state") or "",
        "business_type": row.get("business_type") or "",
        "google_rating": str(row.get("google_rating") or ""),
        "review_count": str(row.get("review_count") or ""),
        "website_url": row.get("website_url") or "",
        "website_status": row.get("website_status") or "",
        "score": str(row.get("forge_score") or ""),
        "lead_tier": row.get("lead_tier") or "",
        "site_tier": row.get("site_tier") or "",
        "date_scraped": row.get("date_scraped") or "",
        "demo_site_path": row.get("demo_url") or "",
        "email_sent": "true" if email_sent else "false",
        "email_sent_date": (
            row["email_sent_date"][:10]
            if row.get("email_sent_date")
            else ""
        ),
        "reply_status": row.get("reply_status") or "",
        "approved": row.get("approved_flag") or ("true" if row.get("approved") else "false"),
    }


def updates_csv_to_db(updates: dict) -> dict:
    """Map agent CSV-style field updates to DB columns."""
    mapped: Dict[str, Any] = {}
    field_map = {
        "demo_site_path": "demo_url",
        "score": "forge_score",
        "email_sent": "email_sent",
        "email_sent_date": "email_sent_date",
        "reply_status": "reply_status",
        "approved": "approved_flag",
        "notes": "notes",
    }
    for k, v in updates.items():
        col = field_map.get(k, k)
        if col == "email_sent":
            mapped["email_sent"] = _bool_from_csv(v)
            if mapped["email_sent"]:
                mapped["status"] = "emailed"
        elif col == "forge_score":
            mapped["forge_score"] = _int_or_none(v)
        elif col == "approved_flag":
            mapped["approved_flag"] = str(v)
            mapped["approved"] = _bool_from_csv(v)
        elif col == "notes":
            mapped["notes"] = v
        elif col == "email_sent_date" and v:
            mapped["email_sent_date"] = (
                f"{v}T12:00:00Z" if len(str(v)) == 10 else str(v)
            )
        else:
            mapped[col] = v
    mapped["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    return mapped