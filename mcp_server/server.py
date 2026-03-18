"""
Model Context Protocol (MCP) Server for City Liveability API.

Exposes the core API functionality as MCP tools so that LLM agents
(e.g. Claude, GitHub Copilot) can query city data, compute liveability
scores, detect anomalies, and add observations conversationally.

Run with:
    python -m mcp_server.server          (stdio transport)
    mcp dev mcp_server/server.py         (MCP Inspector)
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so that `app.*` imports work
# regardless of how this file is launched (e.g. via `mcp dev`).
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import Base
from app.services.city_service import CityService
from app.services.analytics_service import AnalyticsService
from app.services.metric_service import MetricService
from app.services.observation_service import ObservationService
from app.models.user import User
from app.schemas.city import CityCreate
from app.schemas.observation import ObservationCreate

settings = get_settings()

# Database setup (separate engine for MCP process)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Initialize MCP server
mcp = FastMCP(
    "City Liveability API",
    instructions=(
        "MCP server for the City Liveability & Urban Climate Insights API. "
        "Query UK city data, compute liveability scores, detect anomalies, "
        "and explore urban climate trends."
    ),
)


def _get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


# ─── Resources ───────────────────────────────────────────────────────────────


@mcp.resource("cities://list")
def list_all_cities() -> str:
    """List all cities in the database with their basic info."""
    db = _get_db()
    try:
        service = CityService(db)
        cities, total = service.list_cities(limit=200)
        lines = [f"Total cities: {total}\n"]
        for c in cities:
            lines.append(
                f"- {c.name} (ID: {c.id}, Region: {c.region}, Pop: {c.population or 'N/A'})"
            )
        return "\n".join(lines)
    finally:
        db.close()


@mcp.resource("cities://{city_id}/summary")
def city_summary(city_id: int) -> str:
    """Get a detailed summary of a specific city."""
    db = _get_db()
    try:
        service = CityService(db)
        city = service.get_by_id(city_id)
        return (
            f"City: {city.name}\n"
            f"Region: {city.region}\n"
            f"Country: {city.country}\n"
            f"Coordinates: ({city.latitude}, {city.longitude})\n"
            f"Population: {city.population or 'N/A'}\n"
            f"Created: {city.created_at}"
        )
    finally:
        db.close()


# ─── Tools ───────────────────────────────────────────────────────────────────


@mcp.tool()
def search_cities(region: str | None = None, limit: int = 20) -> str:
    """Search for cities, optionally filtering by region.

    Args:
        region: Filter by region name (e.g. 'Yorkshire', 'Greater London')
        limit: Maximum number of results (default 20)
    """
    db = _get_db()
    try:
        service = CityService(db)
        cities, total = service.list_cities(region=region, limit=limit)
        if not cities:
            return "No cities found matching your criteria."
        lines = [f"Found {total} cities:"]
        for c in cities:
            lines.append(f"  • {c.name} (ID: {c.id}) — {c.region}, pop: {c.population or 'N/A'}")
        return "\n".join(lines)
    finally:
        db.close()


@mcp.tool()
def get_city_details(city_id: int) -> str:
    """Get detailed information about a specific city.

    Args:
        city_id: The numeric ID of the city
    """
    db = _get_db()
    try:
        service = CityService(db)
        city = service.get_by_id(city_id)
        return (
            f"City: {city.name}\n"
            f"Region: {city.region}\n"
            f"Country: {city.country}\n"
            f"Location: ({city.latitude:.4f}, {city.longitude:.4f})\n"
            f"Population: {city.population or 'Unknown'}"
        )
    finally:
        db.close()


@mcp.tool()
def add_city(
    name: str,
    region: str,
    latitude: float,
    longitude: float,
    country: str = "United Kingdom",
    population: int | None = None,
) -> str:
    """Add a new city to the database.

    Args:
        name: City name
        region: Region/county (e.g. 'Yorkshire', 'Greater London')
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        country: Country name (default: United Kingdom)
        population: City population (optional)
    """
    db = _get_db()
    try:
        service = CityService(db)
        data = CityCreate(
            name=name,
            region=region,
            latitude=latitude,
            longitude=longitude,
            country=country,
            population=population,
        )
        city = service.create(data)
        return f"Created city '{city.name}' with ID {city.id}."
    finally:
        db.close()


@mcp.tool()
def compute_liveability(city_id: int) -> str:
    """Compute the liveability score for a city based on its climate and socioeconomic data.

    Returns an overall score (0-100) plus sub-scores for climate,
    affordability, safety, and environment.

    Args:
        city_id: The numeric ID of the city
    """
    db = _get_db()
    try:
        service = AnalyticsService(db)
        result = service.compute_liveability_for_city(city_id)
        return (
            f"Liveability for {result['city_name']}:\n"
            f"  Overall:       {result['overall_score']:.1f}/100\n"
            f"  Climate:       {result['climate_score']:.1f}/100\n"
            f"  Affordability: {result['affordability_score']:.1f}/100\n"
            f"  Safety:        {result['safety_score']:.1f}/100\n"
            f"  Environment:   {result['environment_score']:.1f}/100"
        )
    finally:
        db.close()


@mcp.tool()
def compare_cities(city_ids: list[int]) -> str:
    """Compare liveability scores across multiple cities.

    Args:
        city_ids: List of city IDs to compare
    """
    db = _get_db()
    try:
        service = AnalyticsService(db)
        results = service.compare_cities(city_ids)
        if not results:
            return "No valid cities found for the given IDs."
        lines = ["City Liveability Comparison:\n"]
        # Sort by overall score descending
        results.sort(key=lambda r: r["overall_score"], reverse=True)
        for i, r in enumerate(results, 1):
            lines.append(
                f"  {i}. {r['city_name']}: {r['overall_score']:.1f}/100 "
                f"(Climate: {r['climate_score']:.1f}, "
                f"Afford: {r['affordability_score']:.1f}, "
                f"Safety: {r['safety_score']:.1f}, "
                f"Env: {r['environment_score']:.1f})"
            )
        return "\n".join(lines)
    finally:
        db.close()


@mcp.tool()
def get_climate_trends(city_id: int, metric: str = "aqi", period: str = "12m") -> str:
    """Get time-series trend data for a climate metric.

    Args:
        city_id: The numeric ID of the city
        metric: The metric to trend — one of 'aqi', 'temp', 'humidity', 'precipitation'
        period: Time period e.g. '3m', '6m', '12m', '24m'
    """
    db = _get_db()
    try:
        service = AnalyticsService(db)
        result = service.get_trends(city_id, metric=metric, period=period)
        pts = result["data_points"]
        if not pts:
            return f"No {metric} data available for city {city_id} in the last {period}."
        lines = [f"{metric.upper()} trend for city {city_id} ({period}): {len(pts)} data points"]
        # Show first 5 and last 5 if there are many
        show = pts[:5] + (["..."] if len(pts) > 10 else []) + pts[-5:] if len(pts) > 10 else pts
        for pt in show:
            if isinstance(pt, str):
                lines.append(f"  {pt}")
            else:
                lines.append(f"  {pt['date']}: {pt['value']:.2f}")
        return "\n".join(lines)
    finally:
        db.close()


@mcp.tool()
def detect_anomalies(city_id: int, threshold: float = 2.0) -> str:
    """Detect anomalous climate readings using z-score analysis.

    Args:
        city_id: The numeric ID of the city
        threshold: Z-score threshold (default 2.0; higher = fewer anomalies)
    """
    db = _get_db()
    try:
        service = AnalyticsService(db)
        result = service.detect_anomalies(city_id, threshold=threshold)
        anomalies = result["anomalies"]
        if not anomalies:
            return f"No anomalies detected for city {city_id} at threshold {threshold}."
        lines = [f"Found {len(anomalies)} anomalies (threshold: {threshold}):"]
        for a in anomalies:
            lines.append(
                f"  {a['date']} — {a['metric']}: {a['value']:.1f} (z-score: {a['z_score']:.2f})"
            )
        return "\n".join(lines)
    finally:
        db.close()


@mcp.tool()
def add_observation(
    city_id: int,
    category: str,
    value: float,
    note: str | None = None,
) -> str:
    """Add a user observation for a city.

    Args:
        city_id: The numeric ID of the city
        category: Observation category — one of 'air_quality', 'noise', 'safety',
                  'cleanliness', 'green_space', 'transport', 'general'
        value: Score from 0-100
        note: Optional descriptive note
    """
    db = _get_db()
    try:
        # Get or create a system user for MCP observations
        system_user = db.query(User).filter(User.username == "mcp_agent").first()
        if not system_user:
            from app.utils.security import hash_password
            system_user = User(
                username="mcp_agent",
                email="mcp@system.local",
                hashed_password=hash_password("mcp-system-user"),
                role="user",
            )
            db.add(system_user)
            db.commit()
            db.refresh(system_user)

        service = ObservationService(db)
        data = ObservationCreate(category=category, value=value, note=note)
        obs = service.create(city_id, system_user, data)
        return f"Observation recorded (ID: {obs.id}) — {category}: {value}/100 for city {city_id}."
    finally:
        db.close()


@mcp.tool()
def get_city_climate_data(city_id: int, limit: int = 30) -> str:
    """Get recent climate metric readings for a city.

    Args:
        city_id: The numeric ID of the city
        limit: Maximum number of readings to return (default 30)
    """
    db = _get_db()
    try:
        service = MetricService(db)
        items, total = service.list_climate_metrics(city_id, limit=limit)
        if not items:
            return f"No climate data available for city {city_id}."
        lines = [f"Climate data for city {city_id} ({total} total, showing {len(items)}):"]
        for m in items:
            lines.append(
                f"  {m.date} — Temp: {m.avg_temp_c}°C, AQI: {m.aqi}, "
                f"Humidity: {m.humidity_pct}%, Precip: {m.precipitation_mm}mm"
            )
        return "\n".join(lines)
    finally:
        db.close()


# ─── Prompts ─────────────────────────────────────────────────────────────────


@mcp.prompt()
def city_analysis_prompt(city_name: str) -> str:
    """Generate a prompt for analysing a city's liveability.

    Args:
        city_name: The name of the city to analyse
    """
    return (
        f"Please analyse the liveability of {city_name} using the available tools.\n\n"
        "1. First, search for the city to get its ID.\n"
        "2. Compute its liveability score.\n"
        "3. Check for any anomalies in its climate data.\n"
        "4. Look at recent AQI and temperature trends.\n"
        "5. Provide a comprehensive summary of the city's liveability, "
        "highlighting strengths and areas for improvement."
    )


@mcp.prompt()
def compare_cities_prompt(city_names: str) -> str:
    """Generate a prompt for comparing multiple cities.

    Args:
        city_names: Comma-separated list of city names to compare
    """
    return (
        f"Please compare the liveability of these cities: {city_names}.\n\n"
        "1. Search for each city to get their IDs.\n"
        "2. Use the compare_cities tool with all found IDs.\n"
        "3. For each city, also check their recent AQI trends.\n"
        "4. Provide a ranked comparison with pros and cons for each city."
    )


# ─── Entry point ─────────────────────────────────────────────────────────────


if __name__ == "__main__":
    mcp.run()
