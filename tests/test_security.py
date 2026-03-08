"""Tests for security-related behaviour.

Covers:
- NFR-10: Password hashing, JWT, RBAC
- FR-04: JWT authentication
- FR-05: Role-based access control
- Edge cases for authentication
"""

import pytest
from app.utils.security import hash_password, verify_password, create_access_token
from datetime import timedelta


class TestPasswordHashing:
    """NFR-10: bcrypt password hashing."""

    def test_hash_is_different_from_plain(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"

    def test_verify_correct_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        """bcrypt generates different salts each time."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2
        # But both still verify
        assert verify_password("same", h1)
        assert verify_password("same", h2)


class TestJWTTokens:
    """NFR-10: JWT token creation and properties."""

    def test_create_token(self):
        token = create_access_token(data={"sub": "1"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_token_contains_subject(self):
        from jose import jwt
        from app.config import get_settings
        settings = get_settings()
        token = create_access_token(data={"sub": "42"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "42"
        assert "exp" in payload

    def test_custom_expiry(self):
        from jose import jwt
        from app.config import get_settings
        settings = get_settings()
        token = create_access_token(
            data={"sub": "1"},
            expires_delta=timedelta(hours=2),
        )
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload


class TestRBACEndpoints:
    """FR-05: Role-based access control integration tests."""

    def test_regular_user_cannot_delete_city(self, client, auth_headers, sample_city):
        """Only admins can delete cities."""
        resp = client.delete(f"/api/v1/cities/{sample_city.id}", headers=auth_headers)
        assert resp.status_code == 403

    def test_admin_can_delete_city(self, client, admin_headers, sample_city):
        resp = client.delete(f"/api/v1/cities/{sample_city.id}", headers=admin_headers)
        assert resp.status_code == 204

    def test_both_roles_can_create_city(self, client, auth_headers, admin_headers):
        """Both regular users and admins can create cities."""
        resp1 = client.post("/api/v1/cities/", json={
            "name": "City1", "region": "R1", "latitude": 50, "longitude": -1,
        }, headers=auth_headers)
        resp2 = client.post("/api/v1/cities/", json={
            "name": "City2", "region": "R2", "latitude": 51, "longitude": -2,
        }, headers=admin_headers)
        assert resp1.status_code == 201
        assert resp2.status_code == 201

    def test_unauthenticated_cannot_create(self, client):
        resp = client.post("/api/v1/cities/", json={
            "name": "City", "region": "R", "latitude": 50, "longitude": -1,
        })
        assert resp.status_code in (401, 403)


class TestEndToEndFlow:
    """Full end-to-end user journey: register → login → CRUD."""

    def test_full_user_journey(self, client):
        """Simulates a complete user workflow."""
        # 1. Register
        reg = client.post("/api/v1/auth/register", json={
            "username": "journey_user",
            "email": "journey@example.com",
            "password": "securepass123",
        })
        assert reg.status_code == 201

        # 2. Login
        login = client.post("/api/v1/auth/login", json={
            "username": "journey_user",
            "password": "securepass123",
        })
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Check profile
        me = client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["username"] == "journey_user"

        # 4. Create a city
        city = client.post("/api/v1/cities/", json={
            "name": "Liverpool",
            "region": "North West",
            "latitude": 53.4084,
            "longitude": -2.9916,
            "population": 500000,
        }, headers=headers)
        assert city.status_code == 201
        city_id = city.json()["id"]

        # 5. Read it back
        get_city = client.get(f"/api/v1/cities/{city_id}")
        assert get_city.status_code == 200
        assert get_city.json()["name"] == "Liverpool"

        # 6. Update it
        update = client.put(f"/api/v1/cities/{city_id}", json={
            "population": 510000,
        }, headers=headers)
        assert update.status_code == 200
        assert update.json()["population"] == 510000

        # 7. Create an observation
        obs = client.post(f"/api/v1/cities/{city_id}/observations", json={
            "category": "safety",
            "value": 75.0,
            "note": "Feels safe in the centre",
        }, headers=headers)
        assert obs.status_code == 201
        obs_id = obs.json()["id"]

        # 8. List observations
        obs_list = client.get(f"/api/v1/cities/{city_id}/observations")
        assert obs_list.status_code == 200
        assert obs_list.json()["total"] == 1

        # 9. Update observation
        obs_upd = client.put(f"/api/v1/observations/{obs_id}", json={
            "value": 80.0,
        }, headers=headers)
        assert obs_upd.status_code == 200

        # 10. Get liveability score
        live = client.get(f"/api/v1/cities/{city_id}/liveability")
        assert live.status_code == 200
        assert "overall_score" in live.json()

        # 11. Get narrative (fallback without API key)
        narrative = client.get(f"/api/v1/cities/{city_id}/narrative")
        assert narrative.status_code == 200
        assert "narrative" in narrative.json()

        # 12. Delete observation
        del_obs = client.delete(f"/api/v1/observations/{obs_id}", headers=headers)
        assert del_obs.status_code == 204

        # 13. List cities
        cities_list = client.get("/api/v1/cities/")
        assert cities_list.status_code == 200
        assert cities_list.json()["total"] >= 1
