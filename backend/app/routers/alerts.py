"""Alerts Router — Phase 2
Notification inbox: list, mark-read, config CRUD.
Separate from the legacy alert_events router in __init__.py.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update

from app.database import get_db
from app.models.user import User
from app.models import AlertConfig
from app.models.notification import Notification
from app.middleware.auth import get_current_user

alerts_router = APIRouter(prefix="/alerts", tags=["Notifications"])


# ── Notification endpoints ────────────────────────────────────────────────────

@alerts_router.get("/")
async def list_alerts(
    limit: int = 50,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return notifications for the current user, newest first."""
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
    )
    if unread_only:
        query = query.where(Notification.is_read == False)

    result = await db.execute(query)
    notifications = result.scalars().all()

    unread_count = sum(1 for n in notifications if not n.is_read)

    return {
        "unread_count": unread_count,
        "notifications": [_serialize_notification(n) for n in notifications],
    }


@alerts_router.post("/read/{alert_id}", status_code=204)
async def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a single notification as read."""
    import uuid as _uuid
    result = await db.execute(
        select(Notification).where(
            Notification.id == _uuid.UUID(alert_id),
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    return Response(status_code=204)


@alerts_router.post("/read-all", status_code=204)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all of the current user's notifications as read."""
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .values(is_read=True)
    )
    return Response(status_code=204)


# ── Alert config endpoints ────────────────────────────────────────────────────

class AlertConfigBody(BaseModel):
    score_threshold: float = 0.75          # 0.0–1.0
    slack_webhook_url: Optional[str] = None
    email_address: Optional[str] = None
    enabled: bool = True


@alerts_router.get("/config")
async def get_alert_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the user's alert configuration (or sensible defaults)."""
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        # Return defaults — no row needed yet
        return {
            "score_threshold": 0.75,
            "slack_webhook_url": None,
            "email_address": current_user.email,
            "enabled": True,
        }

    return {
        "score_threshold": round(config.min_match_score / 100.0, 2),
        "slack_webhook_url": config.slack_webhook_url,
        "email_address": current_user.email,
        "enabled": config.is_active,
    }


@alerts_router.put("/config", status_code=200)
async def update_alert_config(
    body: AlertConfigBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upsert alert configuration for the current user."""
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()

    threshold_int = int(body.score_threshold * 100)

    if config:
        config.min_match_score = threshold_int
        config.slack_webhook_url = body.slack_webhook_url
        config.notify_slack = bool(body.slack_webhook_url)
        config.is_active = body.enabled
    else:
        config = AlertConfig(
            user_id=current_user.id,
            min_match_score=threshold_int,
            slack_webhook_url=body.slack_webhook_url,
            notify_slack=bool(body.slack_webhook_url),
            notify_email=True,
            is_active=body.enabled,
        )
        db.add(config)

    await db.flush()
    return {"status": "saved"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize_notification(n: Notification) -> dict:
    return {
        "id": str(n.id),
        "job_id": str(n.job_id) if n.job_id else None,
        "job_title": n.job_title,
        "score": n.score,
        "message": n.message,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }
