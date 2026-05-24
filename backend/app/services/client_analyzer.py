"""
Client Analyzer Service
Analyzes client data and classifies quality using Claude.
"""
from uuid import UUID
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ai.client import claude
from app.ai.prompts.client_analyzer import SYSTEM_PROMPT, build_client_analyzer_prompt
from app.models.client import Client

logger = structlog.get_logger()


class ClientAnalyzerService:
    """Analyzes and classifies Upwork client quality."""

    async def analyze(self, db: AsyncSession, client_id: UUID) -> Client:
        """Run Claude analysis on a client and update their quality scores."""
        result = await db.execute(select(Client).where(Client.id == client_id))
        client = result.scalar_one_or_none()
        if not client:
            raise ValueError(f"Client {client_id} not found")

        client_data = {
            "country": client.country,
            "payment_verified": client.payment_verified,
            "total_spent": float(client.total_spent or 0),
            "hire_rate": float(client.hire_rate or 0),
            "total_hires": client.total_hires,
            "total_reviews": client.total_reviews,
            "average_rating": float(client.average_rating or 0),
            "review_history": client.review_history or [],
        }

        analysis = await claude.complete_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_client_analyzer_prompt(client_data),
            temperature=0.05,
        )

        client.quality_tier = analysis.get("quality_tier")
        client.quality_score = analysis.get("quality_score")
        client.trust_score = analysis.get("trust_score")
        client.red_flags = analysis.get("red_flags", [])
        client.green_flags = analysis.get("green_flags", [])

        from datetime import datetime, timezone
        client.last_analyzed_at = datetime.now(timezone.utc)

        await db.flush()

        logger.info(
            "Client analyzed",
            client_id=str(client_id),
            quality_tier=client.quality_tier,
            quality_score=client.quality_score,
        )

        return client

    async def analyze_from_raw(self, db: AsyncSession, raw_data: dict) -> Client:
        """Create or update a client from raw scraped data, then analyze."""
        upwork_id = raw_data.get("client_id") or raw_data.get("upwork_client_id")
        if not upwork_id:
            return None

        # Check for existing
        result = await db.execute(
            select(Client).where(Client.upwork_client_id == upwork_id)
        )
        client = result.scalar_one_or_none()

        if not client:
            client = Client(upwork_client_id=upwork_id)
            db.add(client)

        # Map raw scraped fields
        client.country = raw_data.get("client_country")
        client.payment_verified = raw_data.get("payment_verified", False)
        client.total_spent = raw_data.get("client_total_spent")
        client.hire_rate = raw_data.get("client_hire_rate")
        client.total_hires = raw_data.get("client_total_hires", 0)
        client.total_reviews = raw_data.get("client_total_reviews", 0)
        client.average_rating = raw_data.get("client_rating")

        await db.flush()

        # Run AI analysis
        return await self.analyze(db, client.id)


client_analyzer_service = ClientAnalyzerService()
