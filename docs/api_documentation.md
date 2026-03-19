# City Liveability & Urban Climate Insights API

**Version:** 1.0.0

Aggregates urban climate, air quality, and socioeconomic data for UK cities. Computes composite liveability scores and provides a natural-language query interface.

## Authentication

All protected endpoints require a Bearer token obtained from `POST /api/v1/auth/login`.

Include the token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

---

## Analytics

### `GET /api/v1/cities/{city_id}/liveability`

**Get Liveability**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl http://localhost:8000/api/v1/cities/1/liveability
```

**Example Response (200):**

```json
{
  "city_id": 1,
  "city_name": "Leeds",
  "overall_score": 61.4,
  "climate_score": 52.3,
  "affordability_score": 68.0,
  "safety_score": 72.0,
  "environment_score": 55.0,
  "data_points": 365
}
```

---

### `GET /api/v1/cities/compare`

**Compare Cities**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `ids` | query | string | Yes | Comma-separated city IDs |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/cities/compare?ids=1,2,3"
```

**Example Response (200):**

```json
[
  {
    "city_id": 1,
    "city_name": "Leeds",
    "overall_score": 61.4,
    "climate_score": 52.3,
    "affordability_score": 68.0,
    "safety_score": 72.0,
    "environment_score": 55.0,
    "data_points": 365
  },
  {
    "city_id": 2,
    "city_name": "Manchester",
    "overall_score": 58.7,
    "climate_score": 49.1,
    "affordability_score": 64.5,
    "safety_score": 65.0,
    "environment_score": 58.0,
    "data_points": 365
  },
  {
    "city_id": 3,
    "city_name": "Bristol",
    "overall_score": 66.2,
    "climate_score": 60.8,
    "affordability_score": 52.0,
    "safety_score": 78.0,
    "environment_score": 72.0,
    "data_points": 365
  }
]
```

---

### `GET /api/v1/cities/{city_id}/trends`

**Get Trends**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |
| `metric` | query | string | No | Metric to trend (`avg_temp_c`, `aqi`, `humidity_pct`, `precipitation_mm`) |
| `period` | query | string | No | Period e.g. `6m`, `12m`, `24m` |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/cities/1/trends?metric=avg_temp_c&period=6m"
```

**Example Response (200):**

```json
{
  "city_id": 1,
  "city_name": "Leeds",
  "metric": "avg_temp_c",
  "period": "6m",
  "data_points": [
    {"date": "2025-09-01", "value": 16.2},
    {"date": "2025-10-01", "value": 12.4},
    {"date": "2025-11-01", "value": 8.7},
    {"date": "2025-12-01", "value": 5.1},
    {"date": "2026-01-01", "value": 3.8},
    {"date": "2026-02-01", "value": 4.9}
  ]
}
```

---

### `GET /api/v1/cities/{city_id}/anomalies`

**Get Anomalies**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |
| `threshold` | query | number | No | Z-score threshold (default: 2.0) |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/cities/1/anomalies?threshold=2.0"
```

**Example Response (200):**

```json
{
  "city_id": 1,
  "city_name": "Leeds",
  "threshold": 2.0,
  "anomalies": [
    {
      "date": "2025-07-19",
      "metric": "avg_temp_c",
      "value": 31.4,
      "z_score": 3.12
    },
    {
      "date": "2026-01-08",
      "metric": "precipitation_mm",
      "value": 42.1,
      "z_score": 2.87
    }
  ]
}
```

---

## Authentication

### `POST /api/v1/auth/register`

**Register**

**Request Body** (`application/json`): `UserRegister`

**Responses:**

| Status | Description |
|--------|-------------|
| 201 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "securepass123"
  }'
```

**Example Response (201):**

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "role": "user",
  "created_at": "2026-03-20T10:00:00"
}
```

**Example Response (422 — validation error):**

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

### `POST /api/v1/auth/login`

**Login**

**Request Body** (`application/json`): `UserLogin`

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "securepass123"
  }'
