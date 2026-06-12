"""
api.py — FORGE REST API
Wraps the FORGE pipeline as HTTP endpoints so Tradebuilt can call it.

Start: python3 api.py
Default port: 8000
"""

import os
import datetime
from typing import Optional, List

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from api_auth import PUBLIC_PATHS, is_auth_enabled, validate_api_key
from config import settings
from job_dispatcher import celery_available, dispatch
from repositories import jobs_repo
from routes.build import router as build_router
from routes.stripe import router as stripe_router
from system_logger import log

load_dotenv()

_docs_url = "/docs" if settings.forge_openapi_enabled else None
_redoc_url = "/redoc" if settings.forge_openapi_enabled else None
_openapi_url = "/openapi.json" if settings.forge_openapi_enabled else None

app = FastAPI(
    title="FORGE API",
    version="3.4",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

_cors_origins = settings.cors_origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stripe_router)
app.include_router(build_router)


@app.middleware("http")
async def require_forge_api_key(request: Request, call_next):
    """Phase 0: reject unauthenticated requests except public paths."""
    path = request.url.path
    if path in PUBLIC_PATHS or request.method == "OPTIONS":
        return await call_next(request)
    if not validate_api_key(
        request.headers.get("Authorization"),
        request.headers.get("X-FORGE-API-Key"),
    ):
        status = 503 if is_auth_enabled() and not settings.forge_api_key.strip() else 401
        detail = (
            "FORGE_API_KEY is not configured on the server"
            if status == 503
            else "Missing or invalid API key"
        )
        return JSONResponse(status_code=status, content={"detail": detail})
    return await call_next(request)


# ── Request models ────────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    business_types: Optional[List[str]] = None  # None = all 26 types
    states: Optional[List[str]] = None          # None = all 20 target states
    max_leads: int = 100


class RunAgentRequest(BaseModel):
    lead_ids: Optional[List[str]] = None   # None = process all pending leads
    approval_mode: bool = False
    send_emails: bool = True


class UpdateLeadRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    approved: Optional[bool] = None


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    from mail.sender import active_provider
    from storage import backend_name

    return {
        "status": "ok",
        "version": "3.4",
        "forge": "running",
        "storage": backend_name(),
        "email": active_provider(),
        "celery": celery_available(),
        "role": settings.forge_role,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


# ── Leads ─────────────────────────────────────────────────────────────────────

@app.get("/leads")
def get_leads(
    status: Optional[str] = None,
    business_type: Optional[str] = None,
    state: Optional[str] = None,
    tier: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Return leads from Supabase with optional filters."""
    try:
        from db import get_leads as db_get_leads
        filters = {}
        if status:        filters["status"] = status
        if business_type: filters["business_type"] = business_type
        if state:         filters["state"] = state
        if tier:          filters["lead_tier"] = tier
        leads = db_get_leads(filters=filters, limit=limit, offset=offset)
        return {"leads": leads, "total": len(leads)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/leads/{lead_id}")
def update_lead(lead_id: str, body: UpdateLeadRequest):
    """Update lead status, notes, or approval."""
    try:
        from db import update_lead as db_update_lead
        updates = {k: v for k, v in body.dict().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        result = db_update_lead(lead_id, updates)
        return {"lead": result[0] if result else None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Scrape ────────────────────────────────────────────────────────────────────

@app.post("/scrape")
def start_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    """Kick off a background scrape run."""
    job_id = dispatch("scrape", req.dict(), background_tasks=background_tasks)
    return {"job_id": job_id, "status": "running"}


# ── Agent (build sites + send emails) ────────────────────────────────────────

@app.post("/run-agent")
def run_agent(req: RunAgentRequest, background_tasks: BackgroundTasks):
    """Build demo sites and send outreach emails for pending leads."""
    job_id = dispatch("agent", req.dict(), background_tasks=background_tasks)
    return {"job_id": job_id, "status": "running"}


# ── Follow-up ─────────────────────────────────────────────────────────────────

@app.post("/followup")
def run_followup_endpoint(background_tasks: BackgroundTasks):
    """Send 3-day follow-up emails to non-responders."""
    job_id = dispatch("followup", {}, background_tasks=background_tasks)
    return {"job_id": job_id, "status": "running"}


# ── Pipeline cycle (full agent cycle) ─────────────────────────────────────────

@app.post("/run-pipeline")
def run_pipeline(background_tasks: BackgroundTasks):
    """Run one full pipeline cycle (scrape → build → send)."""
    job_id = dispatch("pipeline_cycle", {}, background_tasks=background_tasks)
    return {"job_id": job_id, "status": "running"}


# ── Job status ────────────────────────────────────────────────────────────────

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs_repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/jobs")
def list_jobs(limit: int = 50):
    return {"jobs": jobs_repo.list_jobs(limit=limit)}


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/stats")
def get_stats():
    try:
        from db import get_stats as db_get_stats
        return db_get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("FORGE_API_PORT", "8000"))
    print(f"[FORGE API] Starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)