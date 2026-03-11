"""Query router: natural language queries and narrative generation."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.query import NarrativeResponse
from app.services.narrative_service import NarrativeService
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1", tags=["City Narrative"])


@router.get("/cities/{city_id}/narrative", response_model=NarrativeResponse)
def get_city_narrative(
    city_id: int,
    db: Session = Depends(get_db),
):
    analytics = AnalyticsService(db)
    scores = analytics.compute_liveability_for_city(city_id)

    narrative_service = NarrativeService(db)
    narrative = narrative_service.generate_narrative(city_id, scores["city_name"], scores)


    return NarrativeResponse(
        city_id=city_id,
        city_name=scores["city_name"],
        narrative=narrative,
    )