```

**Example Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsImV4cCI6MTc0MjQ3MDAwMH0.abc123",
  "token_type": "bearer"
}
```

**Example Response (401 — invalid credentials):**

```json
{
  "detail": "Invalid username or password",
  "code": "INVALID_CREDENTIALS"
}
```

---

### `GET /api/v1/auth/me`

**Get Me**

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |

**Example Request:**

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

**Example Response (200):**

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "role": "user",
  "created_at": "2026-03-20T10:00:00"
}
```

---

### `POST /api/v1/auth/refresh`

**Refresh Token**

Issue a new access token for an authenticated user.

The caller must present a valid (non-expired) Bearer token.
A fresh token is returned with a reset expiry window.

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Authorization: Bearer <access_token>"
```

**Example Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsImV4cCI6MTc0MjQ3MzYwMH0.xyz789",
  "token_type": "bearer"
}
```

---

## Cities

### `POST /api/v1/cities`

**Create City**

Create a new city. Automatically triggers a background fetch of the last 365 days of weather data from the Open-Meteo archive API, stored as climate metrics.

**Request Body** (`application/json`): `CityCreate`

**Responses:**

| Status | Description |
|--------|-------------|
| 201 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/v1/cities \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "name": "Leeds",
    "region": "Yorkshire",
    "country": "UK",
    "latitude": 53.8008,
    "longitude": -1.5491,
    "population": 812000
  }'
```

**Example Response (201):**

```json
{
  "id": 1,
  "name": "Leeds",
  "region": "Yorkshire",
  "country": "UK",
  "latitude": 53.8008,
  "longitude": -1.5491,
  "population": 812000,
  "created_at": "2026-03-20T10:05:00",
  "updated_at": "2026-03-20T10:05:00"
}
```

---

### `GET /api/v1/cities`

**List Cities**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `offset` | query | integer | No | Pagination offset (default: 0) |
| `limit` | query | integer | No | Results per page, max 100 (default: 20) |
| `region` | query | string | No | Filter by region name |
| `sort` | query | string | No | Sort field, prefix with `-` for descending (e.g. `-population`) |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/cities?region=Yorkshire&limit=5&sort=-population"
```

**Example Response (200):**

```json
{
  "items": [
    {
      "id": 1,
      "name": "Leeds",
      "region": "Yorkshire",
      "country": "UK",
      "latitude": 53.8008,
      "longitude": -1.5491,
      "population": 812000,
      "created_at": "2026-03-20T10:05:00",
      "updated_at": "2026-03-20T10:05:00"
    },
    {
      "id": 4,
      "name": "Sheffield",
      "region": "Yorkshire",
      "country": "UK",
      "latitude": 53.3811,
      "longitude": -1.4701,
      "population": 584000,
      "created_at": "2026-03-20T10:06:00",
      "updated_at": "2026-03-20T10:06:00"
    }
  ],
  "total": 2,
  "offset": 0,
  "limit": 5
}
```

---

### `GET /api/v1/cities/{city_id}`

**Get City**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl http://localhost:8000/api/v1/cities/1
```

**Example Response (200):**

```json
{
  "id": 1,
  "name": "Leeds",
  "region": "Yorkshire",
  "country": "UK",
  "latitude": 53.8008,
  "longitude": -1.5491,
  "population": 812000,
  "created_at": "2026-03-20T10:05:00",
  "updated_at": "2026-03-20T10:05:00"
}
```

**Example Response (404 — not found):**

```json
{
  "detail": "City not found",
  "code": "NOT_FOUND"
}
```

---

### `PUT /api/v1/cities/{city_id}`

**Update City**

Update a city's details. Re-triggers a background fetch of the last 365 days of weather data from the Open-Meteo archive API; duplicate dates are skipped automatically.

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |

**Request Body** (`application/json`): `CityUpdate`

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X PUT http://localhost:8000/api/v1/cities/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "population": 830000
  }'
