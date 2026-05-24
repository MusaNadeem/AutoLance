"""Job ORM Model"""
import uuid
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    Numeric, String, Text, func
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upwork_job_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    url = Column(Text)
    budget_type = Column(String(50))               # fixed | hourly
    budget_min = Column(Numeric(12, 2))
    budget_max = Column(Numeric(12, 2))
    hourly_rate_min = Column(Numeric(10, 2))
    hourly_rate_max = Column(Numeric(10, 2))
    required_skills = Column(JSONB)
    experience_level = Column(String(50))          # entry | intermediate | expert
    project_length = Column(String(100))
    proposal_count = Column(Integer, default=0)
    proposal_tier = Column(String(50))             # low | medium | high | very_high
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"))
    is_featured = Column(Boolean, default=False)
    has_attachments = Column(Boolean, default=False)
    posted_at = Column(DateTime(timezone=True), index=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, index=True)
    embedding = Column(Vector(1536))
    raw_data = Column(JSONB)
    scrape_source = Column(String(100))

    # Relationships
    client = relationship("Client", back_populates="jobs")
    match_scores = relationship("MatchScore", back_populates="job")
    proposals = relationship("Proposal", back_populates="job")
    cover_letters = relationship("CoverLetter", back_populates="job")
    alert_events = relationship("AlertEvent", back_populates="job")

    def __repr__(self):
        return f"<Job {self.title[:50]}>"
