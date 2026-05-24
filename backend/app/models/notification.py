"""Notification model — in-app notification for high-match job alerts."""
import uuid
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Notification(Base):
    """
    Lightweight in-app notification record.
    Created by AlertService.check_and_dispatch() after every scrape+score cycle.
    Separate from AlertEvent which tracks channel dispatch details.
    """
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    job_title = Column(String(500), nullable=False)
    score = Column(Float, nullable=False)          # aggregate score 0.0–1.0
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, server_default="false", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="notifications")
