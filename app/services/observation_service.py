"""Observation service — CRUD for user-reported observations."""

from sqlalchemy.orm import Session
from app.models.observation import Observation
from app.models.city import City
from app.models.user import User
from app.schemas.observation import ObservationCreate, ObservationUpdate
from app.exceptions import NotFoundException, ForbiddenException


class ObservationService:
    def __init__(self, db: Session):
        self.db = db

    def _get_city_or_404(self, city_id: int) -> City:
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise NotFoundException("City", city_id)
        return city

    def create(self, city_id: int, user: User, data: ObservationCreate) -> Observation:
        self._get_city_or_404(city_id)
        obs = Observation(
            city_id=city_id,
            user_id=user.id,
            category=data.category,
            value=data.value,
            note=data.note,
        )
        self.db.add(obs)
        self.db.commit()
        self.db.refresh(obs)
        return obs

    def list_for_city(self, city_id: int, offset: int = 0, limit: int = 20) -> tuple[list[Observation], int]:
        self._get_city_or_404(city_id)
        query = self.db.query(Observation).filter(Observation.city_id == city_id)
        total = query.count()
        items = query.order_by(Observation.created_at.desc()).offset(offset).limit(limit).all()
        return items, total

    def get_by_id(self, obs_id: int) -> Observation:
        obs = self.db.query(Observation).filter(Observation.id == obs_id).first()
        if not obs:
            raise NotFoundException("Observation", obs_id)
        return obs

    def update(self, obs_id: int, user: User, data: ObservationUpdate) -> Observation:
        obs = self.get_by_id(obs_id)
        if obs.user_id != user.id and user.role != "admin":
            raise ForbiddenException("You can only edit your own observations")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(obs, key, value)
        self.db.commit()
        self.db.refresh(obs)
        return obs

    def delete(self, obs_id: int, user: User) -> None:
        obs = self.get_by_id(obs_id)
        if obs.user_id != user.id and user.role != "admin":
            raise ForbiddenException("You can only delete your own observations")
        self.db.delete(obs)
        self.db.commit()
