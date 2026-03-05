"""ClimateMetric ORM model."""

from datetime import datetime, timezone, date
from sqlalchemy import Column, Integer, Float, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ClimateMetric(Base):
    __tablename__ = "climate_metrics"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    avg_temp_c = Column(Float, nullable=True)
    aqi = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    precipitation_mm = Column(Float, nullable=True)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    city = relationship("City", back_populates="climate_metrics")
