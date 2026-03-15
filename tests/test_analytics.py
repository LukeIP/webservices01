"""Tests for analytics endpoints: liveability, comparison, trends, anomalies.

Covers:
- FR-06: Composite liveability scoring
- FR-07: City comparison endpoint
- FR-08: Time-series trends
- FR-09: Anomaly detection
- FR-03: JSON responses with correct status codes
"""

import pytest


class TestLiveability:
    """GET /api/v1/cities/{city_id}/liveability"""

    def test_liveability_with_full_data(self, client, sample_city, climate_data, socioeconomic_data):
        """FR-06: Liveability computed from climate + socioeconomic data."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/liveability")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_score" in data
        assert "climate_score" in data
        assert "affordability_score" in data
        assert "safety_score" in data
        assert "environment_score" in data
        assert "weights_used" in data
        assert data["city_name"] == "Leeds"
        assert data["city_id"] == sample_city.id
        # Scores should be within 0-100
        for key in ["overall_score", "climate_score", "affordability_score", "safety_score", "environment_score"]:
            assert 0 <= data[key] <= 100, f"{key} = {data[key]} out of range"

    def test_liveability_no_metrics(self, client, sample_city):
        """FR-06: Liveability with no metrics uses defaults (50)."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/liveability")
        assert resp.status_code == 200
        data = resp.json()
        # With no data, all sub-scores should be default 50
        assert data["overall_score"] == 50.0

    def test_liveability_city_not_found(self, client):
        """NFR-04: Non-existent city returns 404."""
        resp = client.get("/api/v1/cities/99999/liveability")
        assert resp.status_code == 404

    def test_liveability_weights_included(self, client, sample_city, climate_data, socioeconomic_data):
        """FR-06: Response includes the weights used for transparency."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/liveability")
        data = resp.json()
        weights = data["weights_used"]
        assert "climate" in weights
        assert "affordability" in weights
        assert "safety" in weights
        assert "environment" in weights
        # Weights should sum to 1.0
        assert abs(sum(weights.values()) - 1.0) < 0.01


class TestCompareCities:
    """GET /api/v1/cities/compare"""

    def test_compare_two_cities(self, client, sample_cities):
        """FR-07: Compare returns liveability for multiple cities."""
        ids_param = f"{sample_cities[0].id},{sample_cities[1].id}"
        resp = client.get(f"/api/v1/cities/compare?ids={ids_param}")
        assert resp.status_code == 200
        data = resp.json()
        assert "cities" in data
        assert len(data["cities"]) == 2

    def test_compare_skips_missing_cities(self, client, sample_cities):
        """FR-07: Missing IDs are silently skipped."""
        ids_param = f"{sample_cities[0].id},99999"
        resp = client.get(f"/api/v1/cities/compare?ids={ids_param}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["cities"]) == 1

    def test_compare_all_missing(self, client):
        """FR-07: All missing IDs returns empty list."""
        resp = client.get("/api/v1/cities/compare?ids=99998,99999")
        assert resp.status_code == 200
        assert resp.json()["cities"] == []

    def test_compare_single_city(self, client, sample_city):
        """FR-07: Works with a single city too."""
        resp = client.get(f"/api/v1/cities/compare?ids={sample_city.id}")
        assert resp.status_code == 200
        assert len(resp.json()["cities"]) == 1


class TestTrends:
    """GET /api/v1/cities/{city_id}/trends"""

    def test_trends_with_data(self, client, sample_city, climate_data):
        """FR-08: Returns time-series trend data."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/trends?metric=aqi&period=12m")
        assert resp.status_code == 200
        data = resp.json()
        assert data["city_id"] == sample_city.id
        assert data["metric"] == "aqi"
        assert data["period"] == "12m"
        assert len(data["data_points"]) > 0
        # Each data point should have date and value
        for pt in data["data_points"]:
            assert "date" in pt
            assert "value" in pt

    def test_trends_no_data(self, client, sample_city):
        """FR-08: City with no climate data returns empty data_points."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/trends?metric=aqi")
        assert resp.status_code == 200
        assert resp.json()["data_points"] == []

    def test_trends_invalid_metric(self, client, sample_city, climate_data):
        """NFR-04: Invalid metric returns 400."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/trends?metric=invalid_metric")
        assert resp.status_code == 400

    def test_trends_city_not_found(self, client):
        """NFR-04: Non-existent city returns 404."""
        resp = client.get("/api/v1/cities/99999/trends?metric=aqi")
        assert resp.status_code == 404

    def test_trends_different_periods(self, client, sample_city, climate_data):
        """FR-08: Different period values work."""
        for period in ["3m", "6m", "12m", "24m"]:
            resp = client.get(f"/api/v1/cities/{sample_city.id}/trends?metric=aqi&period={period}")
            assert resp.status_code == 200

    def test_trends_temp_metric(self, client, sample_city, climate_data):
        """FR-08: Trend works for temperature metric."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/trends?metric=temp")
        assert resp.status_code == 200
        assert len(resp.json()["data_points"]) > 0


class TestAnomalies:
    """GET /api/v1/cities/{city_id}/anomalies"""

    def test_anomalies_detected(self, client, sample_city, climate_data):
        """FR-09: Anomalies are detected in climate data."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/anomalies?threshold=2.0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["city_id"] == sample_city.id
        assert data["threshold"] == 2.0
        assert len(data["anomalies"]) > 0
        # Each anomaly should have required fields
        for a in data["anomalies"]:
            assert "date" in a
            assert "metric" in a
            assert "value" in a
            assert "z_score" in a
            assert a["is_anomaly"] is True

    def test_anomalies_high_threshold(self, client, sample_city, climate_data):
        """FR-09: Higher threshold yields fewer anomalies."""
        resp_low = client.get(f"/api/v1/cities/{sample_city.id}/anomalies?threshold=1.5")
        resp_high = client.get(f"/api/v1/cities/{sample_city.id}/anomalies?threshold=3.0")
        low_count = len(resp_low.json()["anomalies"])
        high_count = len(resp_high.json()["anomalies"])
        assert high_count <= low_count

    def test_anomalies_no_data(self, client, sample_city):
        """FR-09: City with no data returns empty anomalies."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/anomalies")
        assert resp.status_code == 200
        assert resp.json()["anomalies"] == []

    def test_anomalies_city_not_found(self, client):
        """NFR-04: Non-existent city returns 404."""
        resp = client.get("/api/v1/cities/99999/anomalies")
        assert resp.status_code == 404

    def test_anomalies_z_scores_are_significant(self, client, sample_city, climate_data):
        """FR-09: Reported z-scores exceed the threshold."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/anomalies?threshold=2.0")
        for a in resp.json()["anomalies"]:
            assert abs(a["z_score"]) >= 2.0


class TestNarrative:
    """GET /api/v1/cities/{city_id}/narrative"""

    def test_narrative_fallback(self, client, sample_city, climate_data, socioeconomic_data):
        """FR-12: Narrative generated (fallback mode without API key)."""
        resp = client.get(f"/api/v1/cities/{sample_city.id}/narrative")
        assert resp.status_code == 200
        data = resp.json()
        assert data["city_name"] == "Leeds"
        assert data["city_id"] == sample_city.id
        assert len(data["narrative"]) > 20  # Should be a meaningful string

    def test_narrative_city_not_found(self, client):
        """NFR-04: Non-existent city returns 404."""
        resp = client.get("/api/v1/cities/99999/narrative")
        assert resp.status_code == 404
