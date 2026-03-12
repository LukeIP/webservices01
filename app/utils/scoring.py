"""Liveability scoring algorithm."""

import math


DEFAULT_WEIGHTS = {
    "climate": 0.25,
    "affordability": 0.30,
    "safety": 0.25,
    "environment": 0.20,
}


def normalise_aqi(aqi: float) -> float:
    """Normalise AQI to 0-100 score (lower AQI = higher score)."""
    # AQI ranges 0-500; we invert and cap
    return max(0, min(100, 100 - (aqi / 5) * 100)) if aqi >= 0 else 50.0


def normalise_temp(avg_temp: float) -> float:
    """Score temperature comfort (ideal ~15-20C for UK)."""
    ideal = 17.5
    deviation = abs(avg_temp - ideal)
    return max(0, 100 - deviation * 5)


def normalise_rent(rent: float, max_rent: float = 2500.0) -> float:
    """Normalise rent to affordability score (lower rent = higher score)."""
    if rent <= 0:
        return 100.0
    return max(0, min(100, (1 - rent / max_rent) * 100))


def normalise_crime(crime_index: float, max_crime: float = 100.0) -> float:
    """Normalise crime index to safety score (lower crime = higher score)."""
    return max(0, min(100, (1 - crime_index / max_crime) * 100))


def normalise_green_space(green_pct: float) -> float:
    """Green space percentage is already 0-100."""
    return max(0, min(100, green_pct))


def compute_liveability(
    avg_temp: float | None = None,
    aqi: float | None = None,
    median_rent: float | None = None,
    crime_index: float | None = None,
    green_space_pct: float | None = None,
    weights: dict | None = None,
) -> dict:
    """Compute liveability scores from raw metrics.

    Returns a dict with individual scores and overall score.
    """
    w = weights or DEFAULT_WEIGHTS.copy()

    # Climate score: average of temp and AQI sub-scores
    temp_score = normalise_temp(avg_temp) if avg_temp is not None else 50.0
    aqi_score = normalise_aqi(aqi) if aqi is not None else 50.0
    climate_score = (temp_score + aqi_score) / 2

    # Affordability
    affordability_score = normalise_rent(median_rent) if median_rent is not None else 50.0

    # Safety
    safety_score = normalise_crime(crime_index) if crime_index is not None else 50.0

    # Environment
    environment_score = normalise_green_space(green_space_pct) if green_space_pct is not None else 50.0

    # Overall weighted score
    overall = (
        w["climate"] * climate_score
        + w["affordability"] * affordability_score
        + w["safety"] * safety_score
        + w["environment"] * environment_score
    )

    return {
        "overall_score": round(overall, 2),
        "climate_score": round(climate_score, 2),
        "affordability_score": round(affordability_score, 2),
        "safety_score": round(safety_score, 2),
        "environment_score": round(environment_score, 2),
        "weights_used": w,
    }
