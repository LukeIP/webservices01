"""Metrics router: CRUD for climate and socioeconomic data."""

from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.rent_submission import RentSubmission
from app.schemas.metric import (
    ClimateMetricCreate,
    ClimateMetricResponse,
    SocioeconomicMetricCreate,
    SocioeconomicMetricResponse,
    RentSubmissionCreate,
    RentSubmissionResponse,
    RentMedianResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.metric_service import MetricService
from app.exceptions import NotFoundException

router = APIRouter(prefix="/api/v1", tags=["Metrics"])


# ---- Climate Metrics ----


@router.post(
    "/cities/{city_id}/climate-metrics",
    response_model=ClimateMetricResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_climate_metric(
    city_id: int,
    data: ClimateMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MetricService(db)
    return service.create_climate_metric(city_id, data)


@router.get(
    "/cities/{city_id}/climate-metrics",
    response_model=PaginatedResponse[ClimateMetricResponse],
)
def list_climate_metrics(
    city_id: int,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    service = MetricService(db)
    items, total = service.list_climate_metrics(
        city_id, start_date=start_date, end_date=end_date, offset=offset, limit=limit
    )
    return PaginatedResponse(items=items, total=total, offset=offset, limit=limit)


@router.get("/climate-metrics/{metric_id}", response_model=ClimateMetricResponse)
def get_climate_metric(metric_id: int, db: Session = Depends(get_db)):
    service = MetricService(db)
    return service.get_climate_metric(metric_id)


@router.delete("/climate-metrics/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_climate_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = MetricService(db)
    service.delete_climate_metric(metric_id)


# ---- Socioeconomic Metrics ----


@router.post(
    "/cities/{city_id}/socioeconomic-metrics",
    response_model=SocioeconomicMetricResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_socioeconomic_metric(
    city_id: int,
    data: SocioeconomicMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MetricService(db)
    return service.create_socioeconomic_metric(city_id, data)


@router.get(
    "/cities/{city_id}/socioeconomic-metrics",
    response_model=PaginatedResponse[SocioeconomicMetricResponse],
)
def list_socioeconomic_metrics(
    city_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    service = MetricService(db)
    items, total = service.list_socioeconomic_metrics(city_id, offset=offset, limit=limit)
    return PaginatedResponse(items=items, total=total, offset=offset, limit=limit)


@router.get("/socioeconomic-metrics/{metric_id}", response_model=SocioeconomicMetricResponse)
def get_socioeconomic_metric(metric_id: int, db: Session = Depends(get_db)):
    service = MetricService(db)
    return service.get_socioeconomic_metric(metric_id)


@router.delete("/socioeconomic-metrics/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_socioeconomic_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = MetricService(db)
    service.delete_socioeconomic_metric(metric_id)


# ---- Rent Submissions (crowdsourced) ----


@router.post(
    "/cities/{city_id}/rent-submissions",
    response_model=RentSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit your monthly rent for a city",
)
def submit_rent(
    city_id: int,
    data: RentSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit or update your rent for the current year. One submission per user per city per year."""
    from app.models.city import City
    if not db.query(City).filter(City.id == city_id).first():
        raise NotFoundException("City", city_id)

    year = datetime.now(timezone.utc).year
    existing = (
        db.query(RentSubmission)
        .filter(
            RentSubmission.city_id == city_id,
            RentSubmission.user_id == current_user.id,
            RentSubmission.year == year,
        )
        .first()
    )
    if existing:
        existing.rent_amount_gbp = data.rent_amount_gbp
        existing.created_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    sub = RentSubmission(
        city_id=city_id,
        user_id=current_user.id,
        rent_amount_gbp=data.rent_amount_gbp,
        year=year,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.get(
    "/cities/{city_id}/rent-submissions",
    response_model=PaginatedResponse[RentSubmissionResponse],
    summary="List rent submissions for a city",
)
def list_rent_submissions(
    city_id: int,
    year: int = Query(None, description="Filter by year (defaults to current year)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    from app.models.city import City
    if not db.query(City).filter(City.id == city_id).first():
        raise NotFoundException("City", city_id)

    filter_year = year or datetime.now(timezone.utc).year
    q = db.query(RentSubmission).filter(
        RentSubmission.city_id == city_id,
        RentSubmission.year == filter_year,
    )
    total = q.count()
    items = q.order_by(RentSubmission.created_at.desc()).offset(offset).limit(limit).all()
    return PaginatedResponse(items=items, total=total, offset=offset, limit=limit)


@router.get(
    "/cities/{city_id}/rent-median",
    response_model=RentMedianResponse,
    summary="Get crowdsourced median rent for a city",
)
def get_rent_median(
    city_id: int,
    year: int = Query(None, description="Year (defaults to current year)"),
    db: Session = Depends(get_db),
):
    from app.models.city import City
    if not db.query(City).filter(City.id == city_id).first():
        raise NotFoundException("City", city_id)

    filter_year = year or datetime.now(timezone.utc).year
    rents = [
        r[0] for r in db.query(RentSubmission.rent_amount_gbp)
        .filter(RentSubmission.city_id == city_id, RentSubmission.year == filter_year)
        .all()
    ]
    median = None
    if rents:
        s = sorted(rents)
        n = len(s)
        median = s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2

    return RentMedianResponse(
        city_id=city_id,
        year=filter_year,
        median_rent_gbp=round(median, 2) if median is not None else None,
        submission_count=len(rents),
    )
