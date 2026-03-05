"""LiveabilityScore ORM model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class LiveabilityScore(Base):
    __tablename__ = "liveability_scores"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    overall_score = Column(Float, nullable=False)
    climate_score = Column(Float, nullable=False)
    affordability_score = Column(Float, nullable=False)
    safety_score = Column(Float, nullable=False)
    environment_score = Column(Float, nullable=False)
    weights_used = Column(JSON, nullable=True)

    city = relationship("City", back_populates="liveability_scores")
