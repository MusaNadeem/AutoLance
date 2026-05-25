"""
Scraping Celery Tasks
Scheduled Upwork job scraping via Bright Data.
"""
import asyncio
from datetime import datetime, timezone
from celery import shared_task
import structlog

from app.workers.celery_app import celery_app
from app.scraping.bright_data import bright_data
from app.scraping.pipeline import pipeline
from app.database import get_db_context
from app.models import ScrapingRun

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="app.workers.scrape_tasks.run_scheduled_scrape",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def run_scheduled_scrape(self):
    """
    Main scheduled scraping task — runs every 15 minutes.
    Triggers Bright Data collection, waits for results, ingests jobs.
    """
    logger.info("Starting scheduled scrape run")
    asyncio.get_event_loop().run_until_complete(_async_scrape(self))


async def _async_scrape(task):
    """Async scraping implementation."""
    started_at = datetime.now(timezone.utc)

    async with get_db_context() as db:
        # Create audit record
        run = ScrapingRun(
            run_type="scheduled",
            source="bright_data_ws",
            status="running",
            started_at=started_at,
        )
        db.add(run)
        await db.commit()

        try:
            # Trigger Bright Data collection
            snapshot_id = await bright_data.trigger_dataset_collection()
            logger.info(f"Snapshot triggered: {snapshot_id}")

            # Wait for results
            raw_jobs = await bright_data.wait_for_snapshot(snapshot_id)
            logger.info(f"Got {len(raw_jobs)} raw jobs from Bright Data")

            # Ingest jobs
            stats = await pipeline.ingest_batch(db, raw_jobs, str(run.id))

            # Update run record
            completed_at = datetime.now(timezone.utc)
            run.status = "completed"
            run.jobs_scraped = stats["total"]
            run.jobs_new = stats["new"]
            run.jobs_updated = stats["updated"]
            run.jobs_deduplicated = stats["deduplicated"]
            run.completed_at = completed_at
            run.duration_seconds = int((completed_at - started_at).total_seconds())

            # Trigger background matching for new jobs
            if stats["new"] > 0:
                from app.workers.match_tasks import score_new_jobs_for_all_users
                score_new_jobs_for_all_users.apply_async(queue="matching")

            logger.info("Scrape run complete", **stats)

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)[:1000]
            run.completed_at = datetime.now(timezone.utc)
            logger.error("Scrape run failed", error=str(e))
            raise task.retry(exc=e)


@celery_app.task(name="app.workers.scrape_tasks.manual_scrape")
def manual_scrape(urls: list[str] = None):
    """Trigger a manual scrape (user-initiated via POST /scrape/trigger)."""
    asyncio.get_event_loop().run_until_complete(_async_manual_scrape(urls))


async def _async_manual_scrape(urls):
    started_at = datetime.now(timezone.utc)

    async with get_db_context() as db:
        # ── Create audit record so GET /scrape/status shows is_running=true ──
        run = ScrapingRun(
            run_type="manual",
            source="bright_data_ws",
            status="running",
            started_at=started_at,
        )
        db.add(run)
        await db.commit()

        try:
            snapshot_id = await bright_data.trigger_dataset_collection(urls=urls)
            raw_jobs = await bright_data.wait_for_snapshot(snapshot_id)
            stats = await pipeline.ingest_batch(db, raw_jobs, str(run.id))

            # ── On success ───────────────────────────────────────────────────
            completed_at = datetime.now(timezone.utc)
            run.status = "completed"
            run.jobs_scraped = stats.get("total", 0)
            run.jobs_new = stats.get("new", 0)
            run.jobs_updated = stats.get("updated", 0)
            run.jobs_deduplicated = stats.get("deduplicated", 0)
            run.jobs_found = stats.get("new", 0)   # Phase 2 API field
            run.completed_at = completed_at
            run.duration_seconds = int((completed_at - started_at).total_seconds())

            # Trigger matching for new jobs
            if stats.get("new", 0) > 0:
                from app.workers.match_tasks import score_new_jobs_for_all_users
                score_new_jobs_for_all_users.apply_async(queue="matching")

            logger.info("Manual scrape complete", **stats)
            return stats

        except Exception as e:
            # ── On failure ───────────────────────────────────────────────────
            run.status = "failed"
            run.error_message = str(e)[:1000]
            run.completed_at = datetime.now(timezone.utc)
            logger.error("Manual scrape failed", error=str(e))
            raise

