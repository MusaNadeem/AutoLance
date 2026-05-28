"""Matches, Cover Letters, Proposals, Alerts, Analytics Routers"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.user import User
from app.models import MatchScore, CoverLetter, Proposal, AlertConfig, AlertEvent
from app.models.job import Job
from app.models.profile import FreelancerProfile
from app.middleware.auth import get_current_user
from app.services.job_scorer import job_scorer_service
from app.services.cover_letter_gen import cover_letter_service

# ────────────────────────────────────────────────────────────────
# MATCHES ROUTER
# ────────────────────────────────────────────────────────────────
matches_router = APIRouter(prefix="/matches", tags=["AI Match Scores"])


@matches_router.get("/")
async def get_matches(
    min_score: int = Query(0, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get ranked job matches for current user."""
    result = await db.execute(
        select(MatchScore, Job)
        .join(Job, MatchScore.job_id == Job.id)
        .where(
            MatchScore.user_id == current_user.id,
            MatchScore.overall_score >= min_score,
            Job.is_active == True,
        )
        .order_by(desc(MatchScore.overall_score))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "match": _serialize_match(m),
            "job": {
                "id": str(j.id),
                "title": j.title,
                "url": j.url,
                "budget_type": j.budget_type,
                "budget_min": float(j.budget_min) if j.budget_min else None,
                "budget_max": float(j.budget_max) if j.budget_max else None,
                "required_skills": j.required_skills,
                "proposal_count": j.proposal_count,
                "proposal_tier": j.proposal_tier,
                "posted_at": j.posted_at,
            },
        }
        for m, j in rows
    ]


@matches_router.post("/{job_id}/score")
async def score_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI scoring for a specific job."""
    profile_result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="Upload your CV first to enable scoring")

    match = await job_scorer_service.score_job(
        db=db,
        user_id=current_user.id,
        job_id=uuid.UUID(job_id),
        profile_id=profile.id,
    )
    return _serialize_match(match)


def _serialize_match(m: MatchScore) -> dict:
    return {
        "id": str(m.id),
        "overall_score": m.overall_score,
        "confidence_score": m.confidence_score,
        "skill_match_score": m.skill_match_score,
        "semantic_relevance_score": m.semantic_relevance_score,
        "budget_fit_score": m.budget_fit_score,
        "win_probability": float(m.win_probability) if m.win_probability else None,
        "strengths": m.strengths,
        "weaknesses": m.weaknesses,
        "recommended_approach": m.recommended_approach,
        "ai_explanation": m.ai_explanation,
        "scored_at": m.scored_at,
    }


# ────────────────────────────────────────────────────────────────
# COVER LETTERS ROUTER
# ────────────────────────────────────────────────────────────────
cover_letters_router = APIRouter(prefix="/cover-letters", tags=["Cover Letters"])


class GenerateCoverLetterRequest(BaseModel):
    job_id: str
    style: str = "professional"
    tone: str = "professional"   # Phase 3: professional | friendly | bold
    custom_instructions: str = ""


@cover_letters_router.post("/generate", status_code=201)
async def generate_cover_letter(
    body: GenerateCoverLetterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a personalized cover letter for a job."""
    letter = await cover_letter_service.generate(
        db=db,
        user_id=current_user.id,
        job_id=uuid.UUID(body.job_id),
        style=body.style,
        tone=body.tone,
        custom_instructions=body.custom_instructions,
    )
    return {
        "id": str(letter.id),
        "content": letter.content,
        "style": letter.style,
        "tone": body.tone,
        "variant_index": letter.variant_index,
        "token_count": letter.token_count,
    }


@cover_letters_router.get("/")
async def list_cover_letters(
    job_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    query = select(CoverLetter).where(CoverLetter.user_id == current_user.id)
    if job_id:
        query = query.where(CoverLetter.job_id == _uuid.UUID(job_id))
    result = await db.execute(
        query.order_by(desc(CoverLetter.created_at)).limit(50)
    )
    letters = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "job_id": str(l.job_id),
            "style": l.style,
            "variant_index": l.variant_index,
            "is_edited": l.is_edited,
            "is_sent": l.is_sent,
            "created_at": l.created_at,
        }
        for l in letters
    ]


