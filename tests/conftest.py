"""Shared test fixtures: test database, client, authenticated users."""

import os
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Override settings BEFORE importing app
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["SKIP_SEED"] = "1"  # Prevent background seed from conflicting with test DB

from app.database import Base, get_db
from app.main import create_app
from app.models.user import User
from app.models.city import City
from app.models.climate_metric import ClimateMetric
from app.models.socioeconomic_metric import SocioeconomicMetric
from app.models.observation import Observation
from app.utils.security import hash_password, create_access_token

# Pre-compute hashed passwords once — bcrypt is intentionally slow
_HASHED_PASSWORD = hash_password("password123")
_HASHED_ADMIN_PASSWORD = hash_password("adminpass123")
_HASHED_OTHER_PASSWORD = hash_password("password456")


# ---------- Database ----------

TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create the test engine and schema once for the entire session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(test_engine):
    """Provide a test database session, rolled back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="session")
def _app():
    """Create the FastAPI app once for the entire session."""
    return create_app()


@pytest.fixture
def client(db, _app):
    """FastAPI test client with dependency override for the database."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    _app.dependency_overrides[get_db] = override_get_db
    with TestClient(_app) as c:
        yield c
    _app.dependency_overrides.clear()


# ---------- Users ----------

@pytest.fixture
def test_user(db) -> User:
    """Create and return a regular test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=_HASHED_PASSWORD,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db) -> User:
    """Create and return an admin user."""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=_HASHED_ADMIN_PASSWORD,
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_user(db) -> User:
    """Create a second regular user for ownership tests."""
    user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=_HASHED_OTHER_PASSWORD,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user) -> dict:
    """Return Authorization headers for the test user."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user) -> dict:
    """Return Authorization headers for the admin user."""
    token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_auth_headers(other_user) -> dict:
    """Return Authorization headers for the other user."""
    token = create_access_token(data={"sub": str(other_user.id)})
    return {"Authorization": f"Bearer {token}"}


# ---------- Cities ----------

@pytest.fixture
def sample_city(db) -> City:
    """Create a sample city."""
    city = City(
        name="Leeds",
        region="Yorkshire",
        country="United Kingdom",
        latitude=53.8008,
        longitude=-1.5491,
        population=800000,
    )
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


@pytest.fixture
def sample_cities(db) -> list[City]:
    """Create multiple sample cities."""
    cities_data = [
        {"name": "Leeds", "region": "Yorkshire", "latitude": 53.8008, "longitude": -1.5491, "population": 800000},
        {"name": "Manchester", "region": "North West", "latitude": 53.4808, "longitude": -2.2426, "population": 550000},
        {"name": "London", "region": "Greater London", "latitude": 51.5074, "longitude": -0.1278, "population": 9000000},
        {"name": "Edinburgh", "region": "Scotland", "latitude": 55.9533, "longitude": -3.1883, "population": 540000},
        {"name": "Bristol", "region": "South West", "latitude": 51.4545, "longitude": -2.5879, "population": 467000},
    ]
    cities = []
    for data in cities_data:
        city = City(country="United Kingdom", **data)
        db.add(city)
        cities.append(city)
    db.commit()
    for c in cities:
        db.refresh(c)
    return cities


# ---------- Metrics ----------

@pytest.fixture
def climate_data(db, sample_city) -> list[ClimateMetric]:
    """Create climate metric data for the sample city."""
    from datetime import timedelta
    metrics = []
    today = date.today()
    for i in range(30):
        d = today - timedelta(days=30 - i)  # Last 30 days relative to today
        m = ClimateMetric(
            city_id=sample_city.id,
            date=d,
            avg_temp_c=5.0 + (i * 0.5),  # 5 to 19.5
            aqi=30.0 + (i % 10) * 5,  # 30 to 75
            humidity_pct=60.0 + (i % 5) * 3,
            precipitation_mm=2.0 + (i % 7),
            source="test_data",
        )
        db.add(m)
        metrics.append(m)
    # Add an anomalous reading
    anomaly = ClimateMetric(
        city_id=sample_city.id,
        date=today - timedelta(days=1),
        avg_temp_c=45.0,  # Extreme outlier
        aqi=300.0,  # Extreme outlier
        humidity_pct=99.0,
        precipitation_mm=50.0,  # Extreme
        source="test_data",
    )
    db.add(anomaly)
    metrics.append(anomaly)
    db.commit()
    for m in metrics:
        db.refresh(m)
    return metrics


@pytest.fixture
def socioeconomic_data(db, sample_city) -> list[SocioeconomicMetric]:
    """Create socioeconomic data for the sample city."""
    metrics = []
    for year in [2022, 2023, 2024]:
        m = SocioeconomicMetric(
            city_id=sample_city.id,
            year=year,
            median_rent_gbp=800.0 + (year - 2022) * 50,
            green_space_pct=35.0,
            crime_index=45.0,
            avg_commute_min=25.0,
            source="test_data",
        )
        db.add(m)
        metrics.append(m)
    db.commit()
    for m in metrics:
        db.refresh(m)
    return metrics


# ---------- Observations ----------

@pytest.fixture
def sample_observation(db, sample_city, test_user) -> Observation:
    """Create a sample observation."""
    obs = Observation(
        city_id=sample_city.id,
        user_id=test_user.id,
        category="air_quality",
        value=72.5,
        note="Very clear skies today",
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs
