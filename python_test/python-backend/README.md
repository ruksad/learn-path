# Python Backend

FastAPI service that is the authoritative data source for the three-tier stack.

## Stack

- Python 3.9+ (developed on 3.12)
- FastAPI 0.115
- Uvicorn
- Pydantic v2

## Project Structure

```
python-backend/
├── app/
│   ├── __init__.py
│   └── main.py          # models, DataStore, middleware, routes
├── tests/
│   ├── conftest.py      # pytest fixtures (TestClient, fresh DataStore)
│   ├── test_data_store.py   # unit tests — DataStore methods
│   ├── test_api_users.py    # integration tests — POST /api/users
│   └── test_api_existing.py # integration tests — read-only endpoints
├── requirements.txt
└── README.md
```

## Running the Server

```bash
cd python-backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main               # starts on http://localhost:8080
```

### Environment variables

| Variable               | Default           | Description |
|------------------------|-------------------|-------------|
| `PORT`                 | `8080`            | Port the server listens on |
| `DATA_FILE`            | `data/store.json` | JSON persistence path. Set to `""` to disable (in-memory only) |
| `DATABASE_URL`         | _(unset)_         | Use SQLite backend: `sqlite:///path/to/db.sqlite` or `sqlite:///:memory:` |
| `API_KEYS`             | _(unset)_         | Comma-separated valid API keys. Unset = auth disabled |
| `RATE_LIMIT_REQUESTS`  | `0`               | Max requests per IP per window. `0` = disabled |
| `RATE_LIMIT_WINDOW`    | `60`              | Sliding window size in seconds |

```bash
# Full production-like startup
DATABASE_URL=sqlite:///data/store.db \
API_KEYS=mykey123,anotherkey \
RATE_LIMIT_REQUESTS=100 \
RATE_LIMIT_WINDOW=60 \
python -m app.main
```

## Running Tests

```bash
cd python-backend
source .venv/bin/activate
python -m pytest tests/ -v
```

With coverage:

