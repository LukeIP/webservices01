"""Liveability and analytics schemas."""

from pydantic import BaseModel
from datetime import datetime


class LiveabilityResponse(BaseModel):
    city_id: int
    city_name: str
    overall_score: float
    climate_score: float
    affordability_score: float
    safety_score: float
    environment_score: float
    weights_used: dict | None = None
    computed_at: datetime | None = None


class CityComparison(BaseModel):
    cities: list[LiveabilityResponse]


class TrendPoint(BaseModel):
    date: str
    value: float


class TrendResponse(BaseModel):
    city_id: int
    metric: str
    period: str
    data_points: list[TrendPoint]


class AnomalyPoint(BaseModel):
    date: str
    metric: str
    value: float
    z_score: float
    is_anomaly: bool


class AnomalyResponse(BaseModel):
    city_id: int
    anomalies: list[AnomalyPoint]
    threshold: float
