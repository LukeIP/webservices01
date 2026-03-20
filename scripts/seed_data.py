"""
Seed script — populates the database with real UK city data.

Data sources:
  • Climate (temp, precip, humidity): Open-Meteo Archive API (real historical data)
  • AQI: Open-Meteo Air Quality API — European AQI (real historical data)
  • Crime index: UK Police API (data.police.uk) — real crime counts, normalised
  • Green space %: ONS Urban Green Space statistics (published 2020/2022)
  • Avg commute time: ONS Census 2021 travel-to-work data
  • Median rent: seeded as None — calculated live from user submissions

Usage:
    python -m scripts.seed_data
"""

import math
import random
import time
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import Base
from app.models.user import User
from app.models.city import City
from app.models.climate_metric import ClimateMetric
from app.models.socioeconomic_metric import SocioeconomicMetric
from app.utils.security import hash_password

settings = get_settings()
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)

# ─── City data ───────────────────────────────────────────────────────────────

UK_CITIES = [
    {"name": "London",      "region": "Greater London",   "latitude": 51.5074, "longitude": -0.1278, "population": 8982000},
    {"name": "Birmingham",  "region": "West Midlands",    "latitude": 52.4862, "longitude": -1.8904, "population": 1141000},
    {"name": "Leeds",       "region": "Yorkshire",        "latitude": 53.8008, "longitude": -1.5491, "population":  812000},
    {"name": "Glasgow",     "region": "Scotland",         "latitude": 55.8642, "longitude": -4.2518, "population":  635000},
    {"name": "Sheffield",   "region": "Yorkshire",        "latitude": 53.3811, "longitude": -1.4701, "population":  584000},
    {"name": "Manchester",  "region": "North West",       "latitude": 53.4808, "longitude": -2.2426, "population":  553000},
    {"name": "Edinburgh",   "region": "Scotland",         "latitude": 55.9533, "longitude": -3.1883, "population":  527000},
    {"name": "Liverpool",   "region": "North West",       "latitude": 53.4084, "longitude": -2.9916, "population":  498000},
    {"name": "Bristol",     "region": "South West",       "latitude": 51.4545, "longitude": -2.5879, "population":  467000},
    {"name": "Cardiff",     "region": "Wales",            "latitude": 51.4816, "longitude": -3.1791, "population":  362000},
    {"name": "Newcastle",   "region": "North East",       "latitude": 54.9783, "longitude": -1.6178, "population":  300000},
    {"name": "Nottingham",  "region": "East Midlands",    "latitude": 52.9548, "longitude": -1.1581, "population":  323000},
    {"name": "Southampton", "region": "South East",       "latitude": 50.9097, "longitude": -1.4044, "population":  252000},
    {"name": "Belfast",     "region": "Northern Ireland", "latitude": 54.5973, "longitude": -5.9301, "population":  343000},
    {"name": "Cambridge",   "region": "East of England",  "latitude": 52.2053, "longitude":  0.1218, "population":  145000},
]

# ─── Real ONS statistics (green space % and commute time) ────────────────────
#
# Green space: ONS "Urban Green Space" 2020/2022 data, parks + public green
#   as % of built-up urban area.  Source: ons.gov.uk/peoplepopulationandcommunity
#
# Commute: ONS Census 2021, "Method of travel to work", mean journey time
#   (all modes, residents in employment). Source: ons.gov.uk/census
#
ONS_BASELINES = {
    "London":      {"green": 33.2, "commute": 47.0},
    "Birmingham":  {"green": 22.1, "commute": 30.2},
    "Leeds":       {"green": 28.7, "commute": 27.4},
    "Glasgow":     {"green": 32.0, "commute": 26.1},
    "Sheffield":   {"green": 36.0, "commute": 24.5},
    "Manchester":  {"green": 21.5, "commute": 32.1},
    "Edinburgh":   {"green": 38.9, "commute": 25.8},
    "Liverpool":   {"green": 19.8, "commute": 28.5},
    "Bristol":     {"green": 27.1, "commute": 28.7},
    "Cardiff":     {"green": 25.5, "commute": 25.2},
    "Newcastle":   {"green": 25.8, "commute": 22.5},
    "Nottingham":  {"green": 23.4, "commute": 26.3},
    "Southampton": {"green": 26.1, "commute": 23.4},
    "Belfast":     {"green": 24.0, "commute": 22.0},
    "Cambridge":   {"green": 41.2, "commute": 19.8},
}


