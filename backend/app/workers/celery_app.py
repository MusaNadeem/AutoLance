"""
Celery Application Configuration
"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "autolance",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.scrape_tasks",
        "app.workers.match_tasks",
        "app.workers.alert_tasks",
    ],
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
    task_routes={
        "app.workers.scrape_tasks.*": {"queue": "scraping"},
        "app.workers.match_tasks.*": {"queue": "matching"},
        "app.workers.alert_tasks.*": {"queue": "alerts"},
    },
    # Retry policies
    task_max_retries=3,
    task_default_retry_delay=30,
    # Beat schedule
    beat_schedule={
        "scrape-upwork-jobs": {
            "task": "app.workers.scrape_tasks.run_scheduled_scrape",
            "schedule": crontab(minute=f"*/{settings.SCRAPE_INTERVAL_MINUTES}"),
            "options": {"queue": "scraping"},
        },
    },
)
