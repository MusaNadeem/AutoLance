"""CV Upload & Management Router"""
import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.models.user import User
from app.models import CVDocument
from app.models.profile import FreelancerProfile
from app.middleware.auth import get_current_user
from app.services.cv_parser import cv_parser_service
from app.config import settings

router = APIRouter(prefix="/cv", tags=["CV Intelligence"])


async def _parse_cv_background(cv_id: str, user_id: str, file_content: bytes, file_type: str, filename: str):
    """Background task: parse CV with Claude and update profile."""
    from app.database import get_db_context
    async with get_db_context() as db:
        try:
            # Extract text
            text, ocr_used = await cv_parser_service.extract_text(file_content, file_type, filename)

            # Analyze with Claude
            parsed = await cv_parser_service.analyze_with_claude(text)
            parsed["skills"] = cv_parser_service.normalize_skills(parsed.get("skills", []))

            # Update CV document
            await db.execute(
                update(CVDocument)
                .where(CVDocument.id == uuid.UUID(cv_id))
                .values(
                    raw_text=text,
                    parsed_data=parsed,
                    ocr_used=ocr_used,
                    parsing_status="done",
                )
            )

            # Upsert freelancer profile
            profile_result = await db.execute(
                select(FreelancerProfile).where(FreelancerProfile.user_id == uuid.UUID(user_id))
            )
            profile = profile_result.scalar_one_or_none()

            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)

            if profile:
                profile.headline = parsed.get("headline")
                profile.summary = parsed.get("summary")
                profile.skills = parsed.get("skills")
                profile.experience_level = parsed.get("experience_level")
                profile.niche = parsed.get("niche")
                profile.specializations = parsed.get("specializations")
                profile.communication_tone = parsed.get("communication_tone")
                profile.inferred_hourly_rate_min = parsed.get("inferred_hourly_rate_min")
                profile.inferred_hourly_rate_max = parsed.get("inferred_hourly_rate_max")
                profile.preferred_project_types = parsed.get("preferred_project_types")
                profile.preferred_industries = parsed.get("preferred_industries")
                profile.last_analyzed_at = now
                profile.profile_version = (profile.profile_version or 1) + 1
            else:
                profile = FreelancerProfile(
                    user_id=uuid.UUID(user_id),
                    headline=parsed.get("headline"),
                    summary=parsed.get("summary"),
                    skills=parsed.get("skills"),
                    experience_level=parsed.get("experience_level"),
                    niche=parsed.get("niche"),
                    specializations=parsed.get("specializations"),
                    communication_tone=parsed.get("communication_tone"),
                    inferred_hourly_rate_min=parsed.get("inferred_hourly_rate_min"),
                    inferred_hourly_rate_max=parsed.get("inferred_hourly_rate_max"),
                    preferred_project_types=parsed.get("preferred_project_types"),
                    preferred_industries=parsed.get("preferred_industries"),
                    last_analyzed_at=now,
                )
                db.add(profile)

        except Exception as e:
            await db.execute(
                update(CVDocument)
                .where(CVDocument.id == uuid.UUID(cv_id))
                .values(parsing_status="failed", parsing_error=str(e)[:500])
            )


