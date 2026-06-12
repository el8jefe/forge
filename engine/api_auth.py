"""
api_auth.py — FORGE API authentication helpers (Phase 0 security)
Validates X-FORGE-API-Key or Authorization: Bearer <key> on protected routes.
Set FORGE_AUTH_ENABLED=false to disable during local debugging only.
"""

import secrets
from typing import Optional

from config import settings

FORGE_API_KEY = settings.forge_api_key.strip()
AUTH_ENABLED = settings.forge_auth_enabled

def public_paths() -> frozenset:
    paths = {"/health", "/webhook/stripe"}
    if settings.forge_openapi_enabled:
        paths.update({"/docs", "/openapi.json", "/redoc"})
    return frozenset(paths)


PUBLIC_PATHS = public_paths()


def is_auth_enabled() -> bool:
    return AUTH_ENABLED and bool(FORGE_API_KEY)


def extract_api_key(authorization: Optional[str], forge_header: Optional[str]) -> str:
    if forge_header:
        return forge_header.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return ""


def validate_api_key(authorization: Optional[str], forge_header: Optional[str]) -> bool:
    if not is_auth_enabled():
        return True
    provided = extract_api_key(authorization, forge_header)
    return bool(provided) and secrets.compare_digest(provided, FORGE_API_KEY)