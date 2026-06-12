# Python Developer Test Project

This project is designed to test **Python developers'** skills in building a backend service (FastAPI) that powers a React + Node.js application.

## 📚 Documentation

- **[Getting Started](./GETTING_STARTED.md)** – Python test setup guide
- **[Test Requirements](./TEST_REQUIREMENTS.md)** – Complete Python test requirements and evaluation criteria
- **[Test Summary](./TEST_SUMMARY.md)** – Quick overview of required tasks
- **[Candidate Checklist](./CANDIDATE_CHECKLIST.md)** – Track your progress

## Project Structure

```
python-test/
├── python-backend/   # FastAPI HTTP server (data source)
├── node-backend/     # Node.js Express API server (calls Python backend)
└── react-frontend/   # React frontend (calls Node.js backend)
```

## Architecture Flow

```
React Frontend (port 5173)
    ↓
Node.js Backend (port 3000)
    ↓
Python Backend (port 8080)
```

## Quick Start

**Important:** Start services in this order (inside `python-test/`):

### 1. Start Python Backend (Data Source)

```bash
cd python-backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m app.main
```

The Python backend will run on `http://localhost:8080` and serves as the data source.

### 2. Start Node.js Backend (API Gateway)

In a new terminal:

```bash
cd node-backend
npm install
npm start
```

The Node.js backend will run on `http://localhost:3000` and proxies requests to the Python backend.

### 3. Start React Frontend

In a new terminal:

```bash
cd react-frontend
npm install
npm run dev
```

The React frontend will run on `http://localhost:5173` and calls the Node.js backend.

## Project Overview

### Python Backend (Data Source)
A FastAPI server that:
- Serves as the primary data source
- Stores users and tasks in-memory
- Exposes REST endpoints (`/api/users`, `/api/tasks`, `/api/stats`)
- Handles JSON requests/responses
- Uses a thread-safe in-memory data store

### Node.js Backend (API Gateway)
Same as other tests: proxies frontend requests to the Python backend.

### React Frontend
Same UI as other tests: shows users, tasks, stats, and health.

## Implementation Status

### Phase 2 — Core Endpoints (complete)

| Endpoint | Status |
|---|---|
| `POST /api/users` | Implemented — validates name, email format, role enum; 201 on success, 400 on bad input or duplicate email |
| `POST /api/tasks` | Implemented — validates title, status enum, userId existence; 201 on success, 400 on bad input |
| `PUT /api/tasks/{id}` | Implemented — partial update; 200 on success, 404 if not found, 400 on bad input |
| Request logging middleware | Implemented — logs method, path, status code, duration on every request |

### Phase 5 — Bonus Features (complete)

| Feature | Status |
|---|---|
| API key authentication (`API_KEYS` env var, `X-API-Key` header, 401/403) | Done |
| Per-IP rate limiting (`RATE_LIMIT_REQUESTS`/`RATE_LIMIT_WINDOW`, 429 + `Retry-After`) | Done |
| Metrics endpoint (`GET /metrics` — counters, status breakdown, response times) | Done |
| SQLite database integration (`DATABASE_URL=sqlite:///…`, drop-in store replacement) | Done |

### Phase 3 — Advanced Features (complete)

| Feature | Status |
|---|---|
| JSON persistence (`DATA_FILE` env var, survives restart) | Done |
| Stats caching with 30s TTL, invalidated on every mutation | Done |
| Content-Type middleware — rejects non-JSON `POST`/`PUT` with 415 | Done |
| Enhanced health check — uptime, live user/task counts | Done |

### Phase 4 — Code Quality (complete)

| Area | Status |
|---|---|
| Unit tests (`tests/test_data_store.py`) | 16 tests — DataStore methods, thread-safety, edge cases |
| Integration tests (`tests/test_api_users.py`) | 22 tests — happy path, all validation errors, duplicate email |
| Integration tests (`tests/test_api_existing.py`) | 18 tests — health, GET users/tasks/stats, filters |
| Error handling | HTTP 400 / 404 / 500 with consistent JSON shape; stack traces never exposed |
| Documentation | API reference, error table, test instructions in `python-backend/README.md` |

Run tests: `cd python-backend && python -m pytest tests/ -v`

## Test Requirements

**See [TEST_REQUIREMENTS.md](./TEST_REQUIREMENTS.md) for detailed Python test requirements and evaluation criteria.**
