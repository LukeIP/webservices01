"""City request/response schemas."""

from pydantic import BaseModel, Field
from datetime import datetime


class CityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    region: str = Field(..., min_length=1, max_length=100)
    country: str = Field(default="United Kingdom", max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    population: int | None = Field(default=None, ge=0)


class CityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    region: str | None = Field(default=None, min_length=1, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    population: int | None = Field(default=None, ge=0)


class CityResponse(BaseModel):
    id: int
    name: str
    region: str
    country: str
    latitude: float
    longitude: float
    population: int | None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
