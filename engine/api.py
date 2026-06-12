"""
api.py — FORGE REST API
Wraps the FORGE pipeline as HTTP endpoints so Tradebuilt can call it.

Start: python3 api.py
Default port: 8000
"""

import os
import uuid
import threading
import datetime
from typing import Optional, List

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from api_auth import PUBLIC_PATHS, is_auth_enabled, validate_api_key
from config import settings
from system_logger import log

load_dotenv()

app = FastAPI(title="FORGE API", version="3.1")

_cors_origins = settings.cors_origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

# ── In-memory job tracker (replaced by Supabase in production) ──────────────
_jobs: dict = {}


def _new_job(job_type: str, params: dict) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "id": job_id,
        "type": job_type,
        "status": "running",
        "params": params,
        "leads_found": 0,
        "sites_built": 0,
        "emails_sent": 0,
        "started_at": datetime.datetime.utcnow().isoformat(),
        "completed_at": None,
        "error": None,
    }
    return job_id


def _finish_job(job_id: str, result: dict = None, error: str = None):
    if job_id not in _jobs:
        return
    _jobs[job_id]["status"] = "failed" if error else "complete"
    _jobs[job_id]["completed_at"] = datetime.datetime.utcnow().isoformat()
    if error:
        _jobs[job_id]["error"] = error
    if result:
        _jobs[job_id].update(result)


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
    return {
        "status": "ok",
        "version": "3.0",
        "forge": "running",
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
        from db import update_lead
        updates = {k: v for k, v in body.dict().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        result = update_lead(lead_id, updates)
        return {"lead": result[0] if result else None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Scrape ────────────────────────────────────────────────────────────────────

def _run_scrape(job_id: str, req: ScrapeRequest):
    try:
        from scraper import run_scraper
        from storage.leads_storage import save_leads

        email_leads, call_leads = run_scraper()
        if email_leads or call_leads:
            save_leads(email_leads, call_leads)

        _finish_job(job_id, {"leads_found": len(email_leads) + len(call_leads)})
    except Exception as e:
        _finish_job(job_id, error=str(e))


@app.post("/scrape")
def start_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    """Kick off a background scrape run."""
    job_id = _new_job("scrape", req.dict())
    background_tasks.add_task(_run_scrape, job_id, req)
    return {"job_id": job_id, "status": "running"}


# ── Agent (build sites + send emails) ────────────────────────────────────────

def _run_agent(job_id: str, req: RunAgentRequest):
    try:
        from site_builder import process_lead
        from emailer import send_batch
        from storage.leads_storage import load_all_leads, update_lead
        from storage.outreach_storage import log_sent

        sites_built = 0
        emails_sent = 0

        leads = [
            row for row in load_all_leads()
            if (not req.lead_ids or row.get("id") in req.lead_ids)
            and row.get("email_sent", "").lower() != "true"
        ]

        demo_urls: dict = {}
        for lead in leads:
            name = (lead.get("business_name") or lead.get("name", "")).strip()
            try:
                demo_url = process_lead(lead)
                sites_built += 1
                if demo_url and name:
                    demo_urls[name] = demo_url
                    update_lead(name, {"demo_site_path": demo_url})
                elif lead.get("demo_site_path"):
                    demo_urls[name] = lead["demo_site_path"]
            except Exception as e:
                log("run_agent", "ERROR", f"site build {name}: {e}")

        if req.send_emails and demo_urls:
            sent, _failed, sent_names = send_batch(leads, demo_urls, stagger=True)
            emails_sent = sent
            sent_set = {n.lower() for n in sent_names}
            for lead in leads:
                name = (lead.get("business_name") or "").strip()
                if name.lower() in sent_set:
                    log_sent(lead, demo_urls.get(name, ""))
                    update_lead(name, {
                        "email_sent": "true",
                        "email_sent_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                    })

        _finish_job(job_id, {"sites_built": sites_built, "emails_sent": emails_sent})
    except Exception as e:
        _finish_job(job_id, error=str(e))


@app.post("/run-agent")
def run_agent(req: RunAgentRequest, background_tasks: BackgroundTasks):
    """Build demo sites and send outreach emails for pending leads."""
    job_id = _new_job("agent", req.dict())
    background_tasks.add_task(_run_agent, job_id, req)
    return {"job_id": job_id, "status": "running"}


# ── Follow-up ─────────────────────────────────────────────────────────────────

def _run_followup(job_id: str):
    try:
        from followup import run_followup
        sent = run_followup()
        _finish_job(job_id, {"emails_sent": sent})
    except Exception as e:
        _finish_job(job_id, error=str(e))


@app.post("/followup")
def run_followup_endpoint(background_tasks: BackgroundTasks):
    """Send 3-day follow-up emails to non-responders."""
    job_id = _new_job("followup", {})
    background_tasks.add_task(_run_followup, job_id)
    return {"job_id": job_id, "status": "running"}


# ── Job status ────────────────────────────────────────────────────────────────

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/jobs")
def list_jobs():
    return {"jobs": list(_jobs.values())}


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
