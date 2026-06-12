"""
pipeline_runners.py — Shared pipeline execution logic (Phase 3)

Called by Celery workers and by in-process fallback when Redis is unavailable.
"""

import datetime
from typing import Any, Dict

from system_logger import log


def run_scrape(job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from repositories import jobs_repo
    from scraper import run_scraper
    from storage.leads_storage import save_leads

    jobs_repo.mark_running(job_id)
    try:
        email_leads, call_leads = run_scraper()
        if email_leads or call_leads:
            save_leads(email_leads, call_leads)
        result = {"leads_found": len(email_leads) + len(call_leads)}
        jobs_repo.mark_complete(job_id, result)
        return result
    except Exception as e:
        jobs_repo.mark_failed(job_id, str(e))
        raise


def run_agent(job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from repositories import jobs_repo
    from site_builder import process_lead
    from emailer import send_batch
    from storage.leads_storage import load_all_leads, update_lead
    from storage.outreach_storage import log_sent

    jobs_repo.mark_running(job_id)
    try:
        lead_ids = payload.get("lead_ids")
        send_emails = payload.get("send_emails", True)

        leads = [
            row for row in load_all_leads()
            if (not lead_ids or row.get("id") in lead_ids)
            and row.get("email_sent", "").lower() != "true"
        ]

        sites_built = 0
        emails_sent = 0
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

        if send_emails and demo_urls:
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

        result = {"sites_built": sites_built, "emails_sent": emails_sent}
        jobs_repo.mark_complete(job_id, result)
        return result
    except Exception as e:
        jobs_repo.mark_failed(job_id, str(e))
        raise


def run_followup(job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from repositories import jobs_repo
    from followup import run_followup as followup_fn

    jobs_repo.mark_running(job_id)
    try:
        sent = followup_fn()
        result = {"emails_sent": sent}
        jobs_repo.mark_complete(job_id, result)
        return result
    except Exception as e:
        jobs_repo.mark_failed(job_id, str(e))
        raise


def run_pipeline_cycle(job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from repositories import jobs_repo
    from agent import run_pipeline_cycle as cycle_fn

    jobs_repo.mark_running(job_id)
    try:
        cycle_fn()
        result = {"status": "cycle_complete"}
        jobs_repo.mark_complete(job_id, result)
        return result
    except Exception as e:
        jobs_repo.mark_failed(job_id, str(e))
        raise