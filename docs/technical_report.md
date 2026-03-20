# Technical Report: City Liveability & Urban Climate Insights API

**Module:** COMP — Web Services and Web Data, University of Leeds
**Author:** Luke Price
**Date:** 20 March 2026
**Repository:** [GitHub](https://github.com/lukeprice/webservices01)

---

## 1. Introduction

This report documents the design, implementation, and evaluation of the City Liveability & Urban Climate Insights API — a data-driven RESTful web service that aggregates urban climate, air quality, and socioeconomic data for UK cities. The system computes composite liveability scores, detects statistical climate anomalies, and delivers city narrative summaries through a structured API. Crucially, it also exposes a Model Context Protocol (MCP) server so that LLM agents such as Claude can interact with the data conversationally via tool calls — a feature that extends the project beyond conventional web API design into the emerging space of AI-accessible data services.

The project was chosen because it sits at the intersection of two personally relevant domains: environmental data and practical AI integration. The open-ended nature of the brief allowed me to build something that demonstrates not just functional CRUD mechanics, but a coherent system with a meaningful analytical purpose.

---

## 2. Technology Stack Justification

### 2.1 Framework — FastAPI

FastAPI was chosen over Django REST Framework and Flask for three principal reasons. First, it is natively asynchronous, which matters when performing I/O-bound operations such as fetching weather data from an external API during city creation. Second, it generates interactive OpenAPI documentation (Swagger UI and ReDoc) automatically from Python type annotations, eliminating the need to maintain a separate documentation layer. Third, FastAPI's tight coupling with Pydantic v2 provides compile-time schema validation and serialisation at substantially higher throughput than equivalent Django approaches, which is relevant when stress-testing with the 100 requests-per-minute rate limit.

Django was explicitly evaluated and ruled out: its ORM and request–response cycle carry more overhead than is needed for a pure API service, and its synchronous-by-default model would have required additional configuration to support async database access.

### 2.2 ORM — SQLAlchemy 2.0

SQLAlchemy 2.0 was selected as the ORM layer for its support of multiple database backends and its mature, well-documented query interface. The decision to separate the ORM from the web framework (rather than using Django's built-in ORM) allows the same model definitions to target both the SQLite development database and a PostgreSQL production instance without any code changes — only the `DATABASE_URL` environment variable differs.

### 2.3 Database — SQLite (development) / PostgreSQL (production)

SQLite is used locally because it requires zero configuration and produces a single portable file, accelerating development iteration. The production configuration targets PostgreSQL, hosted via Railway, because it handles concurrent connections safely and provides the full type system required for production data integrity. Alembic is used for schema versioning, ensuring that migrations are tracked in version control and can be applied or rolled back deterministically.

A NoSQL database such as MongoDB was considered for the climate metrics collection, given that time-series readings have a naturally document-like structure. However, SQLite and PostgreSQL were preferred because the relational model allows efficient JOIN queries between cities, climate metrics, and socioeconomic data — which is precisely what the analytics endpoints require — without denormalising data or duplicating city identifiers across nested documents.

### 2.4 Authentication — JWT with RBAC

Stateless JWT tokens were chosen over session-based authentication because the API is designed to be consumed by both human clients and LLM agents, neither of which benefits from server-side session storage. The `python-jose` library handles token signing with HMAC-SHA256 (HS256), and `bcrypt` is used for password hashing with an appropriate cost factor. Role-based access control (RBAC) distinguishes between `user` and `admin` roles: administrative operations such as deleting cities or climate readings are protected by an admin-only dependency injected at the router level, keeping the authorisation logic centralised rather than duplicated per endpoint.

### 2.5 External Data — Open-Meteo Archive API

Open-Meteo was chosen as the weather data source because it is free, requires no API key, and provides historical daily climate variables (temperature, precipitation, humidity) through a clean REST interface. When a city is created or updated, a background thread fetches the previous 365 days of climate data and stores it as climate metric rows, automatically skipping dates that are already present to avoid duplication. This approach seeds the database with meaningful real-world data without requiring a separate ETL pipeline.

### 2.6 MCP Server

The Model Context Protocol server was implemented using Anthropic's `fastmcp` SDK. It exposes nine tools covering city search, liveability computation, anomaly detection, trend retrieval, and observation recording. The MCP server is mounted on the same FastAPI process at `/mcp/sse`, meaning no separate deployment is required. This design enables a Claude Desktop instance to connect to the deployed Railway URL and interact with UK city data conversationally — for example, asking which city has the best air quality trend over the past six months and receiving a computed, data-backed answer.

---

## 3. Architecture and Design Decisions

The application follows a layered architecture with clear separation of concerns:

- **Routers** handle HTTP routing and request/response serialisation.
- **Services** contain all business logic and are the only layer that touches the ORM session.
- **Models** define the database schema using SQLAlchemy declarative syntax.
- **Schemas** define Pydantic models for request validation and response serialisation.
- **Utils** contain pure functions — the scoring algorithm, security helpers, and the SQL sandbox validator — with no database dependencies, making them straightforward to unit-test in isolation.

This separation means that routers are thin and testable without a live database (by injecting a mock service), while services can be unit-tested by passing an in-memory SQLite session.

### 3.1 Liveability Scoring

The composite liveability score is computed from four sub-dimensions: climate comfort (25%), affordability (30%), safety (25%), and environment (20%). Each raw metric is normalised to a 0–100 scale using domain-specific functions. For example, temperature comfort is scored by measuring deviation from an ideal UK temperature of 17.5°C, penalising both extreme heat and cold. AQI is inverted — a lower index produces a higher score. Rent and crime index are normalised relative to empirical UK maxima. The weighted sum produces an overall score that is interpretable and comparable across cities.

### 3.2 Anomaly Detection

Z-score-based anomaly detection was implemented in the analytics service. For a given city and metric, the service computes the population mean and standard deviation across all stored readings, then identifies dates where the absolute z-score exceeds a configurable threshold (defaulting to 2.0). This approach is statistically sound for continuous climate variables and surfaces genuine outliers such as heatwave days or extreme precipitation events without requiring any external ML library.

### 3.3 Router Ordering

A non-obvious design constraint arose from FastAPI's path matching rules. The `GET /api/v1/cities/compare` endpoint must be registered before `GET /api/v1/cities/{city_id}`, because FastAPI matches routes in registration order and `compare` would otherwise be interpreted as a `city_id` parameter. This is documented explicitly in the application factory (`main.py`) as a comment to prevent future developers from accidentally reordering the router includes.

---

## 4. Testing Approach

The project includes 228 tests organised into modules that mirror the application structure. Tests are written using `pytest` with `httpx` as the test client, which supports FastAPI's async interface natively.

The test strategy covers several layers:

- **Integration tests** exercise full request–response cycles against an in-memory SQLite database, seeded with known fixtures. These tests verify that CRUD endpoints return correct status codes, response shapes, and pagination envelopes.
- **Unit tests** for services pass a real but temporary SQLite session to verify business logic without the HTTP layer.
- **Security tests** verify that protected routes reject unauthenticated requests with 401, that RBAC enforcement rejects non-admin users on admin-only endpoints with 403, and that JWTs with tampered signatures are rejected.
- **Utility tests** exercise the scoring algorithm and SQL validator with edge-case inputs.
- **Middleware tests** confirm that the rate limiter triggers at the configured threshold and that the logging middleware records latency fields.

A deliberate choice was made to use real SQLite sessions rather than mocked database calls in integration tests, having observed that mocked tests can mask schema-level bugs that only appear when the ORM generates actual SQL. This trades a small increase in test execution time for substantially higher confidence that the database interaction is correct.

---

## 5. Challenges and Lessons Learned

**Router ordering** was the most counterintuitive issue encountered during development. The FastAPI path-matching behaviour described above caused intermittent 422 validation errors on the comparison endpoint until the root cause was identified and the router registration order was fixed.

**Background seeding** required careful handling to avoid blocking application startup. The Open-Meteo fetch for 365 days of data across 15 cities produces several thousand HTTP requests, so the seed script was moved to a daemon thread that runs after the application is ready to accept requests. A `SKIP_SEED` environment variable was introduced to suppress this behaviour during testing, preventing tests from making real external HTTP calls.

**Alembic and SQLite** have a well-known incompatibility: SQLite does not support `ALTER COLUMN` operations, which means certain schema changes require table recreation rather than an in-place modification. This was managed by using a batch migration mode in the Alembic environment configuration, which transparently handles the recreation without requiring manual intervention.

---

## 6. Limitations and Future Development

The current implementation has several known limitations:

**Liveability weights are static.** The scoring algorithm uses fixed weights (climate 25%, affordability 30%, safety 25%, environment 20%). A future version could expose a `/liveability?weights=...` query parameter allowing callers to specify their own priority profile, or could learn user-specific weights from saved preferences.

**Narrative generation is template-based.** The city narrative endpoint currently fills a string template with numeric scores. Integrating a language model (via the Claude API) would produce genuinely readable, contextualised narratives that highlight relative strengths and weaknesses compared to peer cities.

**No time-based liveability history.** The analytics endpoints compute a snapshot score from the most recent data. Tracking how a city's liveability score evolves over time would enable trend endpoints showing whether cities are improving or declining, which would be valuable for policy analysis.

**Read replicas and caching.** Under production load, repeatedly computing liveability scores from raw climate data is unnecessarily expensive. A caching layer (Redis, or simple in-process `functools.lru_cache` with TTL) on the analytics service would reduce database load significantly.

**Frontend portal.** A basic HTML frontend is mounted at `/ui`, but it is static. A React or Vue frontend consuming the API would provide a more complete demonstration of the system's capabilities.

---

## 7. Conclusion

This project demonstrates a complete, production-quality RESTful API built with a modern Python stack. The choice of FastAPI, SQLAlchemy 2.0, and JWT authentication reflects considered trade-offs between development velocity, runtime performance, and maintainability. The addition of an MCP server goes beyond the basic requirements to position the API as an AI-accessible data service — a design pattern that is increasingly relevant as LLM agents become primary consumers of structured data. The 228-test suite provides confidence that the implementation is correct and that future changes can be validated without regression.

---

## 8. References

- FastAPI documentation — https://fastapi.tiangolo.com
- SQLAlchemy 2.0 documentation — https://docs.sqlalchemy.org/en/20/
- Open-Meteo Archive API — https://open-meteo.com/en/docs/historical-weather-api
- Anthropic Model Context Protocol SDK — https://github.com/anthropics/mcp
- python-jose — https://python-jose.readthedocs.io
- slowapi — https://slowapi.readthedocs.io
- Alembic documentation — https://alembic.sqlalchemy.org

---

## 9. Generative AI Declaration
Generative AI tools were used at multiple stages of this project. During the ideation phase, AI was used to brainstorm viable project concepts and investigate suitable open datasets for each. Once a direction was chosen, AI assisted in generating an initial code scaffold and boilerplate code — for example, producing model definitions directly from a database diagram — which was then validated against a manually written test suite. AI was also used to review test coverage and suggest additional cases, though debugging failures required manual intervention throughout. Finally, AI assisted in drafting and refining this technical report.
Overall, AI proved genuinely useful, particularly in accelerating low-level implementation tasks. This freed up time to focus on higher-level architectural decisions — such as the anomaly detection approach, and MCP integration — rather than spending time on arbitrary boilerplate syntax and conventions.

However, AI assistance had a notable drawback: generated code rarely incorporated proactive refactoring. As the codebase grew, this resulted in accumulating technical debt that required periodic manual intervention to restructure. Future use would benefit from explicitly prompting for refactoring suggestions alongside new code generation.