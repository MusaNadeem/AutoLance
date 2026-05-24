"""
Cover Letter Generation Service
Generates personalized cover letters with multiple style variants.
"""
from uuid import UUID
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ai.client import claude
from app.ai.prompts.cover_letter import SYSTEM_PROMPT, build_cover_letter_prompt
from app.models import MatchScore, CoverLetter
from app.models.profile import FreelancerProfile
from app.models.job import Job

logger = structlog.get_logger()

VALID_STYLES = ["professional", "casual", "technical", "creative"]


class CoverLetterService:
    """Generates AI-powered cover letters for job applications."""

    async def generate(
        self,
        db: AsyncSession,
        user_id: UUID,
        job_id: UUID,
        style: str = "professional",
        custom_instructions: str = "",
        save: bool = True,
    ) -> CoverLetter:
        """Generate a personalized cover letter for a job."""
        if style not in VALID_STYLES:
            style = "professional"

        # Load job
        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Load match score
        match_result = await db.execute(
            select(MatchScore).where(
                MatchScore.user_id == user_id,
                MatchScore.job_id == job_id,
            )
        )
        match = match_result.scalar_one_or_none()

        # Load profile
        profile_result = await db.execute(
            select(FreelancerProfile).where(FreelancerProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            raise ValueError("No freelancer profile found. Please upload your CV first.")

        profile_context = {
            "headline": profile.headline,
            "niche": profile.niche,
            "experience_level": profile.experience_level,
            "skills": profile.skills,
            "specializations": profile.specializations,
            "communication_tone": profile.communication_tone,
        }
        job_context = {
            "title": job.title,
            "description": (job.description or "")[:2000],
            "required_skills": job.required_skills,
            "budget_type": job.budget_type,
            "project_length": job.project_length,
        }
        match_context = {}
        if match:
            match_context = {
                "strengths": match.strengths,
                "recommended_approach": match.recommended_approach,
                "proposal_hook": None,  # Stored in raw AI output if needed
                "client_quality_score": match.client_quality_score,
            }

        # Generate the letter
        prompt = build_cover_letter_prompt(
            profile=profile_context,
            job=job_context,
            match=match_context,
            style=style,
            custom_instructions=custom_instructions,
        )

        content = await claude.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.7,  # Higher for creative writing
        )

        # Count variants for this job+user
        existing_count_result = await db.execute(
            select(CoverLetter).where(
                CoverLetter.user_id == user_id,
                CoverLetter.job_id == job_id,
            )
        )
        existing = existing_count_result.scalars().all()
        variant_index = len(existing) + 1

        cover_letter = CoverLetter(
            user_id=user_id,
            job_id=job_id,
            match_score_id=match.id if match else None,
            content=content,
            style=style,
            variant_index=variant_index,
            generation_prompt=prompt[:2000],
            token_count=await claude.count_tokens(content),
        )

        if save:
            db.add(cover_letter)
            await db.flush()

        logger.info(
            "Cover letter generated",
            job_id=str(job_id),
            style=style,
            variant=variant_index,
            length=len(content),
        )

        return cover_letter


cover_letter_service = CoverLetterService()
