"""
Storage facade — routes reads/writes to Postgres or CSV based on STORAGE_BACKEND.
"""

from config import settings
from repositories.postgres_client import is_configured
from system_logger import log


def use_postgres() -> bool:
    if settings.storage_backend.lower() != "postgres":
        return False
    if not is_configured():
        log("storage", "WARNING", "STORAGE_BACKEND=postgres but Supabase not configured — using CSV")
        return False
    return True


def backend_name() -> str:
    return "postgres" if use_postgres() else "csv"