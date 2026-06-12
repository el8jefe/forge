"""Email warmup and daily send counters in Postgres."""

import datetime
from typing import Any, Dict

from repositories import postgres_client as pg

COUNTERS_ID = "default"

WARMUP_SCHEDULE = {
    1: 80, 2: 140, 3: 200, 4: 260, 5: 320, 6: 380, 7: 500,
}
GMAIL_MAX = 500


def _empty_hourly() -> Dict[str, int]:
    return {str(h): 0 for h in range(24)}


def _today() -> str:
    return datetime.date.today().isoformat()


def _get_or_create() -> dict:
    rows = pg.get("email_send_counters", {"id": f"eq.{COUNTERS_ID}", "limit": "1"})
    today = _today()
    if rows and rows[0].get("counter_date") == today:
        return rows[0]

    warmup_start = today
    warmup_day = 1
    if rows:
        try:
            start = datetime.date.fromisoformat(rows[0].get("warmup_start_date") or today)
            warmup_start = start.isoformat()
            warmup_day = (datetime.date.today() - start).days + 1
        except ValueError:
            pass

    daily_limit = WARMUP_SCHEDULE.get(warmup_day, GMAIL_MAX)
    new_row = {
        "id": COUNTERS_ID,
        "counter_date": today,
        "send_count": 0,
        "hourly_counts": _empty_hourly(),
        "warmup_start_date": warmup_start,
        "warmup_day": warmup_day,
        "daily_limit": daily_limit,
        "sends": [],
    }
    try:
        pg.post("email_send_counters", new_row, prefer="resolution=merge-duplicates,return=representation")
    except Exception:
        pg.patch("email_send_counters", {"id": COUNTERS_ID}, new_row)
    refreshed = pg.get("email_send_counters", {"id": f"eq.{COUNTERS_ID}", "limit": "1"})
    return refreshed[0] if refreshed else new_row


def _save(state: dict) -> None:
    state["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    pg.patch("email_send_counters", {"id": COUNTERS_ID}, state)


def get_warmup_state() -> dict:
    row = _get_or_create()
    return {
        "start_date": row.get("warmup_start_date") or _today(),
        "current_day": row.get("warmup_day", 1),
        "daily_limit_override": row.get("daily_limit", WARMUP_SCHEDULE.get(1, 80)),
    }


def update_warmup_state() -> dict:
    row = _get_or_create()
    try:
        start = datetime.date.fromisoformat(row.get("warmup_start_date") or _today())
    except ValueError:
        start = datetime.date.today()
    current_day = (datetime.date.today() - start).days + 1
    row["warmup_day"] = current_day
    row["daily_limit"] = WARMUP_SCHEDULE.get(current_day, GMAIL_MAX)
    _save(row)
    return {
        "start_date": start.isoformat(),
        "current_day": current_day,
        "daily_limit_override": row["daily_limit"],
    }


def get_daily_limit() -> int:
    return int(_get_or_create().get("daily_limit") or WARMUP_SCHEDULE.get(1, 80))


def load_send_log() -> dict:
    row = _get_or_create()
    hc = row.get("hourly_counts") or {}
    for h in range(24):
        hc.setdefault(str(h), 0)
    return {
        "date": row.get("counter_date"),
        "count": row.get("send_count", 0),
        "hourly_counts": hc,
        "warmup_day": row.get("warmup_day", 1),
        "last_send_timestamp": (row.get("last_send_at") or "")[:19],
        "sends": row.get("sends") or [],
    }


def save_send_log(data: dict) -> None:
    row = _get_or_create()
    row["send_count"] = data.get("count", 0)
    row["hourly_counts"] = data.get("hourly_counts", _empty_hourly())
    row["sends"] = data.get("sends", [])
    if data.get("last_send_timestamp"):
        row["last_send_at"] = data["last_send_timestamp"]
    _save(row)


def get_today_count() -> int:
    return int(_get_or_create().get("send_count") or 0)


def get_current_hour_count() -> int:
    row = _get_or_create()
    hc = row.get("hourly_counts") or {}
    return int(hc.get(str(datetime.datetime.now().hour), 0))