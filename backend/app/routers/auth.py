"""Auth Router — Register, Login, Refresh, Me"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.middleware.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account and send a verification email."""
    from datetime import datetime, timezone, timedelta
    import secrets

    existing = await db.execute(select(User).where(User.email == body.email))
    user = existing.scalar_one_or_none()

    if user:
        if user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered")
        # Overwrite unverified user details
        user.password_hash = hash_password(body.password)
        user.full_name = body.full_name
    else:
        user = User(
            email=body.email,
            password_hash=hash_password(body.password),
            full_name=body.full_name,
            is_verified=False,
        )
        db.add(user)

    # Generate 6-digit OTP
    otp = str(secrets.randbelow(900000) + 100000)
    expiry = datetime.now(timezone.utc) + timedelta(minutes=10)

    user.verification_token = otp
    user.reset_token_expires = expiry
    await db.flush()

    # Best-effort verification email
    try:
        from app.services.notification import notification_service
        await notification_service.send_transactional_email(
            to_email=user.email,
            to_name=user.full_name or "there",
            subject="Your AutoLance Verification Code",
            html_body=(
                f"<p>Welcome to AutoLance, {user.full_name or 'there'}!</p>"
                f"<p>Your email verification code is:</p>"
                f"<h2 style='letter-spacing: 5px;'>{otp}</h2>"
                f"<p>This code will expire in 10 minutes.</p>"
            ),
        )
    except Exception:
        pass

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.email),
        refresh_token=create_refresh_token(str(user.id)),
    )


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str

class ResendOtpRequest(BaseModel):
    email: EmailStr

@router.post("/resend-otp")
async def resend_otp(body: ResendOtpRequest, db: AsyncSession = Depends(get_db)):
    """Resend the email verification OTP."""
    from datetime import datetime, timezone, timedelta
    import secrets

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or user.is_verified:
        # Don't reveal if email exists or is already verified to prevent enumeration
        return {"detail": "If your account exists and is unverified, a new code has been sent."}

    # Generate new 6-digit OTP
    otp = str(secrets.randbelow(900000) + 100000)
    expiry = datetime.now(timezone.utc) + timedelta(minutes=10)

    user.verification_token = otp
    user.reset_token_expires = expiry
    await db.flush()

    # Best-effort email send
    try:
        from app.services.notification import notification_service
        await notification_service.send_transactional_email(
            to_email=user.email,
            to_name=user.full_name or "there",
            subject="Your New AutoLance Verification Code",
            html_body=(
                f"<p>Hi {user.full_name or 'there'},</p>"
                f"<p>Here is your new email verification code:</p>"
                f"<h2 style='letter-spacing: 5px;'>{otp}</h2>"
                f"<p>This code will expire in 10 minutes.</p>"
            ),
        )
    except Exception:
        pass

    return {"detail": "If your account exists and is unverified, a new code has been sent."}

@router.post("/verify-otp")
async def verify_otp(body: VerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    """Verify email address via 6-digit OTP."""
    from datetime import datetime, timezone
    
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or OTP")
        
    if user.is_verified:
        return {"detail": "Email already verified"}

    if user.verification_token != body.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    if not user.reset_token_expires or user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP has expired")

    user.is_verified = True
    user.verification_token = None
    user.reset_token_expires = None
    return {"detail": "Email verified successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email address to log in.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.email),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Issue new access token using refresh token."""
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    from uuid import UUID
    result = await db.execute(select(User).where(User.id == UUID(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.email),
        refresh_token=create_refresh_token(str(user.id)),
    )


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password", status_code=200)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a password-reset token and email it to the user.
    Always returns 200 so we don't reveal whether the email exists.
    """
    import uuid as _uuid
    from datetime import datetime, timezone, timedelta

    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()

    if user:
        token = _uuid.uuid4().hex
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)

        # Best-effort email send — never block the response
        try:
            from app.services.notification import notification_service
            from app.config import settings as app_settings
            frontend_url = app_settings.ALLOWED_ORIGINS.split(',')[0].strip()
            await notification_service.send_transactional_email(
                to_email=user.email,
                to_name=user.full_name or "there",
                subject="Reset your AutoLance password",
                html_body=(
                    f"<p>Hi {user.full_name or 'there'},</p>"
                    f"<p>Click the link below to reset your password. It expires in 1 hour.</p>"
                    f"<p><a href='{frontend_url}/reset-password?token={token}'>Reset Password</a></p>"
                    f"<p>If you didn't request this, ignore this email.</p>"
                ),
            )
        except Exception:
            pass

    return {"detail": "If that email exists we've sent a reset link"}


@router.post("/reset-password", status_code=200)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Validate reset token and set a new password."""
    from datetime import datetime, timezone

    result = await db.execute(select(User).where(User.reset_token == body.token))
    user = result.scalar_one_or_none()

    if not user or not user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user.password_hash = hash_password(body.new_password)
    user.reset_token = None
    user.reset_token_expires = None

    return {"detail": "Password updated successfully"}


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "role": current_user.role,
        "subscription_tier": current_user.subscription_tier,
        "created_at": current_user.created_at,
    }
