"""Tests for authentication endpoints: registration, login, and current user.

Covers:
- FR-04: JWT authentication
- FR-05: Role-based access control
- NFR-04: Structured error responses
- NFR-10: Security (password hashing, JWT)
"""

import pytest


class TestRegister:
    """POST /api/v1/auth/register"""

    def test_register_success(self, client):
        """FR-04: Successful user registration returns 201 with user data."""
        resp = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert data["role"] == "user"
        assert "id" in data
        # Password must NOT be in the response
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, client, test_user):
        """NFR-04: Duplicate username returns 409 with structured error."""
        resp = client.post("/api/v1/auth/register", json={
            "username": "testuser",  # same as test_user
            "email": "different@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 409
        data = resp.json()
        assert data["code"] == "DUPLICATE"
        assert "username" in data["detail"]

    def test_register_duplicate_email(self, client, test_user):
        """NFR-04: Duplicate email returns 409."""
        resp = client.post("/api/v1/auth/register", json={
            "username": "different",
            "email": "test@example.com",  # same as test_user
            "password": "securepass123",
        })
        assert resp.status_code == 409

    def test_register_short_username(self, client):
        """FR-17: Username validation — too short."""
        resp = client.post("/api/v1/auth/register", json={
            "username": "ab",
            "email": "short@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 422  # Pydantic validation

    def test_register_short_password(self, client):
        """FR-17: Password validation — too short."""
        resp = client.post("/api/v1/auth/register", json={
            "username": "validuser",
            "email": "valid@example.com",
            "password": "short",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        """FR-17: Email validation — invalid format."""
        resp = client.post("/api/v1/auth/register", json={
            "username": "validuser",
            "email": "not-an-email",
            "password": "securepass123",
        })
        assert resp.status_code == 422

    def test_register_missing_fields(self, client):
        """FR-17: Missing required fields returns 422."""
        resp = client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 422


class TestLogin:
    """POST /api/v1/auth/login"""

    def test_login_success(self, client, test_user):
        """FR-04: Successful login returns JWT token."""
        resp = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20  # JWT is a long string

    def test_login_wrong_password(self, client, test_user):
        """NFR-04: Invalid credentials return structured error."""
        resp = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        """NFR-04: Login with nonexistent user returns 401."""
        resp = client.post("/api/v1/auth/login", json={
            "username": "nobody",
            "password": "anything",
        })
        assert resp.status_code == 401


class TestGetMe:
    """GET /api/v1/auth/me"""

    def test_get_me_authenticated(self, client, test_user, auth_headers):
        """FR-04: Authenticated user can view their profile."""
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "hashed_password" not in data

    def test_get_me_no_token(self, client):
        """FR-04: Request without token returns 401/403."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)

    def test_get_me_invalid_token(self, client):
        """FR-04: Invalid JWT returns 401."""
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalid.token.here"
        })
        assert resp.status_code == 401

    def test_get_me_expired_token(self, client, test_user):
        """FR-04: Expired token returns 401."""
        from app.utils.security import create_access_token
        from datetime import timedelta
        expired = create_access_token(
            data={"sub": str(test_user.id)},
            expires_delta=timedelta(seconds=-1),
        )
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {expired}"
        })
        assert resp.status_code == 401


class TestTokenRefresh:
    """POST /api/v1/auth/refresh"""

    def test_refresh_returns_new_token(self, client, auth_headers):
        """Authenticated user receives a fresh JWT token."""
        resp = client.post("/api/v1/auth/refresh", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Token should be a valid JWT string
        assert data["access_token"].count(".") == 2

    def test_refresh_new_token_works(self, client, auth_headers):
        """The refreshed token can be used to access protected endpoints."""
        # Get a new token
        resp = client.post("/api/v1/auth/refresh", headers=auth_headers)
        new_token = resp.json()["access_token"]
        # Use it
        resp2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_token}"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["username"] == "testuser"

    def test_refresh_requires_auth(self, client):
        """Unauthenticated users cannot refresh tokens."""
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code in (401, 403)

    def test_refresh_rejects_expired_token(self, client, test_user):
        """Expired token cannot be used to refresh."""
        from app.utils.security import create_access_token
        from datetime import timedelta
        expired = create_access_token(
            data={"sub": str(test_user.id)},
            expires_delta=timedelta(seconds=-1),
        )
        resp = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert resp.status_code == 401