```

**Example Response (200):**

```json
{
  "id": 1,
  "name": "Leeds",
  "region": "Yorkshire",
  "country": "UK",
  "latitude": 53.8008,
  "longitude": -1.5491,
  "population": 830000,
  "created_at": "2026-03-20T10:05:00",
  "updated_at": "2026-03-20T11:00:00"
}
```

---

### `DELETE /api/v1/cities/{city_id}`

**Delete City** *(Admin only)*

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |

**Responses:**

| Status | Description |
|--------|-------------|
| 204 | Successful Response (no body) |
| 403 | Forbidden — admin role required |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X DELETE http://localhost:8000/api/v1/cities/1 \
  -H "Authorization: Bearer <admin_access_token>"
```

**Example Response (204):** *(empty body)*

**Example Response (403 — insufficient permissions):**

```json
{
  "detail": "Admin access required",
  "code": "FORBIDDEN"
}
```

---

## City Narrative

### `GET /api/v1/cities/{city_id}/narrative`

**Get City Narrative**

Returns a textual summary of a city's liveability based on its computed scores.

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl http://localhost:8000/api/v1/cities/1/narrative
```

**Example Response (200):**

```json
{
  "city_id": 1,
  "city_name": "Leeds",
  "narrative": "Leeds has an overall liveability score of 61.4/100. Climate scores 52.3/100, affordability 68.0/100, safety 72.0/100, and environment 55.0/100."
}
```

---

## Health

### `GET /`

**Health Check**

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |

**Example Request:**

```bash
curl http://localhost:8000/
```

**Example Response (200):**

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## Metrics

### `POST /api/v1/cities/{city_id}/climate-metrics`

**Create Climate Metric**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |

**Request Body** (`application/json`): `ClimateMetricCreate`

**Responses:**

| Status | Description |
|--------|-------------|
| 201 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/v1/cities/1/climate-metrics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "date": "2026-03-20",
    "avg_temp_c": 8.5,
    "aqi": 42.0,
    "humidity_pct": 78.0,
    "precipitation_mm": 3.2,
    "source": "manual"
  }'
```

**Example Response (201):**

```json
{
  "id": 1001,
  "city_id": 1,
  "date": "2026-03-20",
  "avg_temp_c": 8.5,
  "aqi": 42.0,
  "humidity_pct": 78.0,
  "precipitation_mm": 3.2,
  "source": "manual",
  "created_at": "2026-03-20T12:00:00"
}
```

---

### `GET /api/v1/cities/{city_id}/climate-metrics`

**List Climate Metrics**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |
| `start_date` | query | string | No | ISO date, e.g. `2026-01-01` |
| `end_date` | query | string | No | ISO date, e.g. `2026-03-20` |
| `offset` | query | integer | No | Pagination offset (default: 0) |
| `limit` | query | integer | No | Results per page, max 100 (default: 20) |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/cities/1/climate-metrics?start_date=2026-03-01&end_date=2026-03-20&limit=3"
```

**Example Response (200):**

```json
{
  "items": [
    {
      "id": 999,
      "city_id": 1,
      "date": "2026-03-01",
      "avg_temp_c": 7.1,
      "aqi": 38.5,
      "humidity_pct": 81.0,
      "precipitation_mm": 1.4,
      "source": "open_meteo",
      "created_at": "2026-03-20T10:05:12"
    },
    {
      "id": 1000,
      "city_id": 1,
      "date": "2026-03-10",
      "avg_temp_c": 9.3,
      "aqi": 35.0,
      "humidity_pct": 74.5,
      "precipitation_mm": 0.0,
      "source": "open_meteo",
      "created_at": "2026-03-20T10:05:12"
    },
    {
      "id": 1001,
      "city_id": 1,
      "date": "2026-03-20",
      "avg_temp_c": 8.5,
      "aqi": 42.0,
      "humidity_pct": 78.0,
      "precipitation_mm": 3.2,
      "source": "manual",
      "created_at": "2026-03-20T12:00:00"
    }
  ],
  "total": 3,
  "offset": 0,
  "limit": 3
}
```

---

### `GET /api/v1/climate-metrics/{metric_id}`

**Get Climate Metric**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `metric_id` | path | integer | Yes |  |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl http://localhost:8000/api/v1/climate-metrics/1001
```

