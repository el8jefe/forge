"""
celery_app.py — FORGE Celery application (Phase 3)

Workers process scrape, agent, followup, and scheduled pipeline tasks.
Start worker:  celery -A celery_app worker --loglevel=info
Start beat:    celery -A celery_app beat --loglevel=info
"""

import os
import sys

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)

from celery import Celery
from celery.schedules import crontab

from config import settings

celery_app = Celery(
    "forge",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=["tasks.pipeline"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="forge",
    beat_schedule={
        "pipeline-cycle-6h": {
            "task": "tasks.pipeline.run_pipeline_cycle_task",
            "schedule": crontab(minute=0, hour="0,6,12,18"),
        },
    },
)