"""SocioeconomicMetric ORM model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class SocioeconomicMetric(Base):
    __tablename__ = "socioeconomic_metrics"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    median_rent_gbp = Column(Float, nullable=True)
    green_space_pct = Column(Float, nullable=True)
    crime_index = Column(Float, nullable=True)
    avg_commute_min = Column(Float, nullable=True)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    city = relationship("City", back_populates="socioeconomic_metrics")
