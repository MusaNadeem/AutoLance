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
            <p style="margin: 8px 0 0; opacity: 0.9;">FreelanceRadar found a great match for you</p>
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
              View on FreelanceRadar →
            </a>
            <a href="{job_url}" style="display: block; background: #1A1A2E; color: #A78BFA; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-size: 14px;">
              View on Upwork
            </a>
          </div>
          <div style="padding: 16px 32px; border-top: 1px solid #2D2D4E; font-size: 12px; color: #6B7280; text-align: center;">
            FreelanceRadar · Unsubscribe
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


notification_service = NotificationService()