**Example Response (200):**

```json
{
  "id": 1001,
  "city_id": 1,
  "date": "2026-03-20",
  "avg_temp_c": 8.5,
  "aqi": 42.0,
  "humidity_pct": 78.0,
  "precipitation_mm": 3.2,
  "source": "manual",
  "created_at": "2026-03-20T12:00:00"
}
```

---

### `DELETE /api/v1/climate-metrics/{metric_id}`

**Delete Climate Metric** *(Admin only)*

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `metric_id` | path | integer | Yes |  |

**Responses:**

| Status | Description |
|--------|-------------|
| 204 | Successful Response (no body) |
| 403 | Forbidden — admin role required |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X DELETE http://localhost:8000/api/v1/climate-metrics/1001 \
  -H "Authorization: Bearer <admin_access_token>"
```

**Example Response (204):** *(empty body)*

---

### `POST /api/v1/cities/{city_id}/socioeconomic-metrics`

**Create Socioeconomic Metric**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |

**Request Body** (`application/json`): `SocioeconomicMetricCreate`

**Responses:**

| Status | Description |
|--------|-------------|
| 201 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/v1/cities/1/socioeconomic-metrics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "year": 2025,
    "median_rent_gbp": 950,
    "green_space_pct": 22.5,
    "crime_index": 45.0,
    "avg_commute_min": 34,
    "source": "ONS"
  }'
```

**Example Response (201):**

```json
{
  "id": 42,
  "city_id": 1,
  "year": 2025,
  "median_rent_gbp": 950,
  "green_space_pct": 22.5,
  "crime_index": 45.0,
  "avg_commute_min": 34,
  "source": "ONS",
  "created_at": "2026-03-20T12:05:00"
}
```

---

### `GET /api/v1/cities/{city_id}/socioeconomic-metrics`

**List Socioeconomic Metrics**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |
| `offset` | query | integer | No | Pagination offset (default: 0) |
| `limit` | query | integer | No | Results per page, max 100 (default: 20) |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/cities/1/socioeconomic-metrics"
```

**Example Response (200):**

```json
{
  "items": [
    {
      "id": 40,
      "city_id": 1,
      "year": 2023,
      "median_rent_gbp": 875,
      "green_space_pct": 22.5,
      "crime_index": 47.0,
      "avg_commute_min": 36,
      "source": "ONS",
      "created_at": "2026-03-20T10:05:00"
    },
    {
      "id": 42,
      "city_id": 1,
      "year": 2025,
      "median_rent_gbp": 950,
      "green_space_pct": 22.5,
      "crime_index": 45.0,
      "avg_commute_min": 34,
      "source": "ONS",
      "created_at": "2026-03-20T12:05:00"
    }
  ],
  "total": 2,
  "offset": 0,
  "limit": 20
}
```

---

### `GET /api/v1/socioeconomic-metrics/{metric_id}`

**Get Socioeconomic Metric**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `metric_id` | path | integer | Yes |  |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl http://localhost:8000/api/v1/socioeconomic-metrics/42
```

**Example Response (200):**

```json
{
  "id": 42,
  "city_id": 1,
  "year": 2025,
  "median_rent_gbp": 950,
  "green_space_pct": 22.5,
  "crime_index": 45.0,
  "avg_commute_min": 34,
  "source": "ONS",
  "created_at": "2026-03-20T12:05:00"
}
```

---

### `DELETE /api/v1/socioeconomic-metrics/{metric_id}`

**Delete Socioeconomic Metric** *(Admin only)*

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `metric_id` | path | integer | Yes |  |

**Responses:**

