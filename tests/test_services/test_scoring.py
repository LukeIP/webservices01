"""Unit tests for the scoring utility module.

Covers:
- FR-06: Composite liveability scoring algorithm
- Normalisation functions
- Weight handling
"""

import pytest
from app.utils.scoring import (
    normalise_aqi,
    normalise_temp,
    normalise_rent,
    normalise_crime,
    normalise_green_space,
    compute_liveability,
    DEFAULT_WEIGHTS,
)


class TestNormaliseAQI:
    """AQI normalisation: lower AQI = better (higher score)."""

    def test_zero_aqi(self):
        assert normalise_aqi(0) == 100.0

    def test_moderate_aqi(self):
        score = normalise_aqi(50)
        assert 0 <= score <= 100

    def test_very_high_aqi(self):
        score = normalise_aqi(500)
        assert score == 0.0

    def test_negative_aqi_defaults(self):
        """Negative AQI should return default 50."""
        assert normalise_aqi(-1) == 50.0


class TestNormaliseTemp:
    """Temperature normalisation: ideal ~17.5C."""

    def test_ideal_temp(self):
        assert normalise_temp(17.5) == 100.0

    def test_cold_temp(self):
        score = normalise_temp(0)
        assert score < 100
        assert score >= 0

    def test_hot_temp(self):
        score = normalise_temp(35)
        assert score < 100
        assert score >= 0

    def test_extreme_cold(self):
        score = normalise_temp(-20)
        assert score == 0  # Way below ideal


class TestNormaliseRent:
    """Rent normalisation: lower rent = higher affordability score."""

    def test_zero_rent(self):
        assert normalise_rent(0) == 100.0

    def test_max_rent(self):
        assert normalise_rent(2500) == 0.0

    def test_mid_rent(self):
        score = normalise_rent(1250)
        assert 40 <= score <= 60  # Should be ~50

    def test_negative_rent(self):
        assert normalise_rent(-100) == 100.0


class TestNormaliseCrime:
    """Crime normalisation: lower crime = higher safety score."""

    def test_zero_crime(self):
        assert normalise_crime(0) == 100.0

    def test_max_crime(self):
        assert normalise_crime(100) == 0.0

    def test_mid_crime(self):
        score = normalise_crime(50)
        assert score == 50.0


class TestNormaliseGreenSpace:
    """Green space: percentage directly maps to 0-100."""

    def test_full_green(self):
        assert normalise_green_space(100) == 100.0

    def test_no_green(self):
        assert normalise_green_space(0) == 0.0

    def test_over_100_capped(self):
        assert normalise_green_space(120) == 100.0

    def test_negative_capped(self):
        assert normalise_green_space(-10) == 0.0


class TestComputeLiveability:
    """Integration test for the composite liveability computation."""

    def test_all_defaults(self):
        """All None values → all defaults → overall = 50."""
        result = compute_liveability()
        assert result["overall_score"] == 50.0
        assert result["climate_score"] == 50.0
        assert result["affordability_score"] == 50.0
        assert result["safety_score"] == 50.0
        assert result["environment_score"] == 50.0

    def test_perfect_scores(self):
        """Perfect metrics → high scores."""
        result = compute_liveability(
            avg_temp=17.5,
            aqi=0,
            median_rent=0,
            crime_index=0,
            green_space_pct=100,
        )
        assert result["overall_score"] == 100.0
        assert result["climate_score"] == 100.0
        assert result["affordability_score"] == 100.0
        assert result["safety_score"] == 100.0
        assert result["environment_score"] == 100.0

    def test_worst_scores(self):
        """Worst metrics → low scores."""
        result = compute_liveability(
            avg_temp=-20,
            aqi=500,
            median_rent=2500,
            crime_index=100,
            green_space_pct=0,
        )
        assert result["overall_score"] == 0.0

    def test_custom_weights(self):
        """Custom weights are used and returned."""
        custom = {"climate": 0.5, "affordability": 0.2, "safety": 0.2, "environment": 0.1}
        result = compute_liveability(weights=custom)
        assert result["weights_used"] == custom

    def test_default_weights_sum_to_one(self):
        assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 0.001

    def test_mixed_metrics(self):
        """Realistic mix of good/bad metrics."""
        result = compute_liveability(
            avg_temp=15.0,
            aqi=40,
            median_rent=900,
            crime_index=30,
            green_space_pct=40,
        )
        assert 0 <= result["overall_score"] <= 100
        # Leeds-like metrics should give a moderate-good score
        assert result["overall_score"] > 30

    def test_return_structure(self):
        """Result dict has all required keys."""
        result = compute_liveability()
        required_keys = {"overall_score", "climate_score", "affordability_score",
                         "safety_score", "environment_score", "weights_used"}
        assert required_keys == set(result.keys())
