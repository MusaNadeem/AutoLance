"""FreelancerProfile ORM Model"""
import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class FreelancerProfile(Base):
    __tablename__ = "freelancer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    headline = Column(String(500))
    summary = Column(Text)
    skills = Column(JSONB)                        # [{name, level, years}]
    experience_level = Column(String(50))         # junior | mid | senior | expert
    niche = Column(String(255))
    specializations = Column(JSONB)
    communication_tone = Column(String(100))      # formal | casual | technical
    inferred_hourly_rate_min = Column(Numeric(10, 2))   # from CV parsing
    inferred_hourly_rate_max = Column(Numeric(10, 2))   # from CV parsing
    target_fixed_min = Column(Numeric(10, 2))           # user-set: min fixed-price project ($)
    target_fixed_max = Column(Numeric(10, 2))           # user-set: max fixed-price project ($)
    preferred_project_types = Column(JSONB)
    preferred_industries = Column(JSONB)
    embedding = Column(Vector(1536))
    profile_version = Column(Integer, default=1)
    last_analyzed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profile")
    match_scores = relationship("MatchScore", back_populates="profile")

    def __repr__(self):
        return f"<FreelancerProfile {self.niche} - {self.experience_level}>"
