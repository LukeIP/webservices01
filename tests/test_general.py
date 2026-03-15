"""Tests for health check, CORS, error handling, and general API behaviour.

Covers:
- NFR-04: Global exception handler, structured error responses
- NFR-01: Application structure 
- FR-03: JSON responses
- Health check endpoint
- OpenAPI docs availability
"""

import pytest


class TestHealthCheck:
    """GET / — Health check endpoint."""

    def test_health_check(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "city-liveability-api"
        assert "version" in data

    def test_health_returns_json(self, client):
        """FR-03: All responses are JSON."""
        resp = client.get("/")
        assert resp.headers["content-type"].startswith("application/json")


class TestOpenAPIDocs:
    """Swagger/ReDoc documentation availability."""

    def test_swagger_docs_available(self, client):
        """NFR-05: Auto-generated OpenAPI docs at /docs."""
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_redoc_available(self, client):
        """NFR-05: ReDoc available at /redoc."""
        resp = client.get("/redoc")
        assert resp.status_code == 200

    def test_openapi_json_available(self, client):
        """NFR-05: OpenAPI schema JSON endpoint."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert any(p.startswith("/api/v1/cities") for p in schema["paths"])


class TestErrorHandling:
    """Global error handling and edge cases."""

    def test_404_on_unknown_route(self, client):
        """NFR-04: Unknown routes return 404."""
        resp = client.get("/api/v1/nonexistent")
        assert resp.status_code == 404

    def test_method_not_allowed(self, client):
        """NFR-04: Wrong HTTP method returns 405."""
        resp = client.patch("/api/v1/cities/")
        assert resp.status_code == 405

    def test_invalid_json_body(self, client, auth_headers):
        """NFR-04: Malformed JSON returns 422."""
        resp = client.post(
            "/api/v1/cities/",
            content="not valid json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_wrong_content_type(self, client, auth_headers):
        """NFR-04: Wrong content type returns 422."""
        resp = client.post(
            "/api/v1/cities/",
            content="name=Leeds",
            headers={**auth_headers, "Content-Type": "text/plain"},
        )
        assert resp.status_code == 422


class TestCORS:
    """CORS middleware is configured."""

    def test_cors_headers_present(self, client):
        """NFR-10: CORS is configured."""
        resp = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        # FastAPI CORS middleware should respond
        assert resp.status_code in (200, 204)


class TestJSONResponses:
    """All API responses are JSON with correct content types."""

    def test_list_returns_json(self, client):
        resp = client.get("/api/v1/cities/")
        assert "application/json" in resp.headers["content-type"]

    def test_create_returns_json(self, client, auth_headers):
        resp = client.post("/api/v1/cities/", json={
            "name": "Test", "region": "Test", "latitude": 50, "longitude": -1,
        }, headers=auth_headers)
        assert "application/json" in resp.headers["content-type"]

    def test_error_returns_json(self, client):
        resp = client.get("/api/v1/cities/99999")
        assert "application/json" in resp.headers["content-type"]