| Status | Description |
|--------|-------------|
| 204 | Successful Response (no body) |
| 403 | Forbidden — admin role required |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X DELETE http://localhost:8000/api/v1/socioeconomic-metrics/42 \
  -H "Authorization: Bearer <admin_access_token>"
```

**Example Response (204):** *(empty body)*

---

## Observations

### `POST /api/v1/cities/{city_id}/observations`

**Create Observation**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |

**Request Body** (`application/json`): `ObservationCreate`

**Responses:**

| Status | Description |
|--------|-------------|
| 201 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/v1/cities/1/observations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "category": "air_quality",
    "value": 38.5,
    "note": "Noticeably cleaner after the rain"
  }'
```

**Example Response (201):**

```json
{
  "id": 15,
  "city_id": 1,
  "user_id": 1,
  "category": "air_quality",
  "value": 38.5,
  "note": "Noticeably cleaner after the rain",
  "recorded_at": "2026-03-20T14:30:00",
  "created_at": "2026-03-20T14:30:00"
}
```

---

### `GET /api/v1/cities/{city_id}/observations`

**List Observations**

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `city_id` | path | integer | Yes |  |
| `offset` | query | integer | No | Pagination offset (default: 0) |
| `limit` | query | integer | No | Results per page, max 100 (default: 20) |

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 422 | Validation Error |

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/cities/1/observations?limit=2"
```

**Example Response (200):**

```json
{
  "items": [
    {
      "id": 14,
      "city_id": 1,
      "user_id": 1,
      "category": "noise_level",
      "value": 65.0,
      "note": "Heavy traffic near the ring road",
      "recorded_at": "2026-03-19T09:00:00",
      "created_at": "2026-03-19T09:00:00"
    },
    {
      "id": 15,
      "city_id": 1,
      "user_id": 1,
      "category": "air_quality",
      "value": 38.5,
      "note": "Noticeably cleaner after the rain",
      "recorded_at": "2026-03-20T14:30:00",
      "created_at": "2026-03-20T14:30:00"
    }
  ],
  "total": 2,
  "offset": 0,
  "limit": 2
}
```

---

### `PUT /api/v1/observations/{obs_id}`

**Update Observation** *(Owner only)*

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `obs_id` | path | integer | Yes |  |

**Request Body** (`application/json`): `ObservationUpdate`

**Responses:**

| Status | Description |
|--------|-------------|
| 200 | Successful Response |
| 403 | Forbidden — must be observation owner |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X PUT http://localhost:8000/api/v1/observations/15 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "value": 35.0,
    "note": "Updated after re-reading the sensor"
  }'
```

**Example Response (200):**

```json
{
  "id": 15,
  "city_id": 1,
  "user_id": 1,
  "category": "air_quality",
  "value": 35.0,
  "note": "Updated after re-reading the sensor",
  "recorded_at": "2026-03-20T14:30:00",
  "created_at": "2026-03-20T14:30:00"
}
```

---

### `DELETE /api/v1/observations/{obs_id}`

**Delete Observation** *(Owner only)*

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `obs_id` | path | integer | Yes |  |

**Responses:**

| Status | Description |
|--------|-------------|
| 204 | Successful Response (no body) |
| 403 | Forbidden — must be observation owner |
| 422 | Validation Error |

**Example Request:**

```bash
curl -X DELETE http://localhost:8000/api/v1/observations/15 \
  -H "Authorization: Bearer <access_token>"
```

**Example Response (204):** *(empty body)*

---

## Data Models

### CityCreate

| Field | Type | Required |
|-------|------|----------|
| `name` | string | Yes |
| `region` | string | Yes |
| `country` | string | No |
| `latitude` | number | Yes |
| `longitude` | number | Yes |
| `population` | integer | No |

### CityResponse

| Field | Type | Required |
|-------|------|----------|
| `id` | integer | Yes |
| `name` | string | Yes |
| `region` | string | Yes |
| `country` | string | Yes |
| `latitude` | number | Yes |
| `longitude` | number | Yes |
| `population` | integer | Yes |
| `created_at` | string (datetime) | No |
| `updated_at` | string (datetime) | No |

