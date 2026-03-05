"""City ORM model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, default="United Kingdom")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    population = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    climate_metrics = relationship("ClimateMetric", back_populates="city", cascade="all, delete-orphan")
    socioeconomic_metrics = relationship("SocioeconomicMetric", back_populates="city", cascade="all, delete-orphan")
    liveability_scores = relationship("LiveabilityScore", back_populates="city", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="city", cascade="all, delete-orphan")
    rent_submissions = relationship("RentSubmission", back_populates="city", cascade="all, delete-orphan")
