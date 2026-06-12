"""Celery tasks for FORGE pipeline jobs."""

from celery_app import celery_app
from pipeline_runners import run_agent, run_followup, run_pipeline_cycle, run_scrape


@celery_app.task(name="tasks.pipeline.scrape_task", bind=True, max_retries=2)
def scrape_task(self, job_id: str, payload: dict):
    try:
        return run_scrape(job_id, payload)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="tasks.pipeline.agent_task", bind=True, max_retries=2)
def agent_task(self, job_id: str, payload: dict):
    try:
        return run_agent(job_id, payload)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.pipeline.followup_task", bind=True, max_retries=2)
def followup_task(self, job_id: str, payload: dict):
    try:
        return run_followup(job_id, payload)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.pipeline.run_pipeline_cycle_task", bind=True, max_retries=1)
def run_pipeline_cycle_task(self, job_id: str = "", payload: dict = None):
    from repositories import jobs_repo

    payload = payload or {}
    if not job_id:
        job_id = jobs_repo.create("pipeline_cycle", payload)
    try:
        return run_pipeline_cycle(job_id, payload)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)