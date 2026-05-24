"""
Job Ingestion Pipeline
Processes raw scraped jobs: normalize → deduplicate → upsert → trigger scoring.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.job import Job
from app.models.client import Client
from app.models import ScrapingRun
from app.services.client_analyzer import client_analyzer_service

logger = structlog.get_logger()

PROPOSAL_TIERS = {
    (0, 5): "low",
    (6, 15): "medium",
    (16, 30): "high",
    (31, float("inf")): "very_high",
}


class JobIngestionPipeline:
    """Processes and stores scraped job data."""

    async def ingest_batch(
        self,
        db: AsyncSession,
        raw_jobs: list[dict],
        run_id: Optional[str] = None,
    ) -> dict:
        """Process a batch of raw scraped jobs."""
        stats = {"total": len(raw_jobs), "new": 0, "updated": 0, "deduplicated": 0}

        for raw in raw_jobs:
            try:
                result = await self._process_single(db, raw)
                stats[result] += 1
            except Exception as e:
                logger.error("Failed to process job", error=str(e), raw=str(raw)[:200])

        logger.info("Batch ingestion complete", **stats)
        return stats

    async def _process_single(self, db: AsyncSession, raw: dict) -> str:
        """Process one job. Returns 'new', 'updated', or 'deduplicated'."""
        upwork_job_id = raw.get("upwork_job_id") or raw.get("id")
        if not upwork_job_id:
            return "deduplicated"

        # Check existing
        existing = await db.execute(
            select(Job).where(Job.upwork_job_id == str(upwork_job_id))
        )
        job = existing.scalar_one_or_none()

        # Process client first
        client = await client_analyzer_service.analyze_from_raw(db, raw)

        # Normalize job data
        normalized = self._normalize(raw, client.id if client else None)

        if job:
            # Update mutable fields
            job.proposal_count = normalized.get("proposal_count", job.proposal_count)
            job.proposal_tier = normalized.get("proposal_tier", job.proposal_tier)
            job.is_active = normalized.get("is_active", True)
            job.raw_data = raw
            return "updated"
        else:
            job = Job(**normalized, raw_data=raw)
            db.add(job)
            await db.flush()
            return "new"

    def _normalize(self, raw: dict, client_id=None) -> dict:
        """Normalize raw scraped data to internal schema."""
        proposal_count = raw.get("proposal_count", 0) or 0
        proposal_tier = self._get_proposal_tier(proposal_count)

        posted_at = None
        if raw.get("posted_at"):
            try:
                posted_at = datetime.fromisoformat(
                    raw["posted_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                posted_at = None

        return {
            "upwork_job_id": str(raw.get("upwork_job_id") or raw.get("id")),
            "title": (raw.get("title") or "")[:500],
            "description": raw.get("description"),
            "url": raw.get("url"),
            "budget_type": raw.get("budget_type", "fixed"),
            "budget_min": self._to_decimal(raw.get("budget_min")),
            "budget_max": self._to_decimal(raw.get("budget_max")),
            "hourly_rate_min": self._to_decimal(raw.get("hourly_rate_min")),
            "hourly_rate_max": self._to_decimal(raw.get("hourly_rate_max")),
            "required_skills": raw.get("required_skills", []),
            "experience_level": raw.get("experience_level"),
            "project_length": raw.get("project_length"),
            "proposal_count": proposal_count,
            "proposal_tier": proposal_tier,
            "client_id": client_id,
            "is_featured": raw.get("is_featured", False),
            "has_attachments": raw.get("has_attachments", False),
            "posted_at": posted_at,
            "is_active": True,
            "scrape_source": raw.get("_source", "bright_data"),
        }

    def _get_proposal_tier(self, count: int) -> str:
        for (low, high), tier in PROPOSAL_TIERS.items():
            if low <= count <= high:
                return tier
        return "very_high"

    def _to_decimal(self, value) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(str(value).replace(",", "").replace("$", ""))
        except (ValueError, TypeError):
            return None


pipeline = JobIngestionPipeline()
