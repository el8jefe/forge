"""Email warmup + send counters — JSON files or Postgres."""

import datetime
import json
import os

from storage import use_postgres

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WARMUP_FILE = os.path.join(_SCRIPT_DIR, "warmup_state.json")
SEND_LOG_FILE = os.path.join(_SCRIPT_DIR, "send_log.json")

WARMUP_SCHEDULE = {1: 80, 2: 140, 3: 200, 4: 260, 5: 320, 6: 380, 7: 500}
GMAIL_MAX = 500


def _empty_hourly_counts() -> dict:
    return {str(h): 0 for h in range(24)}


# ─── CSV/JSON implementations (unchanged logic) ──────────────────────────────

def _json_load_warmup() -> dict:
    if not os.path.exists(WARMUP_FILE):
        state = {
            "start_date": datetime.date.today().isoformat(),
            "current_day": 1,
            "daily_limit_override": WARMUP_SCHEDULE[1],
        }
        _json_save_warmup(state)
        return state
    with open(WARMUP_FILE, "r") as f:
        return json.load(f)


def _json_save_warmup(state: dict) -> None:
    with open(WARMUP_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _json_load_send_log() -> dict:
    today = datetime.date.today().isoformat()
    state = _json_load_warmup()
    warmup_day = state.get("current_day", 1)
    if not os.path.exists(SEND_LOG_FILE):
        return _empty_send_log(today, warmup_day)
    with open(SEND_LOG_FILE, "r") as f:
        try:
            data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            return _empty_send_log(today, warmup_day)
    if data.get("date") != today:
        return _empty_send_log(today, warmup_day)
    hc = data.get("hourly_counts", {})
    for h in range(24):
        hc.setdefault(str(h), 0)
    data["hourly_counts"] = hc
    return data


def _empty_send_log(today: str, warmup_day: int) -> dict:
    return {
        "date": today,
        "count": 0,
        "hourly_counts": _empty_hourly_counts(),
        "warmup_day": warmup_day,
        "last_send_timestamp": "",
        "sends": [],
    }


def _json_save_send_log(data: dict) -> None:
    with open(SEND_LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ─── Public API (used by emailer.py) ─────────────────────────────────────────

def load_warmup_state() -> dict:
    if use_postgres():
        from repositories import counters_repo
        return counters_repo.get_warmup_state()
    return _json_load_warmup()


def save_warmup_state(state: dict) -> None:
    if not use_postgres():
        _json_save_warmup(state)


def update_warmup_state() -> dict:
    if use_postgres():
        from repositories import counters_repo
        return counters_repo.update_warmup_state()
    state = _json_load_warmup()
    try:
        start = datetime.date.fromisoformat(state["start_date"])
    except (KeyError, ValueError):
        start = datetime.date.today()
        state["start_date"] = start.isoformat()
    current_day = (datetime.date.today() - start).days + 1
    state["current_day"] = current_day
    state["daily_limit_override"] = WARMUP_SCHEDULE.get(current_day, GMAIL_MAX)
    _json_save_warmup(state)
    return state


def get_daily_limit() -> int:
    if use_postgres():
        from repositories import counters_repo
        return counters_repo.get_daily_limit()
    return _json_load_warmup().get("daily_limit_override", GMAIL_MAX)


def load_send_log() -> dict:
    if use_postgres():
        from repositories import counters_repo
        return counters_repo.load_send_log()
    return _json_load_send_log()


def save_send_log(data: dict) -> None:
    if use_postgres():
        from repositories import counters_repo
        counters_repo.save_send_log(data)
        return
    _json_save_send_log(data)


def get_today_count() -> int:
    if use_postgres():
        from repositories import counters_repo
        return counters_repo.get_today_count()
    return _json_load_send_log().get("count", 0)


def get_current_hour_count() -> int:
    if use_postgres():
        from repositories import counters_repo
        return counters_repo.get_current_hour_count()
    data = _json_load_send_log()
    return data.get("hourly_counts", {}).get(str(datetime.datetime.now().hour), 0)