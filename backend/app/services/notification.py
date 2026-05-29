"""
Notification Service
Dispatches alerts via Slack webhooks, SendGrid email, and push.
"""
import json
from typing import Optional
import httpx
import structlog
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import settings

logger = structlog.get_logger()


class NotificationService:
    """Multi-channel notification dispatcher."""

    async def send_slack(
        self,
        webhook_url: str,
        job_title: str,
        match_score: int,
        job_url: str,
        client_tier: str,
        reasons: list[str],
    ) -> bool:
        """Send a formatted Slack alert."""
        color = "#10B981" if match_score >= 90 else "#6366F1"
        emoji = "🔥" if match_score >= 90 else "⚡" if match_score >= 80 else "✨"

        payload = {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{emoji} High-Match Job Alert!",
                            },
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Job:*\n{job_title[:80]}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Match Score:*\n{match_score}/100",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Client Quality:*\n{client_tier.title()}",
                                },
                            ],
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Why it matches:*\n• " + "\n• ".join(reasons[:3]),
                            },
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "View Job"},
                                    "url": job_url,
                                    "style": "primary",
                                }
                            ],
                        },
                    ],
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=10.0,
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error("Slack notification failed", error=str(e))
            return False

    async def send_email(
        self,
        to_email: str,
        to_name: str,
        job_title: str,
        match_score: int,
        job_url: str,
        dashboard_url: str,
    ) -> bool:
        """Send an email alert via SendGrid."""
        if not settings.SENDGRID_API_KEY:
            logger.warning("SendGrid not configured, skipping email")
            return False

        html_content = f"""
        <div style="font-family: Inter, sans-serif; max-width: 600px; margin: 0 auto; background: #0F0F1A; color: #fff; border-radius: 12px; overflow: hidden;">
          <div style="background: linear-gradient(135deg, #6366F1, #8B5CF6); padding: 32px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">🎯 High-Match Job Alert</h1>
            <p style="margin: 8px 0 0; opacity: 0.9;">AutoLance found a great match for you</p>
          </div>
          <div style="padding: 32px;">
            <div style="background: #1A1A2E; border-radius: 8px; padding: 24px; margin-bottom: 24px;">
              <h2 style="margin: 0 0 12px; font-size: 18px; color: #E2E8F0;">{job_title[:100]}</h2>
              <div style="display: flex; gap: 16px; margin-top: 16px;">
                <div style="background: #6366F1; border-radius: 6px; padding: 8px 16px; text-align: center;">
                  <div style="font-size: 28px; font-weight: bold;">{match_score}</div>
                  <div style="font-size: 12px; opacity: 0.8;">Match Score</div>
                </div>
              </div>
            </div>
            <a href="{dashboard_url}" style="display: block; background: linear-gradient(135deg, #6366F1, #8B5CF6); color: white; text-align: center; padding: 16px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-bottom: 16px;">
              View on AutoLance →
            </a>
            <a href="{job_url}" style="display: block; background: #1A1A2E; color: #A78BFA; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-size: 14px;">
              View on Upwork
            </a>
          </div>
          <div style="padding: 16px 32px; border-top: 1px solid #2D2D4E; font-size: 12px; color: #6B7280; text-align: center;">
            AutoLance · Unsubscribe
          </div>
        </div>
        """

        message = Mail(
            from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=[(to_email, to_name)],
            subject=f"🎯 New {match_score}% Match: {job_title[:60]}",
            html_content=html_content,
        )

        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            sg.send(message)
            return True
        except Exception as e:
            logger.error("Email notification failed", error=str(e))
            return False


    async def send_transactional_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
    ) -> bool:
        """Send a generic transactional email (password reset, verification, etc.) via Gmail API."""
        if not settings.GMAIL_REFRESH_TOKEN:
            logger.warning("Gmail API not configured, skipping transactional email")
            return False
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from email.message import EmailMessage
            import base64

            creds = Credentials(
                token=None,
                refresh_token=settings.GMAIL_REFRESH_TOKEN,
                client_id=settings.GMAIL_CLIENT_ID,
                client_secret=settings.GMAIL_CLIENT_SECRET,
                token_uri="https://oauth2.googleapis.com/token"
            )
            service = build("gmail", "v1", credentials=creds, cache_discovery=False)

            message = EmailMessage()
            message.set_content("Please enable HTML to view this message.")
            message.add_alternative(html_body, subtype="html")
            message["To"] = f"{to_name} <{to_email}>"
            message["From"] = settings.GMAIL_SENDER_EMAIL or "noreply@autolance.io"
            message["Subject"] = subject

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            # Run synchronous API call in thread pool since it's an async function
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: service.users().messages().send(userId="me", body=create_message).execute()
            )
            return True
        except Exception as e:
            logger.error("Transactional email failed", error=str(e))
            return False


