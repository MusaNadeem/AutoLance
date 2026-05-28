"""Scrape Status Router — Phase 2
Provides real-time scrape observability endpoints.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User
from app.models import ScrapingRun
from app.middleware.auth import get_current_user

scrape_router = APIRouter(prefix="/scrape", tags=["Scrape Status"])

# Scrape runs every 15 minutes (matches Celery beat schedule)
_SCRAPE_INTERVAL_MINUTES = 15


@scrape_router.get("/status")
async def get_scrape_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the last scrape run, whether a scrape is currently running,
    and when the next scheduled scrape will occur.
    """
    result = await db.execute(
        select(ScrapingRun)
        .order_by(desc(ScrapingRun.started_at))
        .limit(1)
    )
    last_run: Optional[ScrapingRun] = result.scalar_one_or_none()

    is_running = last_run is not None and last_run.status == "running"

    # Compute next_run_at: N minutes after the last completed run
    next_run_at: Optional[datetime] = None
    if last_run and last_run.started_at:
        base = last_run.completed_at or last_run.started_at
        next_run_at = base + timedelta(minutes=_SCRAPE_INTERVAL_MINUTES)
        # If next_run_at is in the past, bump to now + interval
        if next_run_at < datetime.now(timezone.utc):
            next_run_at = datetime.now(timezone.utc) + timedelta(minutes=_SCRAPE_INTERVAL_MINUTES)

    return {
        "is_running": is_running,
        "next_run_at": next_run_at.isoformat() if next_run_at else None,
        "last_run": _serialize_run(last_run) if last_run else None,
    }


@scrape_router.post("/trigger")
async def trigger_scrape(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger a scrape. Queues the Celery task immediately.
    Returns 409 if a scrape is already running.
    """
    # Check if already running
    result = await db.execute(
        select(ScrapingRun)
        .where(ScrapingRun.status == "running")
        .limit(1)
    )
    running = result.scalar_one_or_none()
    if running:
        raise HTTPException(status_code=409, detail="A scrape is already running")

    # Require the user to have a scanned CV profile before scraping.
    # The niche and top skills from the profile determine what gets searched.
    from app.models.profile import FreelancerProfile
    profile_result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    if not profile or not (profile.skills or profile.niche):
        raise HTTPException(
            status_code=400,
            detail="Upload and scan your CV first. AutoLance uses your niche and skills to find relevant jobs.",
        )

    # Build targeted keywords from the user's profile.
    seen: set[str] = set()
    keywords: list[str] = []

    # 1. Niche is the primary keyword — most specific signal
    if profile.niche:
        keywords.append(profile.niche)
        seen.add(profile.niche.lower())

    # 2. Top skills sorted by years of experience (up to 5 more)
    skills: list[dict] = profile.skills or []
    for s in sorted(skills, key=lambda s: s.get("years", 0), reverse=True):
        name = (s.get("name") or "").strip()
        if name and name.lower() not in seen and len(keywords) < 6:
            keywords.append(name)
            seen.add(name.lower())

    # 3. Specializations to round out to max 6 keywords
    for spec in (profile.specializations or []):
        spec = (spec or "").strip()
        if spec and spec.lower() not in seen and len(keywords) < 6:
            keywords.append(spec)
            seen.add(spec.lower())

    from app.workers.scrape_tasks import manual_scrape
    task = manual_scrape.apply_async(args=[keywords], queue="scraping")
    return {"task_id": task.id, "queued": True, "keywords": keywords}


@scrape_router.get("/history")
async def scrape_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return last N scrape runs."""
    result = await db.execute(
        select(ScrapingRun)
        .order_by(desc(ScrapingRun.started_at))
        .limit(limit)
    )
    runs = result.scalars().all()
    return [_serialize_run(r) for r in runs]


def _serialize_run(run: ScrapingRun | None) -> dict | None:
    if run is None:
        return None
    return {
        "id":               str(run.id),
        "status":           run.status,
        "started_at":       run.started_at.isoformat()   if run.started_at   else None,
        "completed_at":     run.completed_at.isoformat() if run.completed_at else None,
        "duration_seconds": run.duration_seconds,
        "jobs_found":       run.jobs_scraped or 0,   # total jobs seen in this run
        "jobs_scraped":     run.jobs_scraped or 0,
        "jobs_new":         run.jobs_new     or 0,
        "error_message":    (run.error_message or "")[:200] if run.error_message else None,
    }
