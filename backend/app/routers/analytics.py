"""Analytics Router — Phase 4 dashboard data"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from collections import Counter, defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text

from app.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models import MatchScore
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/")
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/v1/analytics

    Returns aggregated analytics data for the dashboard:
    - jobs_scraped_total: total active jobs in DB
    - avg_score: average overall match score (0-100) for this user
    - score_distribution: 4 buckets (0-25, 25-50, 50-75, 75-100)
    - top_skills_in_demand: top 10 skills from all active jobs
    - scrape_history: last 7 scraping runs
    """

    # ── 1. Total jobs scraped ─────────────────────────────────────────────────
    total_result = await db.execute(
        select(func.count(Job.id)).where(Job.is_active == True)
    )
    jobs_scraped_total: int = total_result.scalar() or 0

    # ── 2. User's match scores for avg + distribution ─────────────────────────
    scores_result = await db.execute(
        select(MatchScore.overall_score)
        .where(MatchScore.user_id == current_user.id)
        .order_by(desc(MatchScore.scored_at))
        .limit(500)  # cap for performance
    )
    raw_scores = [row[0] for row in scores_result.all() if row[0] is not None]

    avg_score: int = round(sum(raw_scores) / len(raw_scores)) if raw_scores else 0

    # Score distribution — 4 buckets. Scores are stored as 0-100 integers.
    buckets = {"0-25": 0, "25-50": 0, "50-75": 0, "75-100": 0}
    for s in raw_scores:
        if s <= 25:
            buckets["0-25"] += 1
        elif s <= 50:
            buckets["25-50"] += 1
        elif s <= 75:
            buckets["50-75"] += 1
        else:
            buckets["75-100"] += 1

    score_distribution = [
        {"bucket": k, "count": v} for k, v in buckets.items()
    ]

    # ── 3. Top skills in demand (from active jobs) ────────────────────────────
    skills_result = await db.execute(
        select(Job.required_skills)
        .where(Job.is_active == True, Job.required_skills.isnot(None))
        .limit(500)
    )
    skill_counter: Counter = Counter()
    for (skills_json,) in skills_result.all():
        if isinstance(skills_json, list):
            for skill in skills_json:
                if isinstance(skill, str) and skill.strip():
                    skill_counter[skill.strip()] += 1

    top_skills_in_demand = [
        {"skill": skill, "count": count}
        for skill, count in skill_counter.most_common(10)
    ]

    # ── 4. Scrape history — last 7 runs ───────────────────────────────────────
    try:
        from app.models import ScrapingRun
        runs_result = await db.execute(
            select(ScrapingRun)
            .order_by(desc(ScrapingRun.started_at))
            .limit(7)
        )
        runs = runs_result.scalars().all()
        scrape_history = [
            {
                "date": r.started_at.strftime("%Y-%m-%d") if r.started_at else None,
                "jobs_found": r.jobs_scraped or 0,
                "jobs_new": r.jobs_new or 0,
                "status": r.status,
            }
            for r in reversed(runs)  # chronological order for the chart
        ]
    except Exception:
        scrape_history = []

    return {
        "jobs_scraped_total": jobs_scraped_total,
        "avg_score": avg_score,
        "score_distribution": score_distribution,
        "top_skills_in_demand": top_skills_in_demand,
        "scrape_history": scrape_history,
    }