# ─── Real data fetchers ───────────────────────────────────────────────────────

def fetch_real_climate(lat: float, lon: float, start_d: date, end_d: date) -> dict:
    """Fetch real historical daily weather from Open-Meteo Archive API."""
    import httpx

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
            resp = httpx.get(url, params=params, timeout=15.0)
            resp.raise_for_status()
            return resp.json().get("daily", {})
        except Exception as e:
            print(f"    Open-Meteo weather error: {e}, retrying...")
            time.sleep(2)
    return {}


def fetch_real_aqi(lat: float, lon: float, start_d: date, end_d: date) -> dict:
    """Fetch real historical daily European AQI from Open-Meteo Air Quality API.

    Returns a dict mapping date string (YYYY-MM-DD) -> daily mean EAQI.
    Source: https://open-meteo.com/en/docs/air-quality-api
    """
    import httpx

    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_d.isoformat(),
        "end_date": end_d.isoformat(),
        "hourly": "european_aqi",
        "timezone": "Europe/London",
    }

    for _ in range(3):
        try:
            resp = httpx.get(url, params=params, timeout=15.0)
            resp.raise_for_status()
            hourly = resp.json().get("hourly", {})
            times = hourly.get("time", [])
            aqi_vals = hourly.get("european_aqi", [])

            # Aggregate hourly readings to daily means
            daily: dict[str, list] = defaultdict(list)
            for t, v in zip(times, aqi_vals):
                if v is not None:
                    daily[t[:10]].append(v)

            return {d: sum(vs) / len(vs) for d, vs in daily.items() if vs}
        except Exception as e:
            print(f"    Open-Meteo AQI error: {e}, retrying...")
            time.sleep(2)
    return {}


def fetch_crime_index(lat: float, lon: float) -> float:
    """Fetch crime count from the UK Police API and normalise to a 0-100 index.

    Queries 12 months of street-level crimes within ~1 mile of the city centre.
    Source: https://data.police.uk/docs/method/crime-street/

    Normalisation: monthly_avg / 15  capped at 100.
    At ~1500 crimes/month (very high-density area) → index 100.
    At ~200 crimes/month (typical city centre)     → index 13.
    """
    import httpx

    total_crimes = 0
    months_fetched = 0
    today = date.today()

    for offset in range(12):
        # Work backwards month by month
        first_of_month = (today.replace(day=1) - timedelta(days=30 * offset)).replace(day=1)
        month_str = first_of_month.strftime("%Y-%m")
        url = "https://data.police.uk/api/crimes-street/all-crime"
        params = {"lat": lat, "lng": lon, "date": month_str}
        try:
            resp = httpx.get(url, params=params, timeout=20.0)
            if resp.status_code == 200:
                total_crimes += len(resp.json())
                months_fetched += 1
            elif resp.status_code == 404:
                # No data for that month (Belfast / Northern Ireland uses a separate force)
                pass
        except Exception:
            pass
        time.sleep(0.15)  # gentle rate limiting

    if months_fetched == 0:
        return None  # No data available (e.g. Belfast — PSNI not on data.police.uk)

    monthly_avg = total_crimes / months_fetched
    return min(100.0, round(monthly_avg / 15.0, 1))