class UpdateCoverLetterRequest(BaseModel):
    content: str


@cover_letters_router.patch("/{letter_id}")
async def update_cover_letter(
    letter_id: str,
    body: UpdateCoverLetterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CoverLetter).where(
            CoverLetter.id == uuid.UUID(letter_id),
            CoverLetter.user_id == current_user.id,
        )
    )
    letter = result.scalar_one_or_none()
    if not letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")

    letter.content = body.content
    letter.is_edited = True
    return {"id": str(letter.id), "content": letter.content}


# ────────────────────────────────────────────────────────────────
# PROPOSALS ROUTER
# ────────────────────────────────────────────────────────────────
proposals_router = APIRouter(prefix="/proposals", tags=["Proposal Tracker"])

VALID_STATUSES = ["drafted", "sent", "viewed", "replied", "interview", "won", "lost"]


class CreateProposalRequest(BaseModel):
    job_id: str
    cover_letter_id: Optional[str] = None
    bid_amount: Optional[float] = None
    bid_type: Optional[str] = "fixed"
    notes: Optional[str] = None


@proposals_router.post("/", status_code=201)
async def create_proposal(
    body: CreateProposalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    proposal = Proposal(
        user_id=current_user.id,
        job_id=uuid.UUID(body.job_id),
        cover_letter_id=uuid.UUID(body.cover_letter_id) if body.cover_letter_id else None,
        bid_amount=body.bid_amount,
        bid_type=body.bid_type,
        notes=body.notes,
    )
    db.add(proposal)
    await db.flush()
    return {"id": str(proposal.id), "status": proposal.status}


@proposals_router.get("/")
async def list_proposals(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Proposal, Job, MatchScore)
        .join(Job, Proposal.job_id == Job.id)
        .outerjoin(
            MatchScore,
            (MatchScore.job_id == Proposal.job_id) & (MatchScore.user_id == current_user.id),
        )
        .where(Proposal.user_id == current_user.id)
    )
    if status:
        query = query.where(Proposal.status == status)
    query = query.order_by(desc(Proposal.created_at))

    result = await db.execute(query)
    rows = result.all()
    return [
        {
            "id": str(p.id),
            "job_id": str(p.job_id),
            "job_title": j.title if j else None,
            "job_url": j.url if j else None,
            "status": p.status,
            "bid_amount": float(p.bid_amount) if p.bid_amount else None,
            "bid_type": p.bid_type,
            "match_score": m.overall_score if m else None,
            "sent_at": p.sent_at,
            "outcome_value": float(p.outcome_value) if p.outcome_value else None,
            "notes": p.notes,
            "created_at": p.created_at,
        }
        for p, j, m in rows
    ]


class UpdateProposalStatusRequest(BaseModel):
    status: str
    outcome_value: Optional[float] = None


