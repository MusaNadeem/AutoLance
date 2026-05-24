"""
Job Scorer Service
Scores freelancer-job compatibility using Claude with 10-dimension analysis.
Phase 1: client quality + aggregate score are computed deterministically after
Claude returns, and the BidStrategyEngine populates all 5 bid columns.
"""
import json
from typing import Optional
from uuid import UUID
import structlog

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ai.client import claude
from app.ai.prompts.job_scorer import SYSTEM_PROMPT, build_job_scorer_prompt
from app.models import MatchScore
from app.models.profile import FreelancerProfile
from app.models.job import Job
from app.models.client import Client
from app.services.scoring import client_quality_score, aggregate_score
from app.services.bid_strategy import bid_strategy_engine

logger = structlog.get_logger()


class JobScorerService:
    """Scores jobs against freelancer profiles using Claude."""

    async def score_job(
        self,
        db: AsyncSession,
        user_id: UUID,
        job_id: UUID,
        profile_id: UUID,
    ) -> MatchScore:
        """
        Generate an AI match score for a job against a freelancer profile.
        Upserts the match_scores record.
        """
        # Load profile
        profile_result = await db.execute(
            select(FreelancerProfile).where(FreelancerProfile.id == profile_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")

        # Load job
        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Load client
        client = None
        if job.client_id:
            client_result = await db.execute(
                select(Client).where(Client.id == job.client_id)
            )
            client = client_result.scalar_one_or_none()

        # Build scoring context
        profile_context = self._build_profile_context(profile)
        job_context = self._build_job_context(job)
        client_context = self._build_client_context(client)

        # Score with Claude
        score_data = await claude.complete_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_job_scorer_prompt(profile_context, job_context, client_context),
            temperature=0.05,
        )

        # ── Phase 1: deterministic overrides ─────────────────────────────────
        # 1. Compute client_quality_score from raw client metrics (not from Claude)
        hire_rate     = float(client.hire_rate or 0) if client else 0.0
        avg_rating    = float(client.average_rating or 0) if client else 0.0
        total_hires   = int(client.total_hires or 0) if client else 0

        # Estimate jobs_posted from total_hires ÷ hire_rate
        if hire_rate > 0:
            rate_fraction = hire_rate if hire_rate <= 1.0 else hire_rate / 100.0
            jobs_posted = int(total_hires / rate_fraction)
        else:
            jobs_posted = total_hires

        cq_score = client_quality_score(
            hire_rate=hire_rate,
            avg_rating=avg_rating,
            jobs_posted=jobs_posted,
        )

        # 2. Compute aggregate overall score with configured weights
        overall = aggregate_score(
            skill_match=score_data.get("skill_match_score", 0),
            roi=score_data.get("semantic_relevance_score", 0),
            competition=score_data.get("competition_score", 0),
            client_quality=cq_score,
        )

        # 3. Override Claude’s values with the deterministic results
        score_data["client_quality_score"] = int(cq_score * 100)   # match_scores stores 0-100
        score_data["overall_score"]        = int(overall * 100)

        # 4. Persist client_quality_score + bid fields on the Job row
        job.client_quality_score = cq_score

        user_target_rate = float(
            profile.inferred_hourly_rate_min
            or profile.inferred_hourly_rate_max
            or 45.0
        )
        bid = bid_strategy_engine.calculate(
            budget_type=job.budget_type or "fixed",
            budget_min=float(job.budget_min) if job.budget_min else None,
            budget_max=float(job.budget_max) if job.budget_max else None,
            hourly_rate_min=float(job.hourly_rate_min) if job.hourly_rate_min else None,
            hourly_rate_max=float(job.hourly_rate_max) if job.hourly_rate_max else None,
            user_target_rate=user_target_rate,
            proposals_count=job.proposal_count or 0,
            client_quality=cq_score,
        )
        job.bid_strategy  = bid["bid_strategy"]
        job.bid_rationale = bid["bid_rationale"]
        job.bid_confidence = bid["bid_confidence"]
        job.bid_range_min = bid["bid_range_min"]
        job.bid_range_max = bid["bid_range_max"]

        await db.flush()  # persist job fields before creating MatchScore

        # ── Upsert match score ────────────────────────────────────────────────
        existing = await db.execute(
            select(MatchScore).where(
                MatchScore.user_id == user_id,
                MatchScore.job_id == job_id,
            )
        )
        match = existing.scalar_one_or_none()

        if match:
            # Update existing score
            for key, value in score_data.items():
                if hasattr(match, key):
                    setattr(match, key, value)
        else:
            match = MatchScore(
                user_id=user_id,
                job_id=job_id,
                profile_id=profile_id,
                overall_score=score_data.get("overall_score", 0),
                confidence_score=score_data.get("confidence_score", 0),
                skill_match_score=score_data.get("skill_match_score", 0),
                semantic_relevance_score=score_data.get("semantic_relevance_score", 0),
                industry_fit_score=score_data.get("industry_fit_score", 0),
                budget_fit_score=score_data.get("budget_fit_score", 0),
                experience_fit_score=score_data.get("experience_fit_score", 0),
                competition_score=score_data.get("competition_score", 0),
                client_quality_score=score_data.get("client_quality_score", 0),
                communication_fit_score=score_data.get("communication_fit_score", 0),
                win_probability=score_data.get("win_probability", 0),
                strengths=score_data.get("strengths", []),
                weaknesses=score_data.get("weaknesses", []),
                recommended_approach=score_data.get("recommended_approach", ""),
                ai_explanation=score_data.get("ai_explanation", ""),
            )
            db.add(match)

        await db.flush()

        logger.info(
            "Job scored",
            job_id=str(job_id),
            overall_score=match.overall_score,
            win_probability=float(match.win_probability or 0),
        )

        return match

    def _build_profile_context(self, profile: FreelancerProfile) -> dict:
        return {
            "headline": profile.headline,
            "niche": profile.niche,
            "experience_level": profile.experience_level,
            "skills": profile.skills,
            "specializations": profile.specializations,
            "hourly_rate_range": {
                "min": float(profile.inferred_hourly_rate_min or 0),
                "max": float(profile.inferred_hourly_rate_max or 0),
            },
            "communication_tone": profile.communication_tone,
            "preferred_project_types": profile.preferred_project_types,
            "preferred_industries": profile.preferred_industries,
        }

    def _build_job_context(self, job: Job) -> dict:
        return {
            "title": job.title,
            "description": (job.description or "")[:3000],  # Cap to avoid token overflow
            "budget_type": job.budget_type,
            "budget_min": float(job.budget_min or 0),
            "budget_max": float(job.budget_max or 0),
            "hourly_rate_min": float(job.hourly_rate_min or 0),
            "hourly_rate_max": float(job.hourly_rate_max or 0),
            "required_skills": job.required_skills,
            "experience_level": job.experience_level,
            "project_length": job.project_length,
            "proposal_count": job.proposal_count,
            "proposal_tier": job.proposal_tier,
            "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        }

    def _build_client_context(self, client: Optional[Client]) -> dict:
        if not client:
            return {"data": "No client data available"}
        return {
            "country": client.country,
            "payment_verified": client.payment_verified,
            "total_spent": float(client.total_spent or 0),
            "hire_rate": float(client.hire_rate or 0),
            "total_hires": client.total_hires,
            "average_rating": float(client.average_rating or 0),
            "quality_tier": client.quality_tier,
            "quality_score": client.quality_score,
            "trust_score": client.trust_score,
        }


job_scorer_service = JobScorerService()
