"""Pipeline job persistence — Postgres pipeline_jobs or in-memory fallback."""

import datetime
import uuid
from typing import Any, Dict, List, Optional

from repositories.postgres_client import is_configured
from system_logger import log

_MEMORY_JOBS: Dict[str, dict] = {}
_FORCE_MEMORY = False


def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def _use_db() -> bool:
    if _FORCE_MEMORY:
        return False
    return is_configured()


def use_memory_backend(force: bool = True) -> None:
    """Test helper — force in-memory job store."""
    global _FORCE_MEMORY
    _FORCE_MEMORY = force
    if force:
        clear_memory_jobs()


def _flatten_job(row: dict) -> dict:
    """Normalize DB or memory row to API response shape."""
    payload = row.get("payload") or {}
    result = row.get("result") or {}
    job_type = row.get("job_type") or row.get("type", "")
    return {
        "id": str(row.get("id", "")),
        "type": job_type,
        "status": row.get("status", "pending"),
        "params": payload,
        "leads_found": result.get("leads_found", 0),
        "sites_built": result.get("sites_built", 0),
        "emails_sent": result.get("emails_sent", 0),
        "result": result,
        "attempts": row.get("attempts", 0),
        "error": row.get("error"),
        "started_at": row.get("started_at"),
        "completed_at": row.get("completed_at"),
        "created_at": row.get("created_at"),
    }


def create(job_type: str, payload: Optional[dict] = None) -> str:
    job_id = str(uuid.uuid4())
    payload = payload or {}
    now = _now_iso()

    if _use_db():
        from repositories import postgres_client as pg
        pg.post("pipeline_jobs", {
            "id": job_id,
            "job_type": job_type,
            "status": "pending",
            "payload": payload,
            "attempts": 0,
            "max_attempts": 3,
            "created_at": now,
        })
        log("jobs_repo", "INFO", f"created job {job_id} type={job_type}")
        return job_id

    _MEMORY_JOBS[job_id] = {
        "id": job_id,
        "job_type": job_type,
        "status": "pending",
        "payload": payload,
        "result": {},
        "attempts": 0,
        "error": None,
        "created_at": now,
        "started_at": None,
        "completed_at": None,
    }
    return job_id


def mark_running(job_id: str) -> None:
    now = _now_iso()
    if _use_db():
        from repositories import postgres_client as pg
        rows = pg.get("pipeline_jobs", {"id": f"eq.{job_id}", "select": "attempts", "limit": "1"})
        attempts = (rows[0].get("attempts") or 0) + 1 if rows else 1
        pg.patch("pipeline_jobs", {"id": job_id}, {
            "status": "running",
            "started_at": now,
            "attempts": attempts,
        })
        return

    job = _MEMORY_JOBS.get(job_id)
    if job:
        job["status"] = "running"
        job["started_at"] = now
        job["attempts"] = job.get("attempts", 0) + 1


def mark_complete(job_id: str, result: dict) -> None:
    now = _now_iso()
    if _use_db():
        from repositories import postgres_client as pg
        pg.patch("pipeline_jobs", {"id": job_id}, {
            "status": "complete",
            "result": result,
            "completed_at": now,
            "error": None,
        })
        return

    job = _MEMORY_JOBS.get(job_id)
    if job:
        job["status"] = "complete"
        job["result"] = result
        job["completed_at"] = now
        job["error"] = None


def mark_failed(job_id: str, error: str) -> None:
    now = _now_iso()
    if _use_db():
        from repositories import postgres_client as pg
        rows = pg.get("pipeline_jobs", {"id": f"eq.{job_id}", "select": "attempts,max_attempts", "limit": "1"})
        attempts = rows[0].get("attempts", 0) if rows else 0
        max_attempts = rows[0].get("max_attempts", 3) if rows else 3
        status = "dead" if attempts >= max_attempts else "failed"
        pg.patch("pipeline_jobs", {"id": job_id}, {
            "status": status,
            "error": error[:2000],
            "completed_at": now,
        })
        return

    job = _MEMORY_JOBS.get(job_id)
    if job:
        job["status"] = "failed"
        job["error"] = error
        job["completed_at"] = now


def get(job_id: str) -> Optional[dict]:
    if _use_db():
        from repositories import postgres_client as pg
        rows = pg.get("pipeline_jobs", {"id": f"eq.{job_id}", "limit": "1"})
        return _flatten_job(rows[0]) if rows else None

    job = _MEMORY_JOBS.get(job_id)
    return _flatten_job(job) if job else None


def list_jobs(limit: int = 50) -> List[dict]:
    if _use_db():
        from repositories import postgres_client as pg
        rows = pg.get("pipeline_jobs", {
            "order": "created_at.desc",
            "limit": str(limit),
        })
        return [_flatten_job(r) for r in rows]

    jobs = sorted(
        _MEMORY_JOBS.values(),
        key=lambda j: j.get("created_at") or "",
        reverse=True,
    )
    return [_flatten_job(j) for j in jobs[:limit]]


def clear_memory_jobs() -> None:
    """Test helper — reset in-memory job store."""
    _MEMORY_JOBS.clear()