# Node.js Backend

Express.js API gateway that sits between the React frontend and the Python backend. It proxies all requests, injects the Python API key, and normalises error shapes so the frontend always receives a consistent response format.

## Architecture

```
React (5173) → Node.js (3000) → Python (8080)
```

All business logic and data live in the Python backend. Node.js only routes, proxies, and translates.

## Setup

```bash
npm install
npm start          # production
npm run dev        # development — auto-reloads with nodemon
```

Server runs on `http://localhost:3000` by default.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3000` | Port the Express server listens on |
| `GO_BACKEND_URL` | `http://localhost:8080` | URL of the Python backend |
| `PYTHON_API_KEY` | _(empty)_ | Forwarded as `X-API-Key` on every Python request. Must match `API_KEYS` set on the Python backend |

Create a `.env` file in this directory to set them:

```env
GO_BACKEND_URL=http://localhost:8080
PYTHON_API_KEY=mykey123
```

> **Important:** if the Python backend is started with `API_KEYS=mykey123`, Node.js must be started with `PYTHON_API_KEY=mykey123` — otherwise every proxied request returns 401.

## API Endpoints

All routes are thin proxies to the Python backend.

### Health
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Node.js status + Python health forwarded as `goBackend` |

```bash
curl http://localhost:3000/health
# { "status": "ok", "message": "...", "goBackend": { "status": "ok", "uptime_seconds": 42, ... } }
```

### Users
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/users` | List all users |
| `GET` | `/api/users/:id` | Get user by ID |
| `POST` | `/api/users` | Create a user — returns 201 |

```bash
# List users
curl http://localhost:3000/api/users

# Get user by ID
curl http://localhost:3000/api/users/1

# Create user
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "role": "admin"}'
```

### Tasks
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/tasks` | List tasks; optional query params `status` and `userId` |
| `PUT` | `/api/tasks/:id` | Partial update a task (title, status, userId — all optional) |
| `POST` | `/api/tasks` | Create a task — returns 201 |

```bash
# All tasks
curl http://localhost:3000/api/tasks

# Filter by status
curl "http://localhost:3000/api/tasks?status=pending"

# Filter by user
curl "http://localhost:3000/api/tasks?userId=1"

# Create task
curl -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Fix bug", "status": "pending", "userId": 1}'

# Update task status
curl -X PUT http://localhost:3000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

### Statistics
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/stats` | Aggregated counts from the Python backend |

```bash
curl http://localhost:3000/api/stats
```

### Metrics
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/metrics` | Request metrics collected by the Python backend (total, errors, response times, by method/status) |

```bash
curl http://localhost:3000/api/metrics
```

## Project Structure

```
node-backend/
├── app.js                  # Express entry point, CORS, body parser
├── config/
│   └── index.js            # Reads env vars (PORT, GO_BACKEND_URL, PYTHON_API_KEY)
├── routes/
│   ├── index.js            # Mounts all sub-routers
│   ├── health.js
│   ├── users.js
│   ├── tasks.js
│   ├── stats.js
│   ├── products.js
│   └── metrics.js
├── controllers/
│   ├── userController.js
│   ├── taskController.js
│   ├── statsController.js
│   └── metricsController.js
└── utils/
    └── httpClient.js       # All HTTP calls to Python; injects X-API-Key header
```

## Error Handling

`httpClient.js` parses Python's `{"detail": "..."}` error shape (including array-of-strings form from Pydantic validation) and re-throws with a plain `message` string. Controllers let unhandled errors bubble up; Express's default error handler returns a JSON error to the frontend.

## Starting with API Key Authentication

```bash
# Terminal 1 — Python backend (key enforced)
cd ../python-backend
API_KEYS=mykey123 python -m app.main

# Terminal 2 — Node.js backend (key forwarded)
PYTHON_API_KEY=mykey123 npm start
```

Without `PYTHON_API_KEY` set the header is omitted and Python returns 401 for every request (except `/health` and `/metrics` which are always public).
