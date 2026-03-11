"""Analytics router: liveability, comparison, trends, anomalies."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.liveability import LiveabilityResponse, TrendResponse, AnomalyResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1", tags=["Analytics"])


@router.get("/cities/{city_id}/liveability")
def get_liveability(city_id: int, db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.compute_liveability_for_city(city_id)


@router.get("/cities/compare")
def compare_cities(
    ids: str = Query(..., description="Comma-separated city IDs"),
    db: Session = Depends(get_db),
):
    city_ids = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    service = AnalyticsService(db)
    return {"cities": service.compare_cities(city_ids)}


@router.get("/cities/{city_id}/trends")
def get_trends(
    city_id: int,
    metric: str = Query("aqi", description="Metric to trend"),
    period: str = Query("12m", description="Period e.g. 6m, 12m, 24m"),
    db: Session = Depends(get_db),
):
    service = AnalyticsService(db)
    return service.get_trends(city_id, metric=metric, period=period)


@router.get("/cities/{city_id}/anomalies")
def get_anomalies(
    city_id: int,
    threshold: float = Query(2.0, ge=1.0, le=5.0, description="Z-score threshold"),
    db: Session = Depends(get_db),
):
    service = AnalyticsService(db)
    return service.detect_anomalies(city_id, threshold=threshold)
