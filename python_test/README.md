# Python Developer Test Project

A three-tier application built to demonstrate Python backend skills with FastAPI, proxied through a Node.js gateway and displayed in a React frontend.

## Documentation

- **[Getting Started](./GETTING_STARTED.md)** — Python test setup guide
- **[Test Requirements](./TEST_REQUIREMENTS.md)** — Complete requirements and evaluation criteria
- **[Test Summary](./TEST_SUMMARY.md)** — Quick overview of required tasks
- **[Candidate Checklist](./CANDIDATE_CHECKLIST.md)** — Original task checklist

## Architecture

```
React Frontend (port 5173)
        ↓  HTTP
Node.js Backend (port 3000)   ← API gateway / proxy
        ↓  HTTP + X-API-Key
Python Backend (port 8080)    ← all business logic and data
```

## Quick Start

Start services in this order, each in its own terminal.

### 1. Python Backend

```bash
cd python-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

With optional features enabled:

```bash
# API key auth + rate limiting + SQLite persistence
API_KEYS=mykey123 \
RATE_LIMIT_REQUESTS=100 \
RATE_LIMIT_WINDOW=60 \
DATABASE_URL=sqlite:///data.db \
python -m app.main
```

### 2. Node.js Backend

```bash
cd node-backend
npm install
API_KEY=mykey123 npm start   # key must match Python's API_KEYS
# or for development auto-reload:
API_KEY=mykey123 npm run dev
```

### 3. React Frontend

```bash
cd react-frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

---

## What Was Required (Candidate Checklist)

### Phase 1 — Setup
All services installed, started, and verified end-to-end.

### Phase 2 — Core Endpoints (required, 2–3 hours)

| Task | Result |
|---|---|
| `POST /api/users` — validate name, email format, role; return 201 | Done |
| `POST /api/tasks` — validate title, status enum, userId existence; return 201 | Done |
| `PUT /api/tasks/{id}` — partial update; 404 if not found, 400 on bad input | Done |
| Request logging middleware — method, path, status code, response time | Done |

### Phase 3 — Advanced Requirements (optional)

| Task | Result |
|---|---|
| Data persistence (JSON file via `DATA_FILE` env var, survives restart) | Done |
| Caching layer with expiration (stats cached 30 s, invalidated on mutations) | Done |
| Request validation middleware (Content-Type check — 415 for non-JSON POST/PUT) | Done |
| Enhanced health check (uptime in seconds, live user/task counts from store) | Done |

### Phase 4 — Code Quality (required)

| Area | Result |
|---|---|
| Unit tests for DataStore (`tests/test_data_store.py`) — 29 tests | Done |
| Integration tests for users (`tests/test_api_users.py`) — 22 tests | Done |
| Integration tests for tasks (`tests/test_api_tasks.py`) — 31 tests | Done |
| Integration tests for existing endpoints (`tests/test_api_existing.py`) — 18 tests | Done |
| Phase 3 tests (`tests/test_phase3.py`) — 23 tests | Done |
| Phase 5 tests (`tests/test_phase5.py`) — 41 tests | Done |
| Appropriate HTTP status codes (201, 400, 404, 415, 429, 401, 403, 500) | Done |
| Errors logged with context; internal details never exposed to clients | Done |
| Python naming conventions, single-purpose functions, no unused code | Done |
| API reference, error table, env var table in `python-backend/README.md` | Done |

Run the full test suite:

```bash
cd python-backend
python -m pytest tests/ -v --tb=short
```

### Phase 5 — Bonus Tasks (optional)

| Task | Result |
|---|---|
| API key authentication (`API_KEYS` env var, `X-API-Key` header, 401/403) | Done |
| Per-IP rate limiting (`RATE_LIMIT_REQUESTS`/`RATE_LIMIT_WINDOW`, sliding window, 429 + `Retry-After`) | Done |
| Metrics / observability (`GET /metrics` — total requests, error counts, response times, by method, by status) | Done |
| SQLite database (`DATABASE_URL=sqlite:///path` — drop-in replacement for in-memory store) | Done |

---

## What We Added Beyond the Checklist

The following were not in the candidate checklist but were built to make the application fully end-to-end and production-closer.

### Python Backend Extras

| Addition | Detail |
|---|---|
| Custom Pydantic v2 validation errors mapped to HTTP 400 | FastAPI's default is 422; we intercept `RequestValidationError` and return 400 with a flat list of field messages |
| Global 500 handler | Catches uncaught exceptions, logs full traceback, returns a safe generic message — no stack traces leak to the client |
| Sliding window rate limiting | Uses `collections.deque` per IP for accurate per-window counting, not a fixed counter |
| Stats cache invalidation on writes | Cache is explicitly cleared inside the same lock block as every mutation, not just on TTL expiry |
| SQLite WAL mode + foreign keys | WAL journal mode for concurrent read performance; foreign key constraints enforced at the DB level |
| `MetricsCollector` class | Thread-safe metrics (total requests, status code buckets, per-method counts, response time list) exposed via `GET /metrics` — always public, even when auth is on |
| Health and metrics always bypass auth | `/health` and `/metrics` are explicitly excluded from API key and rate-limit middleware so monitoring never gets locked out |

### Node.js Backend Extras

| Addition | Detail |
|---|---|
| `GET /api/metrics` route | New `routes/metrics.js` + `controllers/metricsController.js` — proxies Python's `/metrics` to the frontend |
| `X-API-Key` header injection | `httpClient.js` reads `API_KEY` from config and injects the header on every outbound call to Python; the key never touches the browser |
| Python error shape normalisation | `httpClient.js` parses `{"detail": "..."}` and `{"detail": [...]}` from Pydantic and re-throws as a plain string so the frontend always gets a usable message |
| Updated `README.md` | Full env var table, all endpoints with curl examples, project structure, error handling explanation |

### React Frontend Extras

| Addition | Detail |
|---|---|
| `CreateUserForm` component | Collapsible inline form (name, email, role select); shows field-level error from Python validation; updates user list and stats on success |
| `CreateTaskForm` component | Collapsible inline form (title, status select, user select from live list); updates task list and stats on success |
| Inline task status update | Each task card has a status dropdown; change fires `PUT /api/tasks/:id` immediately with a "saving…" indicator and per-card error display |
| `Metrics` component | Displays total requests, 4xx/5xx errors, uptime, avg/min/max response times, per-method bar chart, per-status coloured pills, manual refresh |
| Enhanced `HealthStatus` component | Shows Python health fields as pills: backend status, uptime in seconds, live user and task counts |
| Axios error interceptor | Normalises Python's `detail` field (string or array) into a single error message string — no special-casing at call sites |
| Stats and metrics auto-refresh | After any create operation the stats panel and metrics panel refresh automatically without a full page reload |
| Updated `README.md` | Feature descriptions, component tree, API function table, state flow diagram, full-stack start commands |

---

## Project Structure

```
python-test/
├── README.md                  ← this file
├── CANDIDATE_CHECKLIST.md
├── TEST_REQUIREMENTS.md
├── TEST_SUMMARY.md
├── GETTING_STARTED.md
├── docs/
│   └── progress.md            ← step-by-step implementation explanations
├── python-backend/
│   ├── README.md              ← full API reference + env vars
│   ├── requirements.txt
│   └── app/
│       └── main.py            ← FastAPI app, all models, middleware, routes
│   └── tests/
│       ├── conftest.py
│       ├── test_data_store.py
│       ├── test_api_users.py
│       ├── test_api_tasks.py
│       ├── test_api_existing.py
│       ├── test_phase3.py
│       └── test_phase5.py
├── node-backend/
│   ├── README.md              ← endpoints, env vars, error handling
│   ├── app.js
│   ├── config/index.js        ← PORT, GO_BACKEND_URL, API_KEY
│   ├── routes/
│   │   ├── index.js
│   │   ├── health.js
│   │   ├── users.js
│   │   ├── tasks.js
│   │   ├── stats.js
│   │   └── metrics.js         ← added
│   ├── controllers/
│   │   └── metricsController.js  ← added
│   └── utils/
│       └── httpClient.js      ← X-API-Key injection, error normalisation
└── react-frontend/
    ├── README.md              ← features, component tree, API table, state flow
    ├── vite.config.js
    └── src/
        ├── App.jsx            ← root state and handlers
        ├── services/api.js    ← all axios calls, error normalisation
        └── components/
            ├── HealthStatus.jsx / .css   ← enhanced with Python detail pills
            ├── Metrics.jsx / .css        ← added — observability panel
            ├── CreateUserForm.jsx / .css ← added
            ├── CreateTaskForm.jsx / .css ← added
            ├── TaskList.jsx / .css       ← enhanced with inline status update
            ├── UserList.jsx / .css
            └── Stats.jsx / .css
```
