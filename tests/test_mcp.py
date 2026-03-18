"""Tests for the MCP server module.

Covers:
- FR-06: MCP integration — tools, resources, prompts are registered
- Tool functions return string results
"""

import os
import pytest

# Set env vars before importing MCP server (it imports app.config)
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")

from mcp_server.server import (  # noqa: E402
    mcp,
    search_cities,
    get_city_details,
    add_city,
    get_city_climate_data,
    list_all_cities,
    city_analysis_prompt,
    compare_cities_prompt,
)


class TestMCPRegistration:
    """Verify that the MCP server object is configured correctly."""

    def test_mcp_instance_exists(self):
        """FastMCP instance is created."""
        assert mcp is not None

    def test_mcp_has_name(self):
        """MCP server declares its name."""
        assert mcp.name == "City Liveability API"

    def test_tools_registered(self):
        """Key tools are importable (they were decorated with @mcp.tool)."""
        # If the decorators ran without error, the functions exist
        assert callable(search_cities)
        assert callable(get_city_details)
        assert callable(add_city)
        assert callable(get_city_climate_data)


class TestMCPToolFunctions:
    """
    Integration tests for MCP tool functions.
    These operate against the test database.
    """

    @pytest.fixture(autouse=True)
    def _setup_db(self, test_engine):
        """Ensure test DB tables exist and clean up MCP-committed data after each test."""
        yield
        # MCP tools commit directly to the DB file, bypassing the rollback isolation
        # used by the `db` fixture. Clean up to avoid polluting subsequent tests.
        from sqlalchemy import text
        with test_engine.connect() as conn:
            conn.execute(text("DELETE FROM cities"))
            conn.execute(text("DELETE FROM users"))
            conn.commit()

    def test_search_cities_empty(self):
        """search_cities returns a message when DB is empty."""
        result = search_cities()
        assert isinstance(result, str)
        assert "No cities" in result or "Found" in result

    def test_add_city_and_search(self):
        """add_city creates a city, then search_cities finds it."""
        result = add_city(
            name="TestCity", region="TestRegion", latitude=51.5, longitude=-0.1
        )
        assert "Created" in result
        assert "TestCity" in result

        found = search_cities(region="TestRegion")
        assert "TestCity" in found

    def test_list_all_cities_resource(self):
        """The cities://list resource returns a string."""
        result = list_all_cities()
        assert isinstance(result, str)
        assert "Total cities" in result

    def test_get_city_climate_data_no_data(self):
        """Climate data tool gracefully handles missing data."""
        # Add a city first
        add_city(name="EmptyClimate", region="Test", latitude=50.0, longitude=-1.0)
        result = get_city_climate_data(city_id=1, limit=10)
        assert isinstance(result, str)
        # Either says "No climate data" or returns data
        assert "climate" in result.lower()


class TestMCPPrompts:
    """Verify prompt templates return valid strings."""

    def test_city_analysis_prompt(self):
        result = city_analysis_prompt("Leeds")
        assert "Leeds" in result
        assert "liveability" in result.lower()

    def test_compare_cities_prompt(self):
        result = compare_cities_prompt("Leeds, Manchester, London")
        assert "Leeds" in result
        assert "Manchester" in result
        assert "compare" in result.lower()
