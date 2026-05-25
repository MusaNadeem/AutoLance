"""
Match & Alert Celery Tasks
Background job scoring and alert dispatch.
"""
import asyncio
import structlog
from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.database import get_db_context
from app.models import MatchScore
from app.models.profile import FreelancerProfile
from app.models.job import Job
from app.models.user import User
from app.services.job_scorer import job_scorer_service
from app.services.notification import notification_service, alert_service

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.match_tasks.score_new_jobs_for_all_users")
def score_new_jobs_for_all_users():
    """Score all new/unscored jobs for every active user."""
    asyncio.get_event_loop().run_until_complete(_async_score_all())


async def _async_score_all():
    async with get_db_context() as db:
        # Get all users with profiles
        result = await db.execute(
            select(User).where(User.is_active == True)
        )
        users = result.scalars().all()

        for user in users:
            profile_result = await db.execute(
                select(FreelancerProfile).where(FreelancerProfile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()
            if not profile:
                continue

            # Get unscored jobs (no match_score yet)
            unscored_result = await db.execute(
                select(Job).where(
                    Job.is_active == True,
                    ~Job.id.in_(
                        select(MatchScore.job_id).where(MatchScore.user_id == user.id)
                    ),
                ).limit(50)
            )
            unscored_jobs = unscored_result.scalars().all()

            for job in unscored_jobs:
                try:
                    await job_scorer_service.score_job(
                        db=db,
                        user_id=user.id,
                        job_id=job.id,
                        profile_id=profile.id,
                    )
                except Exception as e:
                    logger.error(
                        "Scoring failed",
                        user_id=str(user.id),
                        job_id=str(job.id),
                        error=str(e),
                    )

            # ── Phase 2: Dispatch alerts once per user after all scoring ──────
            if unscored_jobs:
                try:
                    created = await alert_service.check_and_dispatch(
                        db=db,
                        user_id=user.id,
                        user_email=user.email,
                        user_name=user.full_name or "Freelancer",
                    )
                    if created:
                        logger.info(
                            "Alerts dispatched",
                            user_id=str(user.id),
                            count=created,
                        )
                except Exception as e:
                    logger.error(
                        "Alert dispatch failed",
                        user_id=str(user.id),
                        error=str(e),
                    )


