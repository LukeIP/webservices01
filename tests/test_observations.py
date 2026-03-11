"""Tests for Observation CRUD endpoints.

Covers:
- FR-01: CRUD for Observations
- FR-03: JSON responses with correct HTTP status codes
- FR-05: RBAC — users can only edit/delete own observations
- FR-14: Pagination on list endpoints
- FR-17: Input validation
"""

import pytest


class TestCreateObservation:
    """POST /api/v1/cities/{city_id}/observations"""

    def test_create_observation_success(self, client, auth_headers, sample_city):
        """FR-01: Create an observation returns 201."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/observations",
            json={"category": "air_quality", "value": 85.0, "note": "Clear day"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["category"] == "air_quality"
        assert data["value"] == 85.0
        assert data["note"] == "Clear day"
        assert data["city_id"] == sample_city.id
        assert "id" in data

    def test_create_observation_no_note(self, client, auth_headers, sample_city):
        """FR-01: Note is optional."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/observations",
            json={"category": "noise", "value": 50.0},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["note"] is None

    def test_create_observation_city_not_found(self, client, auth_headers):
        """NFR-04: Observation for non-existent city returns 404."""
        resp = client.post(
            "/api/v1/cities/99999/observations",
            json={"category": "safety", "value": 60.0},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_create_observation_requires_auth(self, client, sample_city):
        """FR-04: Creating observation without auth fails."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/observations",
            json={"category": "air_quality", "value": 70.0},
        )
        assert resp.status_code in (401, 403)

    def test_create_observation_value_out_of_range(self, client, auth_headers, sample_city):
        """FR-17: Value must be 0-100."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/observations",
            json={"category": "air_quality", "value": 150.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_observation_negative_value(self, client, auth_headers, sample_city):
        """FR-17: Negative value rejected."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/observations",
            json={"category": "air_quality", "value": -5.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_observation_empty_category(self, client, auth_headers, sample_city):
        """FR-17: Empty category string rejected."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/observations",
            json={"category": "", "value": 50.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestListObservations:
    """GET /api/v1/cities/{city_id}/observations"""

    def test_list_observations_empty(self, client, sample_city):
        """FR-14: Empty list with pagination metadata."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/observations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_observations_with_data(self, client, sample_city, sample_observation):
        """FR-14: Returns observations for a city with pagination."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/observations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["category"] == "air_quality"

    def test_list_observations_city_not_found(self, client):
        """NFR-04: Listing observations for non-existent city returns 404."""
        resp = client.get("/api/v1/cities/99999/observations")
        assert resp.status_code == 404

    def test_list_observations_pagination(self, client, auth_headers, sample_city):
        """FR-14: Pagination with offset/limit."""
        # Create 5 observations
        for i in range(5):
            client.post(
                f"/api/v1/cities/{sample_city.id}/observations",
                json={"category": "noise", "value": float(i * 10)},
                headers=auth_headers,
            )
        resp = client.get(f"/api/v1/cities/{sample_city.id}/observations?offset=2&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5


class TestUpdateObservation:
    """PUT /api/v1/observations/{obs_id}"""

    def test_update_own_observation(self, client, auth_headers, sample_observation):
        """FR-01: User can update their own observation."""
        resp = client.put(
            f"/api/v1/observations/{sample_observation.id}",
            json={"value": 90.0, "note": "Updated note"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["value"] == 90.0
        assert data["note"] == "Updated note"

    def test_update_others_observation_forbidden(self, client, other_auth_headers, sample_observation):
        """FR-05: Cannot update another user's observation."""
        resp = client.put(
            f"/api/v1/observations/{sample_observation.id}",
            json={"value": 10.0},
            headers=other_auth_headers,
        )
        assert resp.status_code == 403

    def test_admin_can_update_any_observation(self, client, admin_headers, sample_observation):
        """FR-05: Admin can update any observation."""
        resp = client.put(
            f"/api/v1/observations/{sample_observation.id}",
            json={"value": 95.0},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_update_observation_not_found(self, client, auth_headers):
        """NFR-04: Updating non-existent observation returns 404."""
        resp = client.put(
            "/api/v1/observations/99999",
            json={"value": 50.0},
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestDeleteObservation:
    """DELETE /api/v1/observations/{obs_id}"""

    def test_delete_own_observation(self, client, auth_headers, sample_observation):
        """FR-01: User can delete their own observation, returns 204."""
        resp = client.delete(
            f"/api/v1/observations/{sample_observation.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

    def test_delete_others_observation_forbidden(self, client, other_auth_headers, sample_observation):
        """FR-05: Cannot delete another user's observation."""
        resp = client.delete(
            f"/api/v1/observations/{sample_observation.id}",
            headers=other_auth_headers,
        )
        assert resp.status_code == 403

    def test_admin_can_delete_any_observation(self, client, admin_headers, sample_observation):
        """FR-05: Admin can delete any observation."""
        resp = client.delete(
            f"/api/v1/observations/{sample_observation.id}",
            headers=admin_headers,
        )
        assert resp.status_code == 204

    def test_delete_observation_not_found(self, client, auth_headers):
        """NFR-04: Deleting non-existent observation returns 404."""
        resp = client.delete(
            "/api/v1/observations/99999",
            headers=auth_headers,
        )
        assert resp.status_code == 404