@router.post("/upload", status_code=202)
async def upload_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a CV/resume and trigger AI parsing."""
    # Validate file type
    if file.content_type not in settings.allowed_upload_types_list:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}",
        )

    # Read file content
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Save file locally (in production: upload to Supabase Storage)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    saved_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create CV record
    cv_doc = CVDocument(
        user_id=current_user.id,
        file_name=file.filename,
        file_url=f"/uploads/{saved_filename}",
        file_type=file.content_type,
        file_size_bytes=len(content),
        parsing_status="processing",
    )
    db.add(cv_doc)
    await db.flush()

    # Run parsing in background
    background_tasks.add_task(
        _parse_cv_background,
        str(cv_doc.id),
        str(current_user.id),
        content,
        file.content_type,
        file.filename,
    )

    return {
        "cv_id": str(cv_doc.id),
        "status": "processing",
        "message": "CV uploaded. AI parsing in progress.",
    }


@router.get("/")
async def list_cvs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CVDocument).where(CVDocument.user_id == current_user.id)
        .order_by(CVDocument.created_at.desc())
    )
    cvs = result.scalars().all()
    return [
        {
            "id": str(cv.id),
            "file_name": cv.file_name,
            "file_type": cv.file_type,
            "parsing_status": cv.parsing_status,
            "created_at": cv.created_at,
        }
        for cv in cvs
    ]


@router.get("/{cv_id}")
async def get_cv(
    cv_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CVDocument).where(
            CVDocument.id == uuid.UUID(cv_id),
            CVDocument.user_id == current_user.id,
        )
    )
    cv = result.scalar_one_or_none()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return {
        "id": str(cv.id),
        "file_name": cv.file_name,
        "parsing_status": cv.parsing_status,
        "parsed_data": cv.parsed_data,
        "ocr_used": cv.ocr_used,
        "created_at": cv.created_at,
    }


# ────────────────────────────────────────────────────────────────
# PHASE 3: GET + PUT /cv/profile
# ────────────────────────────────────────────────────────────────

from pydantic import BaseModel as _BaseModel
from typing import Optional as _Optional, List as _List


class SkillItem(_BaseModel):
    name: str
    level: str = "intermediate"
    years: float = 0


class ProfileUpdateRequest(_BaseModel):
    headline:                 _Optional[str]        = None
    summary:                  _Optional[str]        = None
    skills:                   _Optional[_List[SkillItem]] = None
    experience_level:         _Optional[str]        = None   # junior|mid|senior|expert
    niche:                    _Optional[str]        = None
    inferred_hourly_rate_min: _Optional[float]      = None
    inferred_hourly_rate_max: _Optional[float]      = None
    target_fixed_min:         _Optional[float]      = None
    target_fixed_max:         _Optional[float]      = None


def _serialize_profile(p: "FreelancerProfile") -> dict:
    """Serialize profile to JSON — all 9 fields, explicit None when absent."""
    def _f(v):
        return float(v) if v is not None else None

    return {
        "id":                       str(p.id),
        "headline":                 p.headline,
        "summary":                  p.summary,
        "skills":                   p.skills or [],
        "experience_level":         p.experience_level,
        "niche":                    p.niche,
        "inferred_hourly_rate_min": _f(p.inferred_hourly_rate_min),
        "inferred_hourly_rate_max": _f(p.inferred_hourly_rate_max),
        "target_fixed_min":         _f(getattr(p, "target_fixed_min", None)),
        "target_fixed_max":         _f(getattr(p, "target_fixed_max", None)),
        "last_analyzed_at":         p.last_analyzed_at.isoformat() if p.last_analyzed_at else None,
        "profile_version":          p.profile_version,
    }


@router.get("/profile")
async def get_cv_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/v1/cv/profile
    Returns the current user's FreelancerProfile.
    Used by onboarding page and /dashboard/profile edit form.
    Returns 404 if no CV has been uploaded yet.
    """
    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="No profile yet. Upload your CV first.")
    return _serialize_profile(profile)


@router.put("/profile")
async def update_cv_profile(
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    PUT /api/v1/cv/profile
    Upsert the user's FreelancerProfile with manually-confirmed values.
    Called by the onboarding Confirm button and /dashboard/profile Save Changes.
    Only fields present in the body (non-None) are updated.
    """
    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        # First-time PUT before any CV upload — create an empty profile
        profile = FreelancerProfile(user_id=current_user.id)
        db.add(profile)

    # Update only provided fields
    update_map = body.model_dump(exclude_none=True)
    if "skills" in update_map:
        update_map["skills"] = [s.model_dump() for s in body.skills]

    for field, value in update_map.items():
        setattr(profile, field, value)

    # Bump version
    profile.profile_version = (profile.profile_version or 1) + 1

    return _serialize_profile(profile)

