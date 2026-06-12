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

| Variable    | Default          | Description |
|-------------|------------------|-------------|
| `PORT`      | `8080`           | Port the server listens on |
| `DATA_FILE` | `data/store.json`| Path for JSON persistence. Set to `""` to disable persistence and use in-memory seed data only |

```bash
PORT=8081 DATA_FILE=mydata.json python -m app.main
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
