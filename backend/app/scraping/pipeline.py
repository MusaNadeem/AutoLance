"""
Job Ingestion Pipeline
Processes raw scraped jobs: normalize → deduplicate → upsert → client quality score → bid strategy.
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
from app.services.scoring import client_quality_score
from app.services.bid_strategy import bid_strategy_engine

logger = structlog.get_logger()

# Default market rate used for bid strategy during raw ingestion.
# job_scorer.py overrides this with the specific freelancer's target rate
# when scoring a job against a user profile.
DEFAULT_HOURLY_RATE: float = 50.0

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
            outcome = "updated"
        else:
            job = Job(**normalized, raw_data=raw)
            db.add(job)
            await db.flush()
            outcome = "new"

        # ── Phase 1: compute client quality + bid strategy at ingestion time ──
        # These provide immediate bid data on every job.
        # job_scorer.py will override them with user-specific values when scoring.
        self._apply_phase1_scores(job, client, raw)

        return outcome

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

    def _apply_phase1_scores(self, job: Job, client, raw: dict) -> None:
        """
        Compute client_quality_score and all 5 bid columns at ingestion time.

        Uses DEFAULT_HOURLY_RATE as a market-average fallback target.
        job_scorer.py will override these with the actual freelancer's rate
        when scoring the job against a specific user profile.
        """
        try:
            # ── Client quality ────────────────────────────────────────────────
            hire_rate   = float(client.hire_rate or 0) if client else 0.0
            avg_rating  = float(client.average_rating or 0) if client else 0.0
            total_hires = int(client.total_hires or 0) if client else 0

            # Estimate jobs_posted from total_hires ÷ hire_rate
            if hire_rate > 0:
                rate_fraction = hire_rate if hire_rate <= 1.0 else hire_rate / 100.0
                jobs_posted = int(total_hires / rate_fraction) if rate_fraction > 0 else total_hires
            else:
                jobs_posted = total_hires

            cq = client_quality_score(
                hire_rate=hire_rate,
                avg_rating=avg_rating,
                jobs_posted=jobs_posted,
            )
            job.client_quality_score = cq

            # ── Bid strategy ──────────────────────────────────────────────────
            budget_min      = float(job.budget_min)      if job.budget_min      else None
            budget_max      = float(job.budget_max)      if job.budget_max      else None
            hourly_rate_min = float(job.hourly_rate_min) if job.hourly_rate_min else None
            hourly_rate_max = float(job.hourly_rate_max) if job.hourly_rate_max else None

            bid = bid_strategy_engine.calculate(
                budget_type=job.budget_type or "fixed",
                budget_min=budget_min,
                budget_max=budget_max,
                hourly_rate_min=hourly_rate_min,
                hourly_rate_max=hourly_rate_max,
                user_target_rate=DEFAULT_HOURLY_RATE,
                proposals_count=job.proposal_count or 0,
                client_quality=cq,
            )

            job.bid_strategy   = bid["bid_strategy"]
            job.bid_rationale  = bid["bid_rationale"]
            job.bid_confidence = bid["bid_confidence"]
            job.bid_range_min  = bid["bid_range_min"]
            job.bid_range_max  = bid["bid_range_max"]

        except Exception as e:
            logger.warning(
                "Phase 1 scoring skipped for job",
                job_id=str(job.id) if job.id else "unknown",
                error=str(e),
            )


pipeline = JobIngestionPipeline()
