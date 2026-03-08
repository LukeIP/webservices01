"""Unit tests for the AnalyticsService.

Covers:
- FR-06: Liveability scoring via service layer
- FR-08: Trend computation
- FR-09: Anomaly detection logic
"""

import pytest
from app.services.analytics_service import AnalyticsService
from app.exceptions import NotFoundException, AppException


class TestAnalyticsServiceLiveability:
    """AnalyticsService.compute_liveability_for_city"""

    def test_compute_with_data(self, db, sample_city, climate_data, socioeconomic_data):
        service = AnalyticsService(db)
        result = service.compute_liveability_for_city(sample_city.id)
        assert result["city_name"] == "Leeds"
        assert 0 <= result["overall_score"] <= 100

    def test_compute_no_data(self, db, sample_city):
        """Defaults to 50 when no metric data exists."""
        service = AnalyticsService(db)
        result = service.compute_liveability_for_city(sample_city.id)
        assert result["overall_score"] == 50.0

    def test_compute_city_not_found(self, db):
        service = AnalyticsService(db)
        with pytest.raises(NotFoundException):
            service.compute_liveability_for_city(99999)

    def test_stores_score_in_db(self, db, sample_city, climate_data, socioeconomic_data):
        """Computed score is persisted in liveability_scores table."""
        from app.models.liveability_score import LiveabilityScore
        service = AnalyticsService(db)
        service.compute_liveability_for_city(sample_city.id)
        scores = db.query(LiveabilityScore).filter(LiveabilityScore.city_id == sample_city.id).all()
        assert len(scores) >= 1


class TestAnalyticsServiceCompare:
    """AnalyticsService.compare_cities"""

    def test_compare_multiple(self, db, sample_cities):
        service = AnalyticsService(db)
        ids = [c.id for c in sample_cities[:3]]
        results = service.compare_cities(ids)
        assert len(results) == 3

    def test_compare_skips_missing(self, db, sample_city):
        service = AnalyticsService(db)
        results = service.compare_cities([sample_city.id, 99999])
        assert len(results) == 1


class TestAnalyticsServiceTrends:
    """AnalyticsService.get_trends"""

    def test_trends_returns_data(self, db, sample_city, climate_data):
        service = AnalyticsService(db)
        result = service.get_trends(sample_city.id, metric="aqi", period="12m")
        assert result["metric"] == "aqi"
        assert len(result["data_points"]) > 0

    def test_trends_invalid_metric_raises(self, db, sample_city):
        service = AnalyticsService(db)
        with pytest.raises(AppException) as exc_info:
            service.get_trends(sample_city.id, metric="invalid")
        assert exc_info.value.status_code == 400

    def test_trends_city_not_found(self, db):
        service = AnalyticsService(db)
        with pytest.raises(NotFoundException):
            service.get_trends(99999)


class TestAnalyticsServiceAnomalies:
    """AnalyticsService.detect_anomalies"""

    def test_detect_anomalies(self, db, sample_city, climate_data):
        service = AnalyticsService(db)
        result = service.detect_anomalies(sample_city.id, threshold=2.0)
        assert result["threshold"] == 2.0
        # Our fixture has an extreme outlier (45°C, 300 AQI)
        assert len(result["anomalies"]) > 0

    def test_no_anomalies_with_high_threshold(self, db, sample_city, climate_data):
        """Very high threshold → fewer or no anomalies."""
        service = AnalyticsService(db)
        result = service.detect_anomalies(sample_city.id, threshold=5.0)
        # Should have fewer anomalies, possibly none
        low_result = service.detect_anomalies(sample_city.id, threshold=1.5)
        assert len(result["anomalies"]) <= len(low_result["anomalies"])

    def test_no_data_returns_empty(self, db, sample_city):
        service = AnalyticsService(db)
        result = service.detect_anomalies(sample_city.id)
        assert result["anomalies"] == []
