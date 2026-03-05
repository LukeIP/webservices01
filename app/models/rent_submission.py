"""RentSubmission ORM model — crowdsourced rent data submitted by users."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class RentSubmission(Base):
    __tablename__ = "rent_submissions"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rent_amount_gbp = Column(Float, nullable=False)
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    city = relationship("City", back_populates="rent_submissions")
    user = relationship("User", back_populates="rent_submissions")

    # One submission per user per city per year (upsert on conflict)
    __table_args__ = (
        UniqueConstraint("city_id", "user_id", "year", name="uq_rent_user_city_year"),
    )