notification_service = NotificationService()


# ── Phase 2: AlertService ─────────────────────────────────────────────────────

class AlertService:
    """
    Orchestrates in-app notification creation and channel dispatch.
    Called after every scrape+score cycle from match_tasks.py.
    """

    DEFAULT_THRESHOLD = 0.75   # 0.0–1.0; match_scores stores 0–100 integers

    async def check_and_dispatch(
        self,
        db,
        user_id,
        user_email: str,
        user_name: str,
    ) -> int:
        """
        Query jobs scored in the last 30 min that exceed the user's alert threshold.
        Deduplicates: never inserts the same job_id + user_id twice.
        Returns the number of new notifications created.
        """
        from datetime import datetime, timezone, timedelta
        from sqlalchemy import select, exists
        from app.models import MatchScore, AlertConfig
        from app.models.notification import Notification
        from app.models.job import Job

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)

        # Load alert config (use defaults if none configured)
        config_result = await db.execute(
            select(AlertConfig).where(AlertConfig.user_id == user_id)
        )
        config = config_result.scalar_one_or_none()
        threshold_int = config.min_match_score if config else int(self.DEFAULT_THRESHOLD * 100)
        slack_url = config.slack_webhook_url if (config and config.notify_slack) else None
        notify_email = config.notify_email if config else False

        # Fetch recent high-scoring match scores not yet notified
        result = await db.execute(
            select(MatchScore, Job)
            .join(Job, Job.id == MatchScore.job_id)
            .where(
                MatchScore.user_id == user_id,
                MatchScore.overall_score >= threshold_int,
                MatchScore.scored_at >= cutoff,
                # Dedup: no existing notification for this user+job pair
                ~exists().where(
                    Notification.user_id == user_id,
                    Notification.job_id == MatchScore.job_id,
                ),
            )
        )
        rows = result.all()

        created = 0
        for match, job in rows:
            score_ratio = round(match.overall_score / 100.0, 4)
            message = (
                f"New {match.overall_score}% match: {job.title[:80]}. "
                f"Proposals: {job.proposal_count or 0}."
            )

            notification = Notification(
                user_id=user_id,
                job_id=job.id,
                job_title=job.title or "Untitled",
                score=score_ratio,
                message=message,
            )
            db.add(notification)
            created += 1

            # Fire Slack (if configured)
            if slack_url:
                try:
                    await notification_service.send_slack(
                        webhook_url=slack_url,
                        job_title=job.title or "",
                        match_score=match.overall_score,
                        job_url=job.url or "",
                        client_tier="high",
                        reasons=match.strengths or [],
                    )
                except Exception:
                    pass  # never block notification creation on channel failure

            # Fire email (if configured)
            if notify_email and config:
                try:
                    await notification_service.send_email(
                        to_email=user_email,
                        to_name=user_name,
                        job_title=job.title or "",
                        match_score=match.overall_score,
                        job_url=job.url or "",
                        dashboard_url="https://app.autolance.io/dashboard",
                    )
                except Exception:
                    pass

        if created:
            await db.flush()

        return created


alert_service = AlertService()
