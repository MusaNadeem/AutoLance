"""MatchScore, CoverLetter, Proposal, Alert, ActivityLog, Notification ORM Models"""
import uuid
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    Numeric, String, Text, func
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.notification import Notification  # noqa: F401 — re-exported


class CVDocument(Base):
    __tablename__ = "cv_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    file_name = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    file_type = Column(String(150))   # MIME types can be long (DOCX = 73 chars)
    file_size_bytes = Column(Integer)
    raw_text = Column(Text)
    parsed_data = Column(JSONB)
    ocr_used = Column(Boolean, default=False)
    parsing_status = Column(String(50), default="pending")
    parsing_error = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="cv_documents")


class MatchScore(Base):
    __tablename__ = "match_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"))
    profile_id = Column(UUID(as_uuid=True), ForeignKey("freelancer_profiles.id"))
    overall_score = Column(Integer, nullable=False, index=True)
    confidence_score = Column(Integer)
    skill_match_score = Column(Integer)
    semantic_relevance_score = Column(Integer)
    industry_fit_score = Column(Integer)
    budget_fit_score = Column(Integer)
    experience_fit_score = Column(Integer)
    competition_score = Column(Integer)
    client_quality_score = Column(Integer)
    communication_fit_score = Column(Integer)
    win_probability = Column(Numeric(5, 2))
    strengths = Column(JSONB)
    weaknesses = Column(JSONB)
    recommended_approach = Column(Text)
    ai_explanation = Column(Text)
    score_version = Column(Integer, default=1)
    scored_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="match_scores")
    job = relationship("Job", back_populates="match_scores")
    profile = relationship("FreelancerProfile", back_populates="match_scores")
    cover_letters = relationship("CoverLetter", back_populates="match_score")
    alert_events = relationship("AlertEvent", back_populates="match_score")


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    match_score_id = Column(UUID(as_uuid=True), ForeignKey("match_scores.id"))
    content = Column(Text, nullable=False)
    style = Column(String(100))
    variant_index = Column(Integer, default=1)
    is_edited = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    generation_prompt = Column(Text)
    token_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="cover_letters")
    job = relationship("Job", back_populates="cover_letters")
    match_score = relationship("MatchScore", back_populates="cover_letters")
    proposals = relationship("Proposal", back_populates="cover_letter")


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    cover_letter_id = Column(UUID(as_uuid=True), ForeignKey("cover_letters.id"))
    status = Column(String(50), default="drafted", index=True)
    job_title_snapshot = Column(String(500))   # snapshot at apply time — survives job deactivation
    bid_amount = Column(Numeric(12, 2))
    bid_type = Column(String(50))
    sent_at = Column(DateTime(timezone=True))
    viewed_at = Column(DateTime(timezone=True))
    replied_at = Column(DateTime(timezone=True))
    interview_at = Column(DateTime(timezone=True))
    outcome_at = Column(DateTime(timezone=True))
    outcome_value = Column(Numeric(12, 2))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="proposals")
    job = relationship("Job", back_populates="proposals")
    cover_letter = relationship("CoverLetter", back_populates="proposals")


class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    min_match_score = Column(Integer, default=85)
    max_proposal_count = Column(Integer, default=10)
    max_hours_since_posted = Column(Integer, default=2)
    min_client_quality_score = Column(Integer, default=60)
    notify_slack = Column(Boolean, default=False)
    notify_email = Column(Boolean, default=True)
    notify_push = Column(Boolean, default=True)
    slack_webhook_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="alert_configs")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    match_score_id = Column(UUID(as_uuid=True), ForeignKey("match_scores.id"))
    trigger_reason = Column(Text)
    channel = Column(String(50))
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))
    is_actioned = Column(Boolean, default=False)

    user = relationship("User", back_populates="alert_events")
    job = relationship("Job", back_populates="alert_events")
    match_score = relationship("MatchScore", back_populates="alert_events")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(255), nullable=False)
    entity_type = Column(String(100))
    entity_id = Column(UUID(as_uuid=True))
    metadata_ = Column("metadata", JSONB)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="activity_logs")


class ScrapingRun(Base):
    __tablename__ = "scraping_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_type = Column(String(100))
    source = Column(String(100))
    status = Column(String(50))
    jobs_scraped = Column(Integer, default=0)
    jobs_new = Column(Integer, default=0)
    jobs_updated = Column(Integer, default=0)
    jobs_deduplicated = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
