# City Liveability & Urban Climate Insights API

A data-driven RESTful API that aggregates urban climate, air quality, and socioeconomic data for UK cities. Computes composite liveability scores, detects climate anomalies, and generates city narrative summaries. Also ships a **Model Context Protocol (MCP)** server so LLM agents can interact with the data conversationally.

> **Module:** COMP — Web Services and Web Data, University of Leeds  
> **Author:** Luke Price  
> **Submission date:** 20 March 2026

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [API Endpoints](#api-endpoints)
6. [Authentication](#authentication)
7. [MCP Server](#mcp-server)
8. [Database Migrations](#database-migrations)
9. [Docker Deployment](#docker-deployment)
10. [Testing](#testing)
11. [Configuration](#configuration)
12. [API Documentation](#api-documentation)
13. [Deliverables](#deliverables)

---

## Features

| Category | Highlights |
|---|---|
| **CRUD** | Full Create / Read / Update / Delete for cities, observations, climate metrics, and socioeconomic metrics |
| **Liveability Scoring** | Composite 0–100 score derived from climate comfort, affordability, safety, and green-space sub-scores |
| **City Comparison** | Side-by-side liveability comparison for multiple cities |
| **Trend Analysis** | Time-series trends for AQI, temperature, humidity, precipitation |
| **Anomaly Detection** | Z-score based outlier detection on climate readings |
| **Narrative Generation** | Template-based liveability narrative summaries per city |
| **MCP Server** | Model Context Protocol tools and resources for LLM agents — accessible locally (stdio) or remotely (SSE) |
| **Auth & RBAC** | JWT-based authentication with user / admin roles |
| **Rate Limiting** | 100 requests / minute per IP via slowapi |
| **Request Logging** | Structured logging middleware with latency tracking |

---

## Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Framework | **FastAPI** 0.115 | Async, auto-generated OpenAPI docs, Pydantic-native |
| ORM | **SQLAlchemy** 2.0 | Mature, supports multiple DB backends |
| Database | **SQLite** (dev/test) / **PostgreSQL** (prod) | Zero-config locally, scales for deployment |
| Auth | **python-jose** + **bcrypt** | Stateless JWT tokens, industry-standard hashing |
| Validation | **Pydantic** v2 | Compile-time schema validation, high performance |
| Weather | **Open-Meteo** Archive API | Free historical weather data (no auth required) |
| MCP | **mcp** SDK (FastMCP) | Exposes API tools to LLM agents |
| Rate Limiting | **slowapi** | Leaky-bucket algorithm built on limits |
| Testing | **pytest** + **httpx** | Fast, fixture-driven, async support |

---

## Project Structure

```
webservices01/
├── app/
│   ├── config.py              # Pydantic-settings configuration
│   ├── database.py            # SQLAlchemy engine & session
│   ├── dependencies.py        # Auth dependency injection (JWT, RBAC)
│   ├── exceptions.py          # Custom exceptions & global handlers
│   ├── main.py                # FastAPI app factory
│   ├── middleware/
│   │   ├── logging_mw.py      # Request logging middleware
│   │   └── rate_limit.py      # Rate limiting (slowapi)
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── city.py
│   │   ├── climate_metric.py
│   │   ├── socioeconomic_metric.py
│   │   ├── liveability_score.py
│   │   └── observation.py
│   ├── routers/               # API endpoint handlers
│   │   ├── auth.py            # Register, login, profile
│   │   ├── cities.py          # City CRUD
│   │   ├── metrics.py         # Climate & socioeconomic CRUD
│   │   ├── observations.py    # User-reported observations
│   │   ├── analytics.py       # Liveability, comparison, trends, anomalies
│   │   └── query.py           # NL-to-SQL query, narrative
│   ├── schemas/               # Pydantic request/response models
│   ├── services/              # Business logic layer
│   │   ├── auth_service.py
│   │   ├── city_service.py
│   │   ├── metric_service.py
│   │   ├── observation_service.py
│   │   ├── analytics_service.py
│   │   ├── narrative_service.py
│   │   └── weather_service.py
│   └── utils/
│       ├── scoring.py         # Liveability scoring algorithm
│       ├── security.py        # Password hashing, JWT
│       └── sql_validator.py   # SQL sandboxing for NL queries
├── mcp_server/
│   └── server.py              # MCP server (tools, resources, prompts)
├── alembic/                   # Database migration scripts
│   ├── env.py
│   └── versions/
├── scripts/
│   ├── seed_data.py           # Database seeding with UK city data
│   └── export_openapi.py      # Export OpenAPI spec & API docs
├── docs/
│   ├── openapi.json           # Exported OpenAPI specification
│   ├── api_documentation.md   # Generated API documentation
│   └── technical_report.md    # Technical report
├── tests/                     # Comprehensive test suite (228 tests)
├── Dockerfile                 # Container deployment
├── docker-compose.yml         # Multi-service orchestration
├── alembic.ini                # Migration configuration
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### 1. Clone and set up

```bash
git clone https://github.com/LukeIP/webservices01
cd webservices01
python -m venv venv
source venv/bin/activate for macOS/linux   # macOS/Linux
venv\Scripts\activate for windows     # Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY
```

### 3. Seed the database

```bash
python -m scripts.seed_data
```

This creates 15 UK cities with 365 days of climate data and 3 years of socioeconomic data.

### 4. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now available at **http://localhost:8000**

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register` | Register a new user | No |
| POST | `/api/v1/auth/login` | Login, receive JWT token | No |
| GET | `/api/v1/auth/me` | Get current user profile | Bearer |
| POST | `/api/v1/auth/refresh` | Refresh JWT token | Bearer |

### Cities

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/cities/` | List cities (paginated, filterable, sortable) | No |
| POST | `/api/v1/cities/` | Create a city | Bearer |
| GET | `/api/v1/cities/{id}` | Get city details | No |
| PUT | `/api/v1/cities/{id}` | Update a city | Bearer |
| DELETE | `/api/v1/cities/{id}` | Delete a city | Admin |

### Climate Metrics

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/cities/{id}/climate-metrics` | List climate data (date-filterable) | No |
| POST | `/api/v1/cities/{id}/climate-metrics` | Add climate reading | Bearer |
| GET | `/api/v1/climate-metrics/{id}` | Get single reading | No |
| DELETE | `/api/v1/climate-metrics/{id}` | Delete reading | Admin |

### Socioeconomic Metrics

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/cities/{id}/socioeconomic-metrics` | List socioeconomic data | No |
| POST | `/api/v1/cities/{id}/socioeconomic-metrics` | Add socioeconomic data | Bearer |
| GET | `/api/v1/socioeconomic-metrics/{id}` | Get single record | No |
| DELETE | `/api/v1/socioeconomic-metrics/{id}` | Delete record | Admin |

### Observations

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/cities/{id}/observations` | List observations for a city | No |
| POST | `/api/v1/cities/{id}/observations` | Add user observation | Bearer |
| PUT | `/api/v1/observations/{id}` | Update own observation | Bearer |
| DELETE | `/api/v1/observations/{id}` | Delete own observation | Bearer |

### Analytics

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/cities/{id}/liveability` | Compute liveability score | No |
| GET | `/api/v1/cities/compare?ids=1,2,3` | Compare cities | No |
| GET | `/api/v1/cities/{id}/trends` | Metric trend data | No |
| GET | `/api/v1/cities/{id}/anomalies` | Detect anomalies | No |
| GET | `/api/v1/cities/{id}/narrative` | AI-generated narrative | No |

### Narrative

---

## Authentication

1. **Register:** `POST /api/v1/auth/register` with `username`, `email`, `password`
2. **Login:** `POST /api/v1/auth/login` with `username`, `password` → returns `access_token`
3. **Use token:** Include `Authorization: Bearer <token>` header on authenticated routes

### Example

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "securepass123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "securepass123"}'

# Use token
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

---

## MCP Server

The project includes a **Model Context Protocol** server that allows LLM agents to interact with the API through tool calls.

### Tools Available

| Tool | Description |
|------|-------------|
| `search_cities` | Search/filter cities by region |
| `get_city_details` | Get city info by ID |
| `add_city` | Create a new city |
| `compute_liveability` | Compute liveability score |
| `compare_cities` | Compare multiple cities |
| `get_climate_trends` | Time-series trend data |
| `detect_anomalies` | Z-score anomaly detection |
| `add_observation` | Record a user observation |
| `get_city_climate_data` | Recent climate readings |

### Running the MCP Server

```bash
# Stdio transport (for LLM integration)
python -m mcp_server.server

# MCP Inspector (development)
mcp dev mcp_server/server.py
```

### Claude Desktop Configuration

The MCP server supports two transport modes:

**Option A — Local (stdio, for development)**

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "city-liveability": {
      "command": "C:path-to-venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_server.server"],
      "cwd": "C:path-to-project\\webservices01"
    }
  }
}
```

**Option B — Remote (SSE, for deployed Railway instance)**

Once deployed to Railway, the MCP server is co-hosted with the REST API at `/mcp`:

```json
{
  "mcpServers": {
    "city-liveability": {
      "url": "https://webservices01-production.up.railway.app//mcp/sse"
    }
  }
}
```

---

## Database Migrations

The project uses **Alembic** for database schema versioning:

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "Description of change"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

---

## Deployment

### Railway (recommended)

The project includes `Procfile`, `runtime.txt`, and `railway.json` for one-click Railway deployment.

1. Push this repository to GitHub
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub Repo**
3. In the Railway dashboard, set the following environment variables:
   | Variable | Value |
   |----------|-------|
   | `SECRET_KEY` | Any long random string |
4. Railway auto-detects the config, installs dependencies, seeds the database, and deploys
5. You get a public URL — both the REST API and MCP SSE endpoint are live

The MCP server is mounted at `/mcp` on the same service, so there is no separate deployment needed.

### Docker (local)

```bash
# Build and run with Docker Compose
docker compose up --build

# Or build and run just the API
docker build -t city-liveability-api .
docker run -p 8000:8000 city-liveability-api
```

---

## Testing

The project includes a comprehensive test suite with **228 tests** covering all functional and non-functional requirements.

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=app --cov-report=term-missing

# Run specific test module
python -m pytest tests/test_analytics.py -v
```

### Test Coverage Areas

- **Auth:** Registration, login, JWT validation, token expiry
- **Cities CRUD:** Create, read, list (pagination/filtering/sorting), update, delete
- **Metrics CRUD:** Climate and socioeconomic metric endpoints
- **Observations:** CRUD, ownership enforcement, admin override
- **Analytics:** Liveability scoring, city comparison, trends, anomalies, narrative
- **Narrative:** City narrative generation
- **Security:** Password hashing, JWT tokens, RBAC enforcement
- **Services:** Unit tests for all service classes
- **Utilities:** Scoring algorithm, SQL validator
- **General:** Health check, CORS, OpenAPI docs, error handling
- **Middleware:** Rate limiting, request logging

---

## Configuration

Configuration is managed via environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./city_liveability.db` | Database connection string |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | JWT signing key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiry |
| `ENVIRONMENT` | `development` | Environment name |

---

## API Documentation

Interactive API documentation is auto-generated by FastAPI:

- **Swagger UI** — `/docs`
- **ReDoc** — `/redoc`
- **OpenAPI JSON** — `/openapi.json`

### Generating API Documentation PDF

```bash
# Generate OpenAPI JSON + Markdown documentation
python scripts/export_openapi.py

# Convert to PDF (requires pandoc)
pandoc docs/api_documentation.md -o docs/api_documentation.pdf
```

The generated documentation is also available in the `docs/` directory.

---

## Deliverables

| Deliverable | Location |
|-------------|----------|
| Source code | This repository |
| README.md | [README.md](README.md) |
| API documentation (PDF) | [docs/api_documentation.pdf](docs/api_documentation.pdf) |
| OpenAPI specification | [docs/openapi.json](docs/openapi.json) |
| Technical report (PDF) | [docs/technical_report.pdf](docs/technical_report.pdf) |
| Presentation slides | [Google Slides](https://docs.google.com/presentation/d/1X7gR_xAH7RzQZcBK50WckjgdNCETrfwiicAUH3EYhUI/edit?usp=sharing) |
| Swagger UI | `/docs` (when server is running) |
| Test suite | [tests/](tests/) — 228 tests |

---

## License

This project was developed for academic coursework at the University of Leeds.