```bash
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

## API Reference

### `GET /health`

Returns live server state — no caching.

```json
{
  "status": "ok",
  "message": "Python backend is running",
  "uptime_seconds": 142.3,
  "store_users": 3,
  "store_tasks": 5
}
```

---

### `GET /api/users`

Returns all users.

```json
{
  "users": [
    { "id": 1, "name": "John Doe", "email": "john@example.com", "role": "developer" }
  ],
  "count": 1
}
```

---

### `POST /api/users`

Creates a new user.

**Request body:**

| Field  | Type   | Required | Validation |
|--------|--------|----------|------------|
| `name` | string | yes      | Non-blank |
| `email`| string | yes      | Valid email format; must be unique |
| `role` | string | yes      | One of: `admin`, `designer`, `developer`, `manager`, `qa` |

**Example request:**

```json
{ "name": "Alice", "email": "alice@example.com", "role": "developer" }
```

**201 Created — success:**

```json
{ "id": 4, "name": "Alice", "email": "alice@example.com", "role": "developer" }
```

**400 Bad Request — validation failure:**

```json
{ "detail": ["body -> email: email is not a valid email address"] }
```

**400 Bad Request — duplicate email:**

```json
{ "detail": "email 'alice@example.com' is already in use" }
```

---

### `GET /api/users/{id}`

Returns a single user.

- `200` — user found
- `404` — `{ "detail": "User not found" }`

---

### `POST /api/tasks`

Creates a new task.

**Request body:**

| Field    | Type    | Required | Validation |
|----------|---------|----------|------------|
| `title`  | string  | yes      | Non-blank |
| `status` | string  | yes      | One of: `completed`, `in-progress`, `pending` |
| `userId` | integer | yes      | Positive integer; must reference an existing user |

**Example request:**

```json
{ "title": "Write unit tests", "status": "pending", "userId": 1 }
```

**201 Created — success:**

```json
{ "id": 4, "title": "Write unit tests", "status": "pending", "userId": 1 }
```

**400 Bad Request — invalid status:**

```json
{ "detail": ["body -> status: status must be one of: completed, in-progress, pending"] }
```

**400 Bad Request — unknown userId:**

```json
{ "detail": "user with id 99 does not exist" }
```

---

### `PUT /api/tasks/{id}`

Partially updates an existing task. All fields are optional — omitted fields keep their current value.

**Request body (all optional):**

| Field    | Type    | Validation when provided |
|----------|---------|--------------------------|
| `title`  | string  | Non-blank |
| `status` | string  | One of: `completed`, `in-progress`, `pending` |
| `userId` | integer | Must reference an existing user |

**Example — update status only:**

```json
{ "status": "completed" }
```

**200 OK — success:**

```json
{ "id": 1, "title": "Implement authentication", "status": "completed", "userId": 1 }
```

- `404` — `{ "detail": "Task not found" }` if `id` does not exist
- `400` — validation error if a provided field is invalid

---

### `GET /api/tasks`

Returns tasks. Supports query filters:

| Param    | Example       | Description |
|----------|---------------|-------------|
| `status` | `pending`     | Filter by status (`pending`, `in-progress`, `completed`) |
| `userId` | `1`           | Filter by user ID |

---

### `GET /api/stats`

```json
{
  "users": { "total": 3 },
  "tasks": { "total": 3, "pending": 1, "inProgress": 1, "completed": 1 }
}
```

## Phase 5 Features

### Authentication — API Keys

Set `API_KEYS` to a comma-separated list of valid keys. When set, all `/api/*` routes require an `X-API-Key` header. `/health` and `/metrics` are always public.

| Scenario | Status |
|---|---|
| Missing `X-API-Key` header | **401** `{ "detail": "Missing X-API-Key header" }` |
| Wrong key | **403** `{ "detail": "Invalid API key" }` |
| Valid key | Request proceeds normally |
| `API_KEYS` not set | Auth disabled — all requests allowed |

```bash
# Enable auth with two keys
API_KEYS=key-abc-123,key-xyz-456 python -m app.main
```

```
curl -H "X-API-Key: key-abc-123" http://localhost:8080/api/users
```

---

### Rate Limiting — Per-IP Sliding Window

Set `RATE_LIMIT_REQUESTS` to the max allowed requests per IP within `RATE_LIMIT_WINDOW` seconds.

```bash
# 100 requests per minute per IP
RATE_LIMIT_REQUESTS=100 RATE_LIMIT_WINDOW=60 python -m app.main
```

When a client exceeds the limit it receives:

```
HTTP 429 Too Many Requests
Retry-After: 60

{ "detail": "Too many requests — please slow down" }
```

`RATE_LIMIT_REQUESTS=0` (the default) disables rate limiting entirely.

---

### Metrics Endpoint — `GET /metrics`

Always public (no API key required). Returns live counters and timing stats:

```json
{
  "uptime_seconds": 142.3,
  "requests": {
    "total_requests": 250,
    "by_status": { "200": 210, "201": 18, "400": 12, "404": 5, "429": 5 },
    "by_method": { "GET": 185, "POST": 50, "PUT": 15 },
    "errors_4xx": 22,
    "errors_5xx": 0,
    "response_times_ms": {
      "avg": 2.4,
      "min": 0.5,
      "max": 48.1,
      "samples": 250
    }
  },
  "store": {
    "users": 5,
    "tasks": 12
  }
}
```

Metrics include all responses — 401, 403, 415, 429 — not just successful ones.

---

### Database Integration — SQLite

Set `DATABASE_URL` to switch from JSON-file persistence to a full SQLite database:

```bash
DATABASE_URL=sqlite:///data/store.db python -m app.main
```

| `DATABASE_URL` value | Backend used |
|---|---|
| _(unset)_ | In-memory `DataStore` with optional JSON file via `DATA_FILE` |
| `sqlite:///path/to/db` | `SQLiteDataStore` — file-based SQLite |
| `sqlite:///:memory:` | `SQLiteDataStore` — in-memory SQLite (useful for testing) |

`SQLiteDataStore` is a drop-in replacement for `DataStore` — same public interface, same seed data, same caching behaviour. SQLite is configured with `WAL` journal mode for concurrent reads and `PRAGMA foreign_keys=ON` for referential integrity.

---

## Phase 3 Features

### Data Persistence

All mutations (`POST /api/users`, `POST /api/tasks`, `PUT /api/tasks/{id}`) are written to a JSON file atomically after each change. On startup the server reads from this file; if the file is absent it falls back to in-memory seed data.

Configure the path with `DATA_FILE` env var. Set to `""` to run fully in-memory (useful for tests or stateless deployments).

### Stats Caching

`GET /api/stats` results are cached in memory for **30 seconds**. The cache is immediately invalidated on any mutation (create user, create task, update task), so the stats are never stale after a write — only reads within the 30-second window after a mutation-free period can serve a cached value.

### Content-Type Middleware

`POST` and `PUT` requests without `Content-Type: application/json` are rejected with **HTTP 415** before reaching any route handler:

```json
{ "detail": "Content-Type must be application/json" }
```

`GET` requests are unaffected. All 415 rejections are logged at `WARNING` level.

---

## Error Handling

All errors follow a consistent shape:

| Status | Meaning |
|--------|---------|
| `400`  | Invalid input or business rule violation (e.g. duplicate email) |
| `404`  | Resource not found |
| `500`  | Unhandled server error — detail is always `"Internal server error"` |

Internal stack traces are never returned to the caller; they are logged server-side.

## Request Logging

Every request is logged in this format:

```
2026-06-12 10:23:01,412 INFO POST /api/users 201 3.2ms
```

Fields: `timestamp  LEVEL  METHOD  PATH  STATUS_CODE  DURATION_ms`

Validation errors are logged at `WARNING` level. Unhandled exceptions are logged at `ERROR` level with a full traceback.
