"""Cities router: CRUD operations."""

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.city import CityCreate, CityUpdate, CityResponse
from app.schemas.common import PaginatedResponse
from app.services.city_service import CityService
from app.services.weather_service import fetch_and_store_weather

router = APIRouter(prefix="/api/v1/cities", tags=["Cities"])


@router.post(
    "",
    response_model=CityResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new city. Automatically triggers a background fetch of the last 365 days of weather data from the Open-Meteo archive API, stored as climate metrics.",
)
def create_city(
    data: CityCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CityService(db)
    city = service.create(data)
    background_tasks.add_task(fetch_and_store_weather, city.id, city.latitude, city.longitude, db)
    return city


@router.get("", response_model=PaginatedResponse[CityResponse])
def list_cities(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    region: str | None = Query(None),
    sort: str | None = Query(None, description="Sort field, prefix with - for desc"),
    db: Session = Depends(get_db),
):
    service = CityService(db)
    cities, total = service.list_cities(offset=offset, limit=limit, region=region, sort=sort)
    return PaginatedResponse(items=cities, total=total, offset=offset, limit=limit)


@router.get("/{city_id}", response_model=CityResponse)
def get_city(city_id: int, db: Session = Depends(get_db)):
    service = CityService(db)
    return service.get_by_id(city_id)


@router.put(
    "/{city_id}",
    response_model=CityResponse,
    description="Update a city's details. Re-triggers a background fetch of the last 365 days of weather data from the Open-Meteo archive API; duplicate dates are skipped automatically.",
)
def update_city(
    city_id: int,
    data: CityUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CityService(db)
    city = service.update(city_id, data)
    background_tasks.add_task(fetch_and_store_weather, city.id, city.latitude, city.longitude, db)
    return city


@router.delete("/{city_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_city(
    city_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = CityService(db)
    service.delete(city_id)
