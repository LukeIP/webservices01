"""Weather service — fetches and stores Open-Meteo climate data for a city."""

import random
import time
from datetime import date, timedelta

import httpx
from sqlalchemy.orm import Session

from app.models.climate_metric import ClimateMetric


def _fetch_open_meteo(lat: float, lon: float, start_d: date, end_d: date) -> dict:
    """Fetch daily weather data from Open-Meteo archive API with retry."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_d.isoformat(),
        "end_date": end_d.isoformat(),
        "daily": "temperature_2m_mean,precipitation_sum,relative_humidity_2m_mean",
        "timezone": "Europe/London",
    }
    for _ in range(3):
        try:
            resp = httpx.get(url, params=params, timeout=10.0)
            resp.raise_for_status()
            return resp.json()["daily"]
        except Exception as e:
            print(f"[weather_service] Open-Meteo error: {e}, retrying...")
            time.sleep(2)
    return {}


def fetch_and_store_weather(city_id: int, latitude: float, longitude: float, db: Session) -> int:
    """Fetch 365 days of weather for a city and persist as ClimateMetric rows.

    Skips dates that already have records to avoid duplicates.
    Returns the count of new records inserted.
    """
    today = date.today()
    end_date = today - timedelta(days=5)   # Open-Meteo archive is ~5 days delayed
    start_date = end_date - timedelta(days=364)

    # Collect existing dates so we don't insert duplicates
    existing_dates = {
        row[0]
        for row in db.query(ClimateMetric.date)
        .filter(ClimateMetric.city_id == city_id)
        .all()
    }

    daily_data = _fetch_open_meteo(latitude, longitude, start_date, end_date)
    if not daily_data or "time" not in daily_data:
        print(f"[weather_service] No data returned for city_id={city_id}")
        return 0

    count = 0
    for i, d_str in enumerate(daily_data["time"]):
        record_date = date.fromisoformat(d_str)
        if record_date in existing_dates:
            continue

        temp = daily_data["temperature_2m_mean"][i]
        precip = daily_data["precipitation_sum"][i]
        humidity_list = daily_data.get("relative_humidity_2m_mean", [])
        hum_val = humidity_list[i] if len(humidity_list) > i else None

        if temp is None:
            temp = 10.0
        if precip is None:
            precip = 0.0
        if hum_val is None:
            hum_val = 70.0

        # AQI is not available from this free endpoint; approximate from season + rain
        is_winter = any(m in d_str for m in ("-12-", "-01-", "-02-"))
        aqi = 35 + random.uniform(-5, 15)
        if is_winter:
            aqi += 15
        if precip > 2:
            aqi -= 10

        db.add(ClimateMetric(
            city_id=city_id,
            date=record_date,
            avg_temp_c=round(temp, 1),
            aqi=max(5, round(aqi, 1)),
            humidity_pct=round(hum_val, 1),
            precipitation_mm=round(precip, 1),
            source="open_meteo",
        ))
        count += 1

    if count:
        db.commit()

    print(f"[weather_service] Inserted {count} climate records for city_id={city_id}")
    return count
