"""Saved Jobs Router — bookmark/unbookmark jobs, list saved jobs."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc

from app.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models import MatchScore
from app.models.saved_job import SavedJob
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/saved", tags=["Saved Jobs"])


def _serialize_job(j: Job, m: MatchScore | None) -> dict:
    score = None
    if m:
        score = {
            "overall":       round(m.overall_score / 100, 2),
            "skill_match":   round((m.skill_match_score or 0) / 100, 2),
            "roi":           round((m.budget_fit_score or 0) / 100, 2),
            "competition":   round((m.competition_score or 0) / 100, 2),
            "client_quality":round((m.client_quality_score or 0) / 100, 2),
        }
    return {
        "id":             str(j.id),
        "upwork_job_id":  j.upwork_job_id,
        "title":          j.title,
        "url":            j.url,
        "budget_type":    j.budget_type,
        "budget_min":     float(j.budget_min) if j.budget_min else None,
        "budget_max":     float(j.budget_max) if j.budget_max else None,
        "hourly_rate_min":float(j.hourly_rate_min) if j.hourly_rate_min else None,
        "hourly_rate_max":float(j.hourly_rate_max) if j.hourly_rate_max else None,
        "required_skills":j.required_skills or [],
        "experience_level":j.experience_level,
        "proposal_count": j.proposal_count,
        "proposal_tier":  j.proposal_tier,
        "posted_at":      j.posted_at,
        "score":          score,
        "is_saved":       True,
    }


@router.get("/")
async def list_saved(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all bookmarked jobs for the current user."""
    result = await db.execute(
        select(SavedJob, Job, MatchScore)
        .join(Job, SavedJob.job_id == Job.id)
        .outerjoin(
            MatchScore,
            (MatchScore.job_id == Job.id) & (MatchScore.user_id == current_user.id),
        )
        .where(SavedJob.user_id == current_user.id)
        .order_by(desc(SavedJob.saved_at))
    )
    rows = result.all()
    return [_serialize_job(j, m) for _, j, m in rows]


@router.post("/{job_id}", status_code=201)
async def save_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bookmark a job."""
    job_uuid = uuid.UUID(job_id)

    job_res = await db.execute(select(Job).where(Job.id == job_uuid))
    if not job_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    existing = await db.execute(
        select(SavedJob).where(SavedJob.user_id == current_user.id, SavedJob.job_id == job_uuid)
    )
    if existing.scalar_one_or_none():
        return {"detail": "Already saved"}

    db.add(SavedJob(user_id=current_user.id, job_id=job_uuid, saved_at=datetime.now(timezone.utc)))
    return {"detail": "Saved"}


@router.delete("/{job_id}", status_code=204)
async def unsave_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove bookmark."""
    await db.execute(
        delete(SavedJob).where(
            SavedJob.user_id == current_user.id,
            SavedJob.job_id == uuid.UUID(job_id),
        )
    )
