"""
Low-level Supabase PostgREST HTTP client.
Service role key bypasses RLS — never expose to browsers.
"""

from typing import Any, Dict, List, Optional

import requests

from config import settings

_BASE_URL: Optional[str] = None
_HEADERS: Optional[Dict[str, str]] = None


def is_configured() -> bool:
    url = settings.supabase_url or ""
    key = settings.supabase_service_key or ""
    return bool(url.strip() and key.strip())


def _init() -> None:
    global _BASE_URL, _HEADERS
    if _BASE_URL:
        return
    if not is_configured():
        raise RuntimeError(
            "Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env"
        )
    _BASE_URL = f"{settings.supabase_url.rstrip('/')}/rest/v1"
    key = settings.supabase_service_key
    _HEADERS = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def reset_client() -> None:
    """Clear cached connection (for tests)."""
    global _BASE_URL, _HEADERS
    _BASE_URL = None
    _HEADERS = None


def get(table: str, params: Optional[Dict[str, Any]] = None) -> List[dict]:
    _init()
    res = requests.get(f"{_BASE_URL}/{table}", headers=_HEADERS, params=params or {}, timeout=30)
    res.raise_for_status()
    return res.json()


def post(table: str, data: Any, *, prefer: Optional[str] = None) -> List[dict]:
    _init()
    headers = dict(_HEADERS)
    if prefer:
        headers["Prefer"] = prefer
    res = requests.post(f"{_BASE_URL}/{table}", headers=headers, json=data, timeout=60)
    res.raise_for_status()
    return res.json() if res.text else []


def patch(table: str, match: Dict[str, str], data: dict) -> List[dict]:
    _init()
    params = {k: f"eq.{v}" for k, v in match.items()}
    res = requests.patch(
        f"{_BASE_URL}/{table}", headers=_HEADERS, params=params, json=data, timeout=30
    )
    res.raise_for_status()
    return res.json() if res.text else []


def upsert(table: str, rows: List[dict], *, on_conflict: str) -> List[dict]:
    prefer = f"resolution=merge-duplicates,return=representation,on_conflict={on_conflict}"
    return post(table, rows, prefer=prefer)