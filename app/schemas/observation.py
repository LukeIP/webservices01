"""Observation request/response schemas."""

from pydantic import BaseModel, Field
from datetime import datetime


VALID_CATEGORIES = ["air_quality", "noise", "safety", "cleanliness", "green_space", "transport", "general"]


class ObservationCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=50)
    value: float = Field(..., ge=0, le=100)
    note: str | None = Field(default=None, max_length=500)


class ObservationUpdate(BaseModel):
    category: str | None = Field(default=None, min_length=1, max_length=50)
    value: float | None = Field(default=None, ge=0, le=100)
    note: str | None = Field(default=None, max_length=500)


class ObservationResponse(BaseModel):
    id: int
    city_id: int
    user_id: int
    category: str
    value: float
    note: str | None
    recorded_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
