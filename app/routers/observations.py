"""Observations router: CRUD for user-reported observations."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.observation import ObservationCreate, ObservationUpdate, ObservationResponse
from app.schemas.common import PaginatedResponse
from app.services.observation_service import ObservationService

router = APIRouter(prefix="/api/v1", tags=["Observations"])


@router.post(
    "/cities/{city_id}/observations",
    response_model=ObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_observation(
    city_id: int,
    data: ObservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ObservationService(db)
    return service.create(city_id, current_user, data)


@router.get(
    "/cities/{city_id}/observations",
    response_model=PaginatedResponse[ObservationResponse],
)
def list_observations(
    city_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = ObservationService(db)
    items, total = service.list_for_city(city_id, offset=offset, limit=limit)
    return PaginatedResponse(items=items, total=total, offset=offset, limit=limit)


@router.put("/observations/{obs_id}", response_model=ObservationResponse)
def update_observation(
    obs_id: int,
    data: ObservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ObservationService(db)
    return service.update(obs_id, current_user, data)


@router.delete("/observations/{obs_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_observation(
    obs_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ObservationService(db)
    service.delete(obs_id, current_user)
