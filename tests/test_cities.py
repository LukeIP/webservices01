"""Tests for City CRUD endpoints.

Covers:
- FR-01: Full CRUD for Cities
- FR-02: 4+ HTTP endpoints
- FR-03: JSON responses with correct status codes
- FR-14: Pagination (offset/limit with total count)
- FR-15: Filtering and sorting
- FR-17: Input validation
- NFR-04: Error handling / structured errors
"""

import pytest


class TestCreateCity:
    """POST /api/v1/cities/"""

    def test_create_city_success(self, client, auth_headers):
        """FR-01: Create a city returns 201 with city data."""
        resp = client.post("/api/v1/cities/", json={
            "name": "York",
            "region": "Yorkshire",
            "latitude": 53.9591,
            "longitude": -1.0815,
            "population": 210000,
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "York"
        assert data["region"] == "Yorkshire"
        assert data["country"] == "United Kingdom"  # default
        assert data["latitude"] == 53.9591
        assert data["population"] == 210000
        assert "id" in data
        assert "created_at" in data

    def test_create_city_requires_auth(self, client):
        """FR-04: Creating a city without auth returns 401/403."""
        resp = client.post("/api/v1/cities/", json={
            "name": "York", "region": "Yorkshire",
            "latitude": 53.9, "longitude": -1.0,
        })
        assert resp.status_code in (401, 403)

    def test_create_city_duplicate(self, client, auth_headers, sample_city):
        """NFR-04: Duplicate city name+region returns 409."""
        resp = client.post("/api/v1/cities/", json={
            "name": "Leeds",
            "region": "Yorkshire",
            "latitude": 53.8,
            "longitude": -1.5,
        }, headers=auth_headers)
        assert resp.status_code == 409
        assert resp.json()["code"] == "DUPLICATE"

    def test_create_city_invalid_latitude(self, client, auth_headers):
        """FR-17: Latitude outside -90..90 rejected."""
        resp = client.post("/api/v1/cities/", json={
            "name": "Nowhere",
            "region": "Test",
            "latitude": 999,
            "longitude": 0,
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_create_city_invalid_longitude(self, client, auth_headers):
        """FR-17: Longitude outside -180..180 rejected."""
        resp = client.post("/api/v1/cities/", json={
            "name": "Nowhere",
            "region": "Test",
            "latitude": 0,
            "longitude": -200,
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_create_city_missing_name(self, client, auth_headers):
        """FR-17: Missing required field returns 422."""
        resp = client.post("/api/v1/cities/", json={
            "region": "Yorkshire",
            "latitude": 53.8,
            "longitude": -1.5,
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_create_city_empty_name(self, client, auth_headers):
        """FR-17: Empty name string rejected."""
        resp = client.post("/api/v1/cities/", json={
            "name": "",
            "region": "Yorkshire",
            "latitude": 53.8,
            "longitude": -1.5,
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_create_city_negative_population(self, client, auth_headers):
        """FR-17: Negative population rejected."""
        resp = client.post("/api/v1/cities/", json={
            "name": "Test",
            "region": "Test",
            "latitude": 50.0,
            "longitude": -1.0,
            "population": -100,
        }, headers=auth_headers)
        assert resp.status_code == 422


class TestGetCity:
    """GET /api/v1/cities/{city_id}"""

    def test_get_city_success(self, client, sample_city):
        """FR-03: Get city by ID returns JSON with correct status."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Leeds"
        assert data["id"] == sample_city.id

    def test_get_city_not_found(self, client):
        """NFR-04: Non-existent city returns 404 with structured error."""
        resp = client.get("/api/v1/cities/99999")
        assert resp.status_code == 404
        data = resp.json()
        assert data["code"] == "NOT_FOUND"

    def test_get_city_does_not_require_auth(self, client, sample_city):
        """Read endpoints should be public (no auth required)."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}")
        assert resp.status_code == 200


class TestListCities:
    """GET /api/v1/cities/"""

    def test_list_cities_empty(self, client):
        """FR-14: Empty list returns paginated response with 0 total."""
        resp = client.get("/api/v1/cities/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["offset"] == 0
        assert data["limit"] == 20

    def test_list_cities_with_data(self, client, sample_cities):
        """FR-14: List returns paginated response with items."""
        resp = client.get("/api/v1/cities/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_list_cities_pagination(self, client, sample_cities):
        """FR-14: Pagination with offset and limit works correctly."""
        resp = client.get("/api/v1/cities/?offset=2&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["offset"] == 2
        assert data["limit"] == 2

    def test_list_cities_filter_by_region(self, client, sample_cities):
        """FR-15: Filtering by region works."""
        resp = client.get("/api/v1/cities/?region=Yorkshire")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Leeds"

    def test_list_cities_filter_case_insensitive(self, client, sample_cities):
        """FR-15: Region filter is case-insensitive."""
        resp = client.get("/api/v1/cities/?region=yorkshire")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_cities_sort_by_population(self, client, sample_cities):
        """FR-15: Sorting by population ascending."""
        resp = client.get("/api/v1/cities/?sort=population")
        assert resp.status_code == 200
        items = resp.json()["items"]
        populations = [c["population"] for c in items]
        assert populations == sorted(populations)

    def test_list_cities_sort_descending(self, client, sample_cities):
        """FR-15: Sorting by population descending with - prefix."""
        resp = client.get("/api/v1/cities/?sort=-population")
        assert resp.status_code == 200
        items = resp.json()["items"]
        populations = [c["population"] for c in items]
        assert populations == sorted(populations, reverse=True)

    def test_list_cities_sort_by_name(self, client, sample_cities):
        """FR-15: Sorting by name."""
        resp = client.get("/api/v1/cities/?sort=name")
        assert resp.status_code == 200
        items = resp.json()["items"]
        names = [c["name"] for c in items]
        assert names == sorted(names)


class TestUpdateCity:
    """PUT /api/v1/cities/{city_id}"""

    def test_update_city_success(self, client, auth_headers, sample_city):
        """FR-01: Update a city returns updated data."""
        resp = client.put(f"/api/v1/cities/{sample_city.id}", json={
            "population": 850000,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["population"] == 850000
        assert data["name"] == "Leeds"  # unchanged

    def test_update_city_partial(self, client, auth_headers, sample_city):
        """FR-01: Partial updates only change provided fields."""
        resp = client.put(f"/api/v1/cities/{sample_city.id}", json={
            "name": "Leeds City",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Leeds City"
        assert data["population"] == 800000  # unchanged

    def test_update_city_not_found(self, client, auth_headers):
        """NFR-04: Updating non-existent city returns 404."""
        resp = client.put("/api/v1/cities/99999", json={
            "name": "Ghost",
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_update_city_requires_auth(self, client, sample_city):
        """FR-04: Update without auth returns 401/403."""
        resp = client.put(f"/api/v1/cities/{sample_city.id}", json={
            "name": "Updated",
        })
        assert resp.status_code in (401, 403)


class TestDeleteCity:
    """DELETE /api/v1/cities/{city_id}"""

    def test_delete_city_as_admin(self, client, admin_headers, sample_city):
        """FR-05: Admin can delete a city, returns 204."""
        resp = client.delete(f"/api/v1/cities/{sample_city.id}", headers=admin_headers)
        assert resp.status_code == 204
        # Verify it's gone
        resp2 = client.get(f"/api/v1/cities/{sample_city.id}")
        assert resp2.status_code == 404

    def test_delete_city_as_user_forbidden(self, client, auth_headers, sample_city):
        """FR-05: Regular user cannot delete a city, returns 403."""
        resp = client.delete(f"/api/v1/cities/{sample_city.id}", headers=auth_headers)
        assert resp.status_code == 403

    def test_delete_city_not_found(self, client, admin_headers):
        """NFR-04: Deleting non-existent city returns 404."""
        resp = client.delete("/api/v1/cities/99999", headers=admin_headers)
        assert resp.status_code == 404

    def test_delete_city_no_auth(self, client, sample_city):
        """FR-04: Delete without auth returns 401/403."""
        resp = client.delete(f"/api/v1/cities/{sample_city.id}")
        assert resp.status_code in (401, 403)