@proposals_router.patch("/{proposal_id}/status")
async def update_proposal_status(
    proposal_id: str,
    body: UpdateProposalStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    result = await db.execute(
        select(Proposal).where(
            Proposal.id == uuid.UUID(proposal_id),
            Proposal.user_id == current_user.id,
        )
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    proposal.status = body.status
    if body.status == "sent":
        proposal.sent_at = now
    elif body.status == "viewed":
        proposal.viewed_at = now
    elif body.status == "replied":
        proposal.replied_at = now
    elif body.status == "interview":
        proposal.interview_at = now
    elif body.status in ("won", "lost"):
        proposal.outcome_at = now
        if body.outcome_value:
            proposal.outcome_value = body.outcome_value

    return {"id": str(proposal.id), "status": proposal.status}


@proposals_router.get("/analytics")
async def proposal_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Proposal funnel analytics."""
    result = await db.execute(
        select(Proposal).where(Proposal.user_id == current_user.id)
    )
    proposals = result.scalars().all()

    total = len(proposals)
    sent = sum(1 for p in proposals if p.status != "drafted")
    replied = sum(1 for p in proposals if p.status in ["replied", "interview", "won", "lost"])
    won = sum(1 for p in proposals if p.status == "won")
    total_value = sum(float(p.outcome_value or 0) for p in proposals if p.status == "won")

    return {
        "total": total,
        "sent": sent,
        "replied": replied,
        "won": won,
        "lost": sum(1 for p in proposals if p.status == "lost"),
        "win_rate": round(won / sent * 100, 1) if sent > 0 else 0,
        "response_rate": round(replied / sent * 100, 1) if sent > 0 else 0,
        "total_revenue": total_value,
        "avg_project_value": round(total_value / won, 2) if won > 0 else 0,
    }


# ────────────────────────────────────────────────────────────────
# ALERTS ROUTER
# ────────────────────────────────────────────────────────────────
alerts_router = APIRouter(prefix="/alerts", tags=["Alert System"])


class AlertConfigRequest(BaseModel):
    min_match_score: int = 85
    max_proposal_count: int = 10
    max_hours_since_posted: int = 2
    min_client_quality_score: int = 60
    notify_slack: bool = False
    notify_email: bool = True
    notify_push: bool = True
    slack_webhook_url: Optional[str] = None


@alerts_router.get("/config")
async def get_alert_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()
    if not config:
        return {"message": "No alert config. POST to /alerts/config to create one."}
    return {
        "min_match_score": config.min_match_score,
        "max_proposal_count": config.max_proposal_count,
        "max_hours_since_posted": config.max_hours_since_posted,
        "min_client_quality_score": config.min_client_quality_score,
        "notify_slack": config.notify_slack,
        "notify_email": config.notify_email,
        "notify_push": config.notify_push,
        "is_active": config.is_active,
    }


@alerts_router.put("/config")
async def upsert_alert_config(
    body: AlertConfigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()

    if config:
        for field, value in body.model_dump().items():
            setattr(config, field, value)
    else:
        config = AlertConfig(user_id=current_user.id, **body.model_dump())
        db.add(config)

    return {"status": "saved"}


@alerts_router.get("/events")
async def alert_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertEvent, Job, MatchScore)
        .join(Job, AlertEvent.job_id == Job.id)
        .outerjoin(MatchScore, AlertEvent.match_score_id == MatchScore.id)
        .where(AlertEvent.user_id == current_user.id)
        .order_by(desc(AlertEvent.sent_at))
        .limit(50)
    )
    rows = result.all()
    return [
        {
            "id": str(e.id),
            "job_id": str(e.job_id),
            "job_title": j.title,
            "match_score": (m.overall_score if m else None),
            "trigger_reason": e.trigger_reason,
            "channel": e.channel,
            "sent_at": e.sent_at,
            "read_at": e.read_at,
            "is_actioned": e.is_actioned,
        }
        for e, j, m in rows
    ]


# ── Phase 2: In-app Notification inbox ───────────────────────────────────────

@alerts_router.get("/")
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/v1/alerts/
    Response: { unread_count: int, notifications: [...] }
    Polled by NotificationBell (60s) and alerts page.
    """
    from app.models.notification import Notification

    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712
    query = query.order_by(desc(Notification.created_at)).limit(limit)

    result = await db.execute(query)
    notifs = result.scalars().all()

    unread_count = sum(1 for n in notifs if not n.is_read)

    return {
        "unread_count": unread_count,
        "notifications": [
            {
                "id":         str(n.id),
                "job_id":     str(n.job_id) if n.job_id else None,
                "job_title":  n.job_title,
                "score":      n.score,
                "message":    n.message,
                "is_read":    n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifs
        ],
    }


@alerts_router.post("/read/{notification_id}", status_code=204)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """POST /api/v1/alerts/read/{id} — mark single notification read."""
    from app.models.notification import Notification

    result = await db.execute(
        select(Notification).where(
            Notification.id == uuid.UUID(notification_id),
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif:
        notif.is_read = True


@alerts_router.post("/read-all", status_code=204)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /api/v1/alerts/read-all
    Mark all unread notifications for current user as read.
    """
    from app.models.notification import Notification
    from sqlalchemy import update as _update

    await db.execute(
        _update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )

