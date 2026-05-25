"""Jobs Router — Browse and filter scraped jobs"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, case
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.client import Client
from app.models import MatchScore
from app.middleware.auth import get_current_user
from app.workers.scrape_tasks import manual_scrape

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Valid sort options
_SORT_OPTIONS = {"score", "posted_at", "budget"}


@router.get("/")
async def list_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    # Phase 4 filter params
    sort_by: str = Query("posted_at", description="score | posted_at | budget"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum overall score (0-100)"),
    posted_within: Optional[int] = Query(None, ge=1, description="Only jobs posted within N hours"),
    # Legacy filter params (kept for compatibility)
    budget_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    proposal_tier: Optional[str] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    skills: Optional[str] = Query(None, description="Comma-separated skills"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paginated job feed with filtering and sorting.

    Phase 4 additions:
    - sort_by: score | posted_at | budget
    - min_score: filter by minimum overall match score (0-100)
    - posted_within: only jobs posted within N hours
    Returns `total` count for pagination.
    """
    if sort_by not in _SORT_OPTIONS:
        sort_by = "posted_at"

    # ── Base query ────────────────────────────────────────────────────────────
    query = select(Job).where(Job.is_active == True)

    # ── Legacy filters ────────────────────────────────────────────────────────
    if budget_type:
        query = query.where(Job.budget_type == budget_type)
    if experience_level:
        query = query.where(Job.experience_level == experience_level)
    if proposal_tier:
        query = query.where(Job.proposal_tier == proposal_tier)
    if min_budget:
        query = query.where(Job.budget_min >= min_budget)
    if max_budget:
        query = query.where(Job.budget_max <= max_budget)

    # ── Phase 4: posted_within filter ─────────────────────────────────────────
    if posted_within:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=posted_within)
        query = query.where(Job.posted_at >= cutoff)

    # ── Phase 4: Sorting ──────────────────────────────────────────────────────
    if sort_by == "budget":
        query = query.order_by(desc(Job.budget_max), desc(Job.posted_at))
    else:
        # Default: posted_at. score is handled post-fetch (after joining match scores).
        query = query.order_by(desc(Job.posted_at))

    # ── Count total matching jobs (for pagination) ────────────────────────────
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total: int = total_result.scalar() or 0

    # ── Fetch page ────────────────────────────────────────────────────────────
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()

    # ── Batch-fetch current user's latest match score per job ─────────────────
    match_scores_by_job: dict[UUID, MatchScore] = {}
    if jobs:
        job_ids = [j.id for j in jobs]
        ms_result = await db.execute(
            select(MatchScore)
            .where(
                MatchScore.user_id == current_user.id,
                MatchScore.job_id.in_(job_ids),
            )
            .order_by(desc(MatchScore.scored_at))
        )
        for ms in ms_result.scalars().all():
            if ms.job_id not in match_scores_by_job:
                match_scores_by_job[ms.job_id] = ms

    # ── Phase 4: min_score filter ─────────────────────────────────────────────
    # Applied post-fetch since score lives in MatchScore, not Job.
    serialized = [_serialize_job(j, match_scores_by_job.get(j.id)) for j in jobs]
    if min_score is not None:
        serialized = [
            s for s in serialized
            if s["score"]["overall"] is not None
            and round(s["score"]["overall"] * 100) >= min_score
        ]

    # ── Phase 4: sort_by=score (post-fetch) ───────────────────────────────────
    if sort_by == "score":
        serialized.sort(
            key=lambda s: (s["score"]["overall"] or 0),
            reverse=True,
        )

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "jobs": serialized,
    }


@router.get("/stats")
async def scraping_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get scraping statistics."""
    from app.models import ScrapingRun
    result = await db.execute(
        select(ScrapingRun).order_by(desc(ScrapingRun.started_at)).limit(10)
    )
    runs = result.scalars().all()

    total_jobs = await db.execute(select(func.count(Job.id)))
    active_jobs = await db.execute(
        select(func.count(Job.id)).where(Job.is_active == True)
    )

    return {
        "total_jobs": total_jobs.scalar(),
        "active_jobs": active_jobs.scalar(),
        "recent_runs": [
            {
                "id": str(r.id),
                "status": r.status,
                "jobs_scraped": r.jobs_scraped,
                "jobs_new": r.jobs_new,
                "started_at": r.started_at,
                "duration_seconds": r.duration_seconds,
            }
            for r in runs
        ],
    }


@router.post("/trigger-scrape")
async def trigger_scrape(current_user: User = Depends(get_current_user)):
    """Manually trigger a job scraping run."""
    manual_scrape.apply_async(queue="scraping")
    return {"status": "triggered", "message": "Scraping job queued"}


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed job info including client data."""
    import uuid as _uuid
    result = await db.execute(
        select(Job).where(Job.id == _uuid.UUID(job_id))
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    client = None
    if job.client_id:
        client_result = await db.execute(
            select(Client).where(Client.id == job.client_id)
        )
        client = client_result.scalar_one_or_none()

    # Fetch latest match score for current user
    ms_result = await db.execute(
        select(MatchScore)
        .where(
            MatchScore.user_id == current_user.id,
            MatchScore.job_id == job.id,
        )
        .order_by(desc(MatchScore.scored_at))
        .limit(1)
    )
    match_score = ms_result.scalar_one_or_none()

    return {**_serialize_job(job, match_score), "client": _serialize_client(client)}


def _serialize_job(job: Job, match_score: Optional[MatchScore] = None) -> dict:
    # ── Base fields (all original — never removed) ────────────────────────────
    data: dict = {
        "id":               str(job.id),
        "upwork_job_id":    job.upwork_job_id,
        "title":            job.title,
        "description":      job.description,
        "url":              job.url,
        "budget_type":      job.budget_type,
        "budget_min":       float(job.budget_min)       if job.budget_min       else None,
        "budget_max":       float(job.budget_max)       if job.budget_max       else None,
        "hourly_rate_min":  float(job.hourly_rate_min)  if job.hourly_rate_min  else None,
        "hourly_rate_max":  float(job.hourly_rate_max)  if job.hourly_rate_max  else None,
        "required_skills":  job.required_skills,
        "experience_level": job.experience_level,
        "project_length":   job.project_length,
        "proposal_count":   job.proposal_count,
        "proposal_tier":    job.proposal_tier,
        "posted_at":        job.posted_at,
        "scraped_at":       job.scraped_at,
    }

    # ── Phase 1: score object — all 4 signals ────────────────────────────────
    # client_quality comes from the Job row (computed at ingestion time).
    # skill_match, roi, competition come from the user's latest MatchScore.
    # All values are normalised to 0.0–1.0 for the frontend.
    cq = float(job.client_quality_score) if job.client_quality_score is not None else None

    def _pct_to_ratio(v) -> Optional[float]:
        """MatchScore stores 0-100 integers; convert to 0.0-1.0 for API."""
        return round(float(v) / 100.0, 4) if v is not None else None

    data["score"] = {
        "overall":        _pct_to_ratio(match_score.overall_score)         if match_score else None,
        "skill_match":    _pct_to_ratio(match_score.skill_match_score)     if match_score else None,
        "roi":            _pct_to_ratio(match_score.semantic_relevance_score) if match_score else None,
        "competition":    _pct_to_ratio(match_score.competition_score)     if match_score else None,
        "client_quality": cq,
    }

    # ── Phase 1: bid object (null when job hasn't been scored yet) ────────────
    if job.bid_strategy is not None:
        r_min = float(job.bid_range_min) if job.bid_range_min is not None else None
        r_max = float(job.bid_range_max) if job.bid_range_max is not None else None
        recommended = round((r_min + r_max) / 2, 2) if (r_min and r_max) else None
        data["bid"] = {
            "recommended": recommended,
            "range_min":   r_min,
            "range_max":   r_max,
            "range":       f"${r_min:.2f} \u2013 ${r_max:.2f} acceptable range"
                           if (r_min and r_max) else None,
            "strategy":    job.bid_strategy,
            "rationale":   job.bid_rationale,
            "confidence":  float(job.bid_confidence) if job.bid_confidence is not None else None,
        }
    else:
        data["bid"] = None

    return data


def _serialize_client(client: Optional[Client]) -> Optional[dict]:
    if not client:
        return None
    return {
        "id": str(client.id),
        "country": client.country,
        "payment_verified": client.payment_verified,
        "total_spent": float(client.total_spent) if client.total_spent else None,
        "hire_rate": float(client.hire_rate) if client.hire_rate else None,
        "total_hires": client.total_hires,
        "average_rating": float(client.average_rating) if client.average_rating else None,
        "quality_tier": client.quality_tier,
        "quality_score": client.quality_score,
        "trust_score": client.trust_score,
        "red_flags": client.red_flags,
        "green_flags": client.green_flags,
    }
