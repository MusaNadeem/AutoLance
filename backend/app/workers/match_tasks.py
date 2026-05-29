"""
Match & Alert Celery Tasks
Background job scoring and alert dispatch.
"""
import asyncio
from celery.utils.log import get_task_logger
from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.database import get_db_context
from app.models import MatchScore, AlertConfig, AlertEvent
from app.models.notification import Notification
from app.models.profile import FreelancerProfile
from app.models.job import Job
from app.models.user import User
from app.services.job_scorer import job_scorer_service
from app.services.notification import notification_service

logger = get_task_logger(__name__)


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
                    match = await job_scorer_service.score_job(
                        db=db,
                        user_id=user.id,
                        job_id=job.id,
                        profile_id=profile.id,
                    )
                    # Check alerts
                    await _check_and_dispatch_alert(db, user, job, match)
                    # Commit per-job so scores appear incrementally and a single
                    # failure doesn't roll back the whole batch.
                    await db.commit()
                except Exception as e:
                    await db.rollback()
                    logger.error(
                        "Scoring failed",
                        user_id=str(user.id),
                        job_id=str(job.id),
                        error=str(e),
                    )


async def _check_and_dispatch_alert(db, user: User, job: Job, match: MatchScore):
    """Check if a match triggers an alert and dispatch notifications."""
    # Load alert config
    config_result = await db.execute(
        select(AlertConfig).where(
            AlertConfig.user_id == user.id,
            AlertConfig.is_active == True,
        )
    )
    config = config_result.scalar_one_or_none()
    if not config:
        return

    # Check thresholds
    if match.overall_score < config.min_match_score:
        return
    if job.proposal_count > config.max_proposal_count:
        return
    if (match.client_quality_score or 0) < config.min_client_quality_score:
        return

    # Hours since posted
    if job.posted_at:
        from datetime import datetime, timezone
        hours_since = (datetime.now(timezone.utc) - job.posted_at).total_seconds() / 3600
        if hours_since > config.max_hours_since_posted:
            return

    trigger_reason = (
        f"Match score: {match.overall_score}/100 | "
        f"Proposals: {job.proposal_count} | "
        f"Client quality: {match.client_quality_score}/100"
    )

    # Phase 2: Insert in-app Notification (deduped — one per job per user)
    existing_notif = await db.execute(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.job_id == job.id,
            Notification.is_read == False,
        )
    )
    if not existing_notif.scalar_one_or_none():
        db.add(Notification(
            user_id=user.id,
            job_id=job.id,
            job_title=job.title,
            score=match.overall_score,
            message=(
                f"New {match.overall_score}/100 match: {job.title[:80]}. "
                f"{job.proposal_count} proposal{'s' if job.proposal_count != 1 else ''} so far."
            ),
            is_read=False,
        ))

    # Dispatch external notifications
    if config.notify_slack and config.slack_webhook_url:
        await notification_service.send_slack(
            webhook_url=config.slack_webhook_url,
            job_title=job.title,
            match_score=match.overall_score,
            job_url=job.url or "",
            client_tier="high",
            reasons=match.strengths or [],
        )
        _log_alert_event(db, user.id, job.id, match.id, trigger_reason, "slack")

    if config.notify_email:
        await notification_service.send_email(
            to_email=user.email,
            to_name=user.full_name or "Freelancer",
            job_title=job.title,
            match_score=match.overall_score,
            job_url=job.url or "",
            dashboard_url="https://app.autolance.io/dashboard",
        )
        _log_alert_event(db, user.id, job.id, match.id, trigger_reason, "email")


def _log_alert_event(db, user_id, job_id, match_id, trigger_reason, channel):
    event = AlertEvent(
        user_id=user_id,
        job_id=job_id,
        match_score_id=match_id,
        trigger_reason=trigger_reason,
        channel=channel,
    )
    db.add(event)
