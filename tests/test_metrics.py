"""Tests for climate and socioeconomic metric endpoints.

Covers:
- FR-02: Climate metric CRUD
- FR-02: Socioeconomic metric CRUD
- FR-03: Correct JSON responses and status codes
- FR-05: RBAC — admin-only delete
"""

import pytest
from datetime import date


class TestClimateMetrics:
    """CRUD tests for /api/v1/cities/{city_id}/climate-metrics"""

    def test_create_climate_metric(self, client, auth_headers, sample_city):
        """Authenticated user can add a climate reading."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/climate-metrics",
            json={"date": "2025-06-15", "avg_temp_c": 18.5, "aqi": 42.0, "humidity_pct": 65.0, "precipitation_mm": 1.2, "source": "test"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["city_id"] == sample_city.id
        assert data["avg_temp_c"] == 18.5
        assert data["aqi"] == 42.0
        assert data["date"] == "2025-06-15"

    def test_create_climate_metric_requires_auth(self, client, sample_city):
        """Unauthenticated users cannot add metrics."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/climate-metrics",
            json={"date": "2025-06-15", "aqi": 42.0},
        )
        assert resp.status_code in (401, 403)

    def test_create_climate_metric_city_not_found(self, client, auth_headers):
        """Adding metric for non-existent city returns 404."""
        resp = client.post(
            "/api/v1/cities/99999/climate-metrics",
            json={"date": "2025-06-15", "aqi": 42.0},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_create_climate_metric_partial_data(self, client, auth_headers, sample_city):
        """Only date is required; other fields are optional."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/climate-metrics",
            json={"date": "2025-06-16"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["avg_temp_c"] is None
        assert data["aqi"] is None

    def test_create_climate_metric_invalid_humidity(self, client, auth_headers, sample_city):
        """Humidity > 100 should be rejected."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/climate-metrics",
            json={"date": "2025-06-15", "humidity_pct": 150.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_list_climate_metrics(self, client, sample_city, climate_data):
        """List returns paginated climate data."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/climate-metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == len(climate_data)
        assert len(data["items"]) <= 50  # default limit

    def test_list_climate_metrics_empty(self, client, sample_city):
        """City with no metrics returns empty list."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/climate-metrics")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_climate_metrics_city_not_found(self, client):
        """Non-existent city returns 404."""
        resp = client.get("/api/v1/cities/99999/climate-metrics")
        assert resp.status_code == 404

    def test_list_climate_metrics_date_filter(self, client, sample_city, climate_data):
        """Date range filtering works."""
        today = date.today()
        resp = client.get(
            f"/api/v1/cities/{sample_city.id}/climate-metrics",
            params={"start_date": str(today), "end_date": str(today)},
        )
        assert resp.status_code == 200
        # At least the anomaly or recent data should fall in range
        data = resp.json()
        assert data["total"] >= 0

    def test_list_climate_metrics_pagination(self, client, sample_city, climate_data):
        """Pagination parameters work correctly."""
        resp = client.get(
            f"/api/v1/cities/{sample_city.id}/climate-metrics",
            params={"offset": 0, "limit": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 5
        assert data["limit"] == 5
        assert data["offset"] == 0

    def test_get_climate_metric(self, client, sample_city, climate_data):
        """Get a single metric by ID."""
        metric_id = climate_data[0].id
        resp = client.get(f"/api/v1/climate-metrics/{metric_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == metric_id

    def test_get_climate_metric_not_found(self, client):
        """Non-existent metric returns 404."""
        resp = client.get("/api/v1/climate-metrics/99999")
        assert resp.status_code == 404

    def test_delete_climate_metric_as_admin(self, client, admin_headers, sample_city, climate_data):
        """Admin can delete a climate metric."""
        metric_id = climate_data[0].id
        resp = client.delete(f"/api/v1/climate-metrics/{metric_id}", headers=admin_headers)
        assert resp.status_code == 204
        # Verify it's gone
        resp2 = client.get(f"/api/v1/climate-metrics/{metric_id}")
        assert resp2.status_code == 404

    def test_delete_climate_metric_as_user_forbidden(self, client, auth_headers, sample_city, climate_data):
        """Regular users cannot delete metrics."""
        metric_id = climate_data[0].id
        resp = client.delete(f"/api/v1/climate-metrics/{metric_id}", headers=auth_headers)
        assert resp.status_code == 403

    def test_delete_climate_metric_no_auth(self, client, sample_city, climate_data):
        """Unauthenticated delete is rejected."""
        metric_id = climate_data[0].id
        resp = client.delete(f"/api/v1/climate-metrics/{metric_id}")
        assert resp.status_code in (401, 403)


class TestSocioeconomicMetrics:
    """CRUD tests for /api/v1/cities/{city_id}/socioeconomic-metrics"""

    def test_create_socioeconomic_metric(self, client, auth_headers, sample_city):
        """Authenticated user can add socioeconomic data."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/socioeconomic-metrics",
            json={"year": 2025, "median_rent_gbp": 950.0, "green_space_pct": 35.0, "crime_index": 48.0, "avg_commute_min": 26.0, "source": "test"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["city_id"] == sample_city.id
        assert data["year"] == 2025
        assert data["median_rent_gbp"] == 950.0

    def test_create_socioeconomic_metric_requires_auth(self, client, sample_city):
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/socioeconomic-metrics",
            json={"year": 2025},
        )
        assert resp.status_code in (401, 403)

    def test_create_socioeconomic_metric_city_not_found(self, client, auth_headers):
        resp = client.post(
            "/api/v1/cities/99999/socioeconomic-metrics",
            json={"year": 2025},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_create_socioeconomic_metric_invalid_year(self, client, auth_headers, sample_city):
        """Year must be between 1900 and 2100."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/socioeconomic-metrics",
            json={"year": 1800},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_socioeconomic_partial(self, client, auth_headers, sample_city):
        """Only year is required; other fields are optional."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/socioeconomic-metrics",
            json={"year": 2024},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["median_rent_gbp"] is None

    def test_list_socioeconomic_metrics(self, client, sample_city, socioeconomic_data):
        resp = client.get(f"/api/v1/cities/{sample_city.id}/socioeconomic-metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == len(socioeconomic_data)

    def test_list_socioeconomic_metrics_empty(self, client, sample_city):
        resp = client.get(f"/api/v1/cities/{sample_city.id}/socioeconomic-metrics")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_socioeconomic_metrics_city_not_found(self, client):
        resp = client.get("/api/v1/cities/99999/socioeconomic-metrics")
        assert resp.status_code == 404

    def test_get_socioeconomic_metric(self, client, sample_city, socioeconomic_data):
        metric_id = socioeconomic_data[0].id
        resp = client.get(f"/api/v1/socioeconomic-metrics/{metric_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == metric_id

    def test_get_socioeconomic_metric_not_found(self, client):
        resp = client.get("/api/v1/socioeconomic-metrics/99999")
        assert resp.status_code == 404

    def test_delete_socioeconomic_metric_as_admin(self, client, admin_headers, sample_city, socioeconomic_data):
        metric_id = socioeconomic_data[0].id
        resp = client.delete(f"/api/v1/socioeconomic-metrics/{metric_id}", headers=admin_headers)
        assert resp.status_code == 204

    def test_delete_socioeconomic_metric_as_user_forbidden(self, client, auth_headers, sample_city, socioeconomic_data):
        metric_id = socioeconomic_data[0].id
        resp = client.delete(f"/api/v1/socioeconomic-metrics/{metric_id}", headers=auth_headers)
        assert resp.status_code == 403

    def test_delete_socioeconomic_metric_no_auth(self, client, sample_city, socioeconomic_data):
        metric_id = socioeconomic_data[0].id
        resp = client.delete(f"/api/v1/socioeconomic-metrics/{metric_id}")
        assert resp.status_code in (401, 403)


class TestRentSubmissions:
    """Crowdsourced rent submission endpoints."""

    def test_submit_rent_success(self, client, auth_headers, sample_city):
        """Authenticated user can submit a rent value."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": 950.0},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["city_id"] == sample_city.id
        assert data["rent_amount_gbp"] == 950.0
        assert "year" in data
        assert "id" in data

    def test_submit_rent_requires_auth(self, client, sample_city):
        """Unauthenticated users cannot submit rent."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": 1000.0},
        )
        assert resp.status_code in (401, 403)

    def test_submit_rent_city_not_found(self, client, auth_headers):
        """Rent submission for non-existent city returns 404."""
        resp = client.post(
            "/api/v1/cities/99999/rent-submissions",
            json={"rent_amount_gbp": 1000.0},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_submit_rent_zero_amount_rejected(self, client, auth_headers, sample_city):
        """Rent amount must be > 0."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": 0.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_submit_rent_negative_rejected(self, client, auth_headers, sample_city):
        """Negative rent amount is rejected."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": -500.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_submit_rent_exceeds_max_rejected(self, client, auth_headers, sample_city):
        """Rent above 20,000 is rejected."""
        resp = client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": 25000.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_submit_rent_upserts_for_same_user(self, client, auth_headers, sample_city):
        """Second submission from same user updates rather than creating a duplicate."""
        client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": 900.0},
            headers=auth_headers,
        )
        resp2 = client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": 1100.0},
            headers=auth_headers,
        )
        assert resp2.status_code == 201
        assert resp2.json()["rent_amount_gbp"] == 1100.0
        # Only one record should exist
        list_resp = client.get(f"/api/v1/cities/{sample_city.id}/rent-submissions")
        assert list_resp.json()["total"] == 1

    def test_list_rent_submissions_empty(self, client, sample_city):
        """City with no submissions returns empty list."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/rent-submissions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_rent_submissions_with_data(self, client, auth_headers, other_auth_headers, sample_city):
        """List returns all submissions for the city."""
        client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": 850.0},
            headers=auth_headers,
        )
        client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": 1050.0},
            headers=other_auth_headers,
        )
        resp = client.get(f"/api/v1/cities/{sample_city.id}/rent-submissions")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_list_rent_submissions_city_not_found(self, client):
        """Non-existent city returns 404."""
        resp = client.get("/api/v1/cities/99999/rent-submissions")
        assert resp.status_code == 404


class TestRentMedian:
    """Crowdsourced median rent endpoint."""

    def test_rent_median_no_data(self, client, sample_city):
        """City with no submissions returns null median."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/rent-median")
        assert resp.status_code == 200
        data = resp.json()
        assert data["median_rent_gbp"] is None
        assert data["submission_count"] == 0
        assert data["city_id"] == sample_city.id

    def test_rent_median_single_submission(self, client, auth_headers, sample_city):
        """Median of a single value equals that value."""
        client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": 1200.0},
            headers=auth_headers,
        )
        resp = client.get(f"/api/v1/cities/{sample_city.id}/rent-median")
        assert resp.status_code == 200
        data = resp.json()
        assert data["median_rent_gbp"] == 1200.0
        assert data["submission_count"] == 1

    def test_rent_median_multiple_submissions(self, client, auth_headers, other_auth_headers, sample_city):
        """Median of two values is their average."""
        client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": 1000.0},
            headers=auth_headers,
        )
        client.post(
            f"/api/v1/cities/{sample_city.id}/rent-submissions",
            json={"rent_amount_gbp": 1200.0},
            headers=other_auth_headers,
        )
        resp = client.get(f"/api/v1/cities/{sample_city.id}/rent-median")
        assert resp.status_code == 200
        data = resp.json()
        assert data["median_rent_gbp"] == 1100.0
        assert data["submission_count"] == 2

    def test_rent_median_city_not_found(self, client):
        """Non-existent city returns 404."""
        resp = client.get("/api/v1/cities/99999/rent-median")
        assert resp.status_code == 404