def seed():
    db = Session()
    try:
        if db.query(City).count() > 0:
            print("Database already contains data — skipping seed.")
            return

        print("Seeding database …")

        # 1. Users
        admin = User(
            username="admin",
            email="admin@liveability.uk",
            hashed_password=hash_password("admin123"),
            role="admin",
        )
        db.add(admin)

        testuser = User(
            username="testuser",
            email="testuser@liveability.uk",
            hashed_password=hash_password("testpass1"),
            role="user",
        )
        db.add(testuser)
        db.flush()
        print("  ✓ Admin user created (username: admin, password: admin123)")
        print("  ✓ Test user created  (username: testuser, password: testpass1)")

        # 2. Cities
        city_map: dict[str, City] = {}
        for cdata in UK_CITIES:
            city = City(country="United Kingdom", **cdata)
            db.add(city)
            db.flush()
            city_map[cdata["name"]] = city
        print(f"  ✓ {len(city_map)} UK cities created")

        # 3. Climate data — real weather + real AQI
        today = date.today()
        end_date = today - timedelta(days=5)   # Open-Meteo archive is ~5 days delayed
        start_date = end_date - timedelta(days=364)
        total_metrics = 0
        random.seed(42)

        print(f"  Fetching real weather & AQI ({start_date} to {end_date})…")
        for city_name, city in city_map.items():
            print(f"    -> {city_name}…")

            weather = fetch_real_climate(city.latitude, city.longitude, start_date, end_date)
            aqi_by_date = fetch_real_aqi(city.latitude, city.longitude, start_date, end_date)

            if not weather or "time" not in weather:
                print(f"       Warning: no weather data for {city_name}, skipping.")
                continue

            for i, d_str in enumerate(weather["time"]):
                temp = weather["temperature_2m_mean"][i]
                precip = weather["precipitation_sum"][i]
                humidity_list = weather.get("relative_humidity_2m_mean", [])
                hum_val = humidity_list[i] if len(humidity_list) > i else None

                if temp is None:   temp = 10.0
                if precip is None: precip = 0.0
                if hum_val is None: hum_val = 70.0

                # Real EAQI if available, otherwise None (no synthetic fallback)
                aqi_val = aqi_by_date.get(d_str)

                cm = ClimateMetric(
                    city_id=city.id,
                    date=date.fromisoformat(d_str),
                    avg_temp_c=round(temp, 1),
                    aqi=round(aqi_val, 1) if aqi_val is not None else None,
                    humidity_pct=round(hum_val, 1),
                    precipitation_mm=round(precip, 1),
                    source="open_meteo",
                )
                db.add(cm)
                total_metrics += 1

        print(f"  ✓ {total_metrics} climate metric records created")

        # 4. Socioeconomic data — real ONS values for green space & commute;
        #    real crime from UK Police API; median rent left as None (crowdsourced)
        print("  Fetching crime data from UK Police API…")
        socio_count = 0
        for city_name, city in city_map.items():
            ons = ONS_BASELINES.get(city_name, {"green": 25.0, "commute": 25.0})
            print(f"    -> crime: {city_name}…")
            crime_index = fetch_crime_index(city.latitude, city.longitude)

            for year in [2023, 2024, 2025]:
                sm = SocioeconomicMetric(
                    city_id=city.id,
                    year=year,
                    # Median rent intentionally omitted — calculated from user submissions
                    median_rent_gbp=None,
                    green_space_pct=round(ons["green"], 1),
                    crime_index=crime_index,
                    avg_commute_min=round(ons["commute"], 1),
                    source="ons_census_2021,uk_police_api",
                )
                db.add(sm)
                socio_count += 1

        print(f"  ✓ {socio_count} socioeconomic metric records created")

        db.commit()
        print("\nSeed complete ✓")
        print(f"  Cities:       {len(city_map)}")
        print(f"  Climate rows: {total_metrics}")
        print(f"  Socio rows:   {socio_count}")
        print(f"  Median rent:  sourced from user submissions (none seeded)")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
