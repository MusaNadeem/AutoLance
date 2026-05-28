"""User ORM Model"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base  # noqa: F401 — imported for relationship type resolution


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(String(1024))
    role = Column(String(50), default="freelancer")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    stripe_customer_id = Column(String(255))
    subscription_tier = Column(String(50), default="free")
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    verification_token = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    profile = relationship("FreelancerProfile", back_populates="user", uselist=False)
    cv_documents = relationship("CVDocument", back_populates="user")
    match_scores = relationship("MatchScore", back_populates="user")
    proposals = relationship("Proposal", back_populates="user")
    cover_letters = relationship("CoverLetter", back_populates="user")
    alert_configs = relationship("AlertConfig", back_populates="user")
    alert_events = relationship("AlertEvent", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

    def __repr__(self):
        return f"<User {self.email}>"
