"""City service — CRUD operations for cities."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.city import City
from app.schemas.city import CityCreate, CityUpdate
from app.exceptions import NotFoundException, DuplicateException


class CityService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: CityCreate) -> City:
        # Check for duplicate city name in same region
        existing = (
            self.db.query(City)
            .filter(func.lower(City.name) == data.name.lower(), func.lower(City.region) == data.region.lower())
            .first()
        )
        if existing:
            raise DuplicateException("City", "name+region", f"{data.name}, {data.region}")

        city = City(**data.model_dump())
        self.db.add(city)
        self.db.commit()
        self.db.refresh(city)
        return city

    def get_by_id(self, city_id: int) -> City:
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise NotFoundException("City", city_id)
        return city

    def list_cities(
        self,
        offset: int = 0,
        limit: int = 20,
        region: str | None = None,
        sort: str | None = None,
    ) -> tuple[list[City], int]:
        query = self.db.query(City)

        if region:
            query = query.filter(func.lower(City.region) == region.lower())

        total = query.count()

        # Sorting
        if sort:
            desc = sort.startswith("-")
            field_name = sort.lstrip("-")
            col = getattr(City, field_name, None)
            if col is not None:
                query = query.order_by(col.desc() if desc else col.asc())
        else:
            query = query.order_by(City.id.asc())

        cities = query.offset(offset).limit(limit).all()
        return cities, total

    def update(self, city_id: int, data: CityUpdate) -> City:
        city = self.get_by_id(city_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(city, key, value)
        self.db.commit()
        self.db.refresh(city)
        return city

    def delete(self, city_id: int) -> None:
        city = self.get_by_id(city_id)
        self.db.delete(city)
        self.db.commit()
