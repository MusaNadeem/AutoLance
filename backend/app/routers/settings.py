"""User Settings Router — profile update, password change, account deletion."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_user, hash_password, verify_password

router = APIRouter(prefix="/settings", tags=["Settings"])


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("/")
async def get_settings(
    current_user: User = Depends(get_current_user),
):
    """Return current user settings."""
    return {
        "id":                str(current_user.id),
        "email":             current_user.email,
        "full_name":         current_user.full_name,
        "avatar_url":        current_user.avatar_url,
        "subscription_tier": current_user.subscription_tier or "free",
        "is_verified":       current_user.is_verified,
    }


@router.put("/profile")
async def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update display name and avatar URL."""
    if body.full_name is not None:
        current_user.full_name = body.full_name.strip()
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url.strip() or None

    return {
        "full_name":  current_user.full_name,
        "avatar_url": current_user.avatar_url,
    }


@router.put("/password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password after verifying the current one."""
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    current_user.password_hash = hash_password(body.new_password)
    return {"detail": "Password updated"}


@router.delete("/account", status_code=204)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete: deactivate account and anonymise email."""
    import uuid as _uuid
    current_user.is_active = False
    current_user.email = f"deleted_{_uuid.uuid4().hex}@deleted.invalid"
    current_user.full_name = "Deleted User"
    current_user.password_hash = ""
