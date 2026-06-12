"""
job_dispatcher.py — Enqueue pipeline work via Celery or in-process fallback (Phase 3)
"""

from typing import Callable, Dict, Optional

from fastapi import BackgroundTasks

from config import settings
from repositories import jobs_repo
from system_logger import log

_RUNNERS: Dict[str, Callable] = {}


def _register_runners():
    if _RUNNERS:
        return
    from pipeline_runners import run_agent, run_followup, run_pipeline_cycle, run_scrape
    _RUNNERS.update({
        "scrape": run_scrape,
        "agent": run_agent,
        "followup": run_followup,
        "pipeline_cycle": run_pipeline_cycle,
    })


def celery_available() -> bool:
    if not settings.use_celery:
        return False
    return bool(settings.celery_broker.strip())


def _celery_task_for(job_type: str):
    from tasks import pipeline as task_module
    return {
        "scrape": task_module.scrape_task,
        "agent": task_module.agent_task,
        "followup": task_module.followup_task,
        "pipeline_cycle": task_module.run_pipeline_cycle_task,
    }.get(job_type)


def dispatch(
    job_type: str,
    payload: Optional[dict] = None,
    *,
    background_tasks: Optional[BackgroundTasks] = None,
) -> str:
    """Create a job record and enqueue execution. Returns job_id."""
    _register_runners()
    payload = payload or {}
    job_id = jobs_repo.create(job_type, payload)

    if celery_available():
        task = _celery_task_for(job_type)
        if task:
            try:
                task.delay(job_id, payload)
                log("job_dispatcher", "INFO", f"celery enqueued {job_type} job={job_id}")
                return job_id
            except Exception as e:
                log("job_dispatcher", "WARNING", f"celery enqueue failed, falling back: {e}")

    runner = _RUNNERS.get(job_type)
    if not runner:
        jobs_repo.mark_failed(job_id, f"unknown job type: {job_type}")
        raise ValueError(f"Unknown job type: {job_type}")

    if background_tasks is not None:
        background_tasks.add_task(runner, job_id, payload)
        log("job_dispatcher", "INFO", f"background task {job_type} job={job_id}")
    else:
        runner(job_id, payload)
        log("job_dispatcher", "INFO", f"sync {job_type} job={job_id}")

    return job_id