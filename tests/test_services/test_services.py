"""Unit tests for CityService and ObservationService.

Covers:
- FR-01: CRUD operations at the service layer
- NFR-01: Service layer separation
- Exception propagation
"""

import pytest
from app.services.city_service import CityService
from app.services.observation_service import ObservationService
from app.schemas.city import CityCreate, CityUpdate
from app.schemas.observation import ObservationCreate, ObservationUpdate
from app.exceptions import NotFoundException, DuplicateException, ForbiddenException


class TestCityService:
    """Service-layer tests for CityService."""

    def test_create_city(self, db):
        service = CityService(db)
        data = CityCreate(name="Bath", region="South West", latitude=51.38, longitude=-2.36)
        city = service.create(data)
        assert city.id is not None
        assert city.name == "Bath"

    def test_get_city_not_found(self, db):
        service = CityService(db)
        with pytest.raises(NotFoundException):
            service.get_by_id(99999)

    def test_duplicate_city(self, db, sample_city):
        service = CityService(db)
        data = CityCreate(name="Leeds", region="Yorkshire", latitude=53.8, longitude=-1.5)
        with pytest.raises(DuplicateException):
            service.create(data)

    def test_list_cities_empty(self, db):
        service = CityService(db)
        cities, total = service.list_cities()
        assert cities == []
        assert total == 0

    def test_list_cities_with_region_filter(self, db, sample_cities):
        service = CityService(db)
        cities, total = service.list_cities(region="Yorkshire")
        assert total == 1
        assert cities[0].name == "Leeds"

    def test_update_city(self, db, sample_city):
        service = CityService(db)
        data = CityUpdate(name="Leeds Updated")
        updated = service.update(sample_city.id, data)
        assert updated.name == "Leeds Updated"

    def test_delete_city(self, db, sample_city):
        service = CityService(db)
        service.delete(sample_city.id)
        with pytest.raises(NotFoundException):
            service.get_by_id(sample_city.id)


class TestObservationService:
    """Service-layer tests for ObservationService."""

    def test_create_observation(self, db, sample_city, test_user):
        service = ObservationService(db)
        data = ObservationCreate(category="noise", value=60.0, note="Test")
        obs = service.create(sample_city.id, test_user, data)
        assert obs.id is not None
        assert obs.category == "noise"
        assert obs.user_id == test_user.id

    def test_create_observation_city_not_found(self, db, test_user):
        service = ObservationService(db)
        data = ObservationCreate(category="noise", value=50.0)
        with pytest.raises(NotFoundException):
            service.create(99999, test_user, data)

    def test_get_observation_not_found(self, db):
        service = ObservationService(db)
        with pytest.raises(NotFoundException):
            service.get_by_id(99999)

    def test_update_own_observation(self, db, sample_observation, test_user):
        service = ObservationService(db)
        data = ObservationUpdate(value=99.0)
        updated = service.update(sample_observation.id, test_user, data)
        assert updated.value == 99.0

    def test_update_others_observation_forbidden(self, db, sample_observation, other_user):
        service = ObservationService(db)
        data = ObservationUpdate(value=10.0)
        with pytest.raises(ForbiddenException):
            service.update(sample_observation.id, other_user, data)

    def test_admin_can_update_any(self, db, sample_observation, admin_user):
        service = ObservationService(db)
        data = ObservationUpdate(value=95.0)
        updated = service.update(sample_observation.id, admin_user, data)
        assert updated.value == 95.0

    def test_delete_own_observation(self, db, sample_observation, test_user):
        service = ObservationService(db)
        service.delete(sample_observation.id, test_user)
        with pytest.raises(NotFoundException):
            service.get_by_id(sample_observation.id)

    def test_delete_others_observation_forbidden(self, db, sample_observation, other_user):
        service = ObservationService(db)
        with pytest.raises(ForbiddenException):
            service.delete(sample_observation.id, other_user)

    def test_list_for_city(self, db, sample_city, sample_observation):
        service = ObservationService(db)
        items, total = service.list_for_city(sample_city.id)
        assert total == 1
        assert items[0].id == sample_observation.id
