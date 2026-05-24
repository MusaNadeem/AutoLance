"""Client ORM Model"""
import uuid
from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upwork_client_id = Column(String(255), unique=True, index=True)
    country = Column(String(100))
    payment_verified = Column(Boolean, default=False)
    total_spent = Column(Numeric(12, 2))
    hire_rate = Column(Numeric(5, 2))
    total_hires = Column(Integer, default=0)
    total_reviews = Column(Integer, default=0)
    average_rating = Column(Numeric(3, 2))
    review_history = Column(JSONB)
    quality_tier = Column(String(50), index=True)  # high | medium | risky | avoid
    quality_score = Column(Integer)
    red_flags = Column(JSONB)
    green_flags = Column(JSONB)
    trust_score = Column(Integer)
    last_analyzed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    jobs = relationship("Job", back_populates="client")

    def __repr__(self):
        return f"<Client {self.upwork_client_id} - {self.quality_tier}>"