### CityUpdate

| Field | Type | Required |
|-------|------|----------|
| `name` | string | No |
| `region` | string | No |
| `country` | string | No |
| `latitude` | number | No |
| `longitude` | number | No |
| `population` | integer | No |

### ClimateMetricCreate

| Field | Type | Required |
|-------|------|----------|
| `date` | string (ISO date) | Yes |
| `avg_temp_c` | number | No |
| `aqi` | number | No |
| `humidity_pct` | number | No |
| `precipitation_mm` | number | No |
| `source` | string | No |

### ClimateMetricResponse

| Field | Type | Required |
|-------|------|----------|
| `id` | integer | Yes |
| `city_id` | integer | Yes |
| `date` | string (ISO date) | Yes |
| `avg_temp_c` | number | Yes |
| `aqi` | number | Yes |
| `humidity_pct` | number | Yes |
| `precipitation_mm` | number | Yes |
| `source` | string | Yes |
| `created_at` | string (datetime) | No |

### NarrativeResponse

| Field | Type | Required |
|-------|------|----------|
| `city_id` | integer | Yes |
| `city_name` | string | Yes |
| `narrative` | string | Yes |

### ObservationCreate

| Field | Type | Required |
|-------|------|----------|
| `category` | string | Yes |
| `value` | number | Yes |
| `note` | string | No |

### ObservationResponse

| Field | Type | Required |
|-------|------|----------|
| `id` | integer | Yes |
| `city_id` | integer | Yes |
| `user_id` | integer | Yes |
| `category` | string | Yes |
| `value` | number | Yes |
| `note` | string | Yes |
| `recorded_at` | string (datetime) | No |
| `created_at` | string (datetime) | No |

### ObservationUpdate

| Field | Type | Required |
|-------|------|----------|
| `category` | string | No |
| `value` | number | No |
| `note` | string | No |

### SocioeconomicMetricCreate

| Field | Type | Required |
|-------|------|----------|
| `year` | integer | Yes |
| `median_rent_gbp` | number | No |
| `green_space_pct` | number | No |
| `crime_index` | number | No |
| `avg_commute_min` | number | No |
| `source` | string | No |

### SocioeconomicMetricResponse

| Field | Type | Required |
|-------|------|----------|
| `id` | integer | Yes |
| `city_id` | integer | Yes |
| `year` | integer | Yes |
| `median_rent_gbp` | number | Yes |
| `green_space_pct` | number | Yes |
| `crime_index` | number | Yes |
| `avg_commute_min` | number | Yes |
| `source` | string | Yes |
| `created_at` | string (datetime) | No |

### TokenResponse

| Field | Type | Required |
|-------|------|----------|
| `access_token` | string | Yes |
| `token_type` | string | No |

### UserLogin

| Field | Type | Required |
|-------|------|----------|
| `username` | string | Yes |
| `password` | string | Yes |

### UserRegister

| Field | Type | Required |
|-------|------|----------|
| `username` | string | Yes |
| `email` | string | Yes |
| `password` | string | Yes |

### UserResponse

| Field | Type | Required |
|-------|------|----------|
| `id` | integer | Yes |
| `username` | string | Yes |
| `email` | string | Yes |
| `role` | string | Yes |
| `created_at` | string (datetime) | No |

### PaginatedResponse

All list endpoints return a paginated envelope:

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | The result objects |
| `total` | integer | Total matching records |
| `offset` | integer | Current page offset |
| `limit` | integer | Page size |

### Error Response

| Field | Type | Description |
|-------|------|-------------|
| `detail` | string | Human-readable error message |
| `code` | string | Machine-readable error code |

### ValidationError (422)

| Field | Type | Required |
|-------|------|----------|
| `loc` | array | Field location path |
| `msg` | string | Error description |
| `type` | string | Error type identifier |
