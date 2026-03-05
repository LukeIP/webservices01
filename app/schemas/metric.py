"""Climate and socioeconomic metric schemas."""

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class ClimateMetricCreate(BaseModel):
    date: date
    avg_temp_c: float | None = None
    aqi: float | None = Field(default=None, ge=0)
    humidity_pct: float | None = Field(default=None, ge=0, le=100)
    precipitation_mm: float | None = Field(default=None, ge=0)
    source: str | None = None


class ClimateMetricResponse(BaseModel):
    id: int
    city_id: int
    date: date
    avg_temp_c: float | None
    aqi: float | None
    humidity_pct: float | None
    precipitation_mm: float | None
    source: str | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class SocioeconomicMetricCreate(BaseModel):
    year: int = Field(..., ge=1900, le=2100)
    median_rent_gbp: float | None = Field(default=None, ge=0)
    green_space_pct: float | None = Field(default=None, ge=0, le=100)
    crime_index: float | None = Field(default=None, ge=0)
    avg_commute_min: float | None = Field(default=None, ge=0)
    source: str | None = None


class SocioeconomicMetricResponse(BaseModel):
    id: int
    city_id: int
    year: int
    median_rent_gbp: float | None
    green_space_pct: float | None
    crime_index: float | None
    avg_commute_min: float | None
    source: str | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class RentSubmissionCreate(BaseModel):
    rent_amount_gbp: float = Field(..., gt=0, le=20000, description="Your monthly rent in GBP")


class RentSubmissionResponse(BaseModel):
    id: int
    city_id: int
    user_id: int
    rent_amount_gbp: float
    year: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class RentMedianResponse(BaseModel):
    city_id: int
    year: int
    median_rent_gbp: Optional[float]
    submission_count: int
