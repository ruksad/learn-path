# React Frontend

Vite + React single-page application that provides a full UI for the three-tier stack.

## Architecture

```
React (5173) → Node.js (3000) → Python (8080)
```

All API calls go through `src/services/api.js` which targets the Node.js backend. The frontend never talks to Python directly and never holds the API key.

## Setup

```bash
npm install
npm run dev       # dev server with HMR at http://localhost:5173
npm run build     # production build → dist/
npm run preview   # preview the production build locally
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:3000` | Node.js backend URL |

Create a `.env` file to override:

```env
VITE_API_URL=http://localhost:3000
```

> The API key (`X-API-Key`) is **not** set here — it is injected server-side by Node.js. Never put secrets in `VITE_` env vars; they are visible in the browser bundle.

## Features

### Health Status
Displayed at the top of the page on every load. Shows:
- Node.js gateway status
- Python backend status, uptime, and live store counts (users / tasks)

### Backend Metrics Panel
Live observability data from Python's `/metrics` endpoint:
- Total request count, 4xx errors, 5xx errors, server uptime
- Average / min / max response times in ms
- Per-method bar chart (GET, POST, PUT, …)
- Per-status-code coloured pills
- Manual refresh button

### Users
- Inline **Add User** form (collapsible) — fields: name, email, role
- User list with click-to-select; selected user's details shown below the list
- Stats panel updates immediately after a user is created

### Tasks
- Inline **Add Task** form (collapsible) — fields: title, status, assigned user (select from live user list)
- Task list with filter buttons: All / Pending / In Progress / Completed
- Inline status dropdown on each task card — changes are PUT to the backend immediately, with a "saving…" indicator and per-card error display
- Stats panel updates immediately after a task is created

### Statistics
Aggregated counts panel: total users, total tasks, breakdown by status.

## Project Structure

```
react-frontend/
├── index.html
├── vite.config.js
├── src/
│   ├── main.jsx
│   ├── App.jsx                     # Root component; owns all state and handlers
│   ├── App.css
│   ├── services/
│   │   └── api.js                  # All axios calls; centralised error normalisation
│   └── components/
│       ├── HealthStatus.jsx / .css  # Health bar with Python detail pills
│       ├── Metrics.jsx / .css       # Metrics panel with cards, bar chart, pills
│       ├── CreateUserForm.jsx / .css # Collapsible user creation form
│       ├── CreateTaskForm.jsx / .css # Collapsible task creation form (needs user list)
│       ├── UserList.jsx / .css
│       ├── TaskList.jsx / .css      # TaskCard with inline status update dropdown
│       └── Stats.jsx / .css
```

## API Service (`src/services/api.js`)

All calls return plain data (no `response.data` unwrapping at call sites). Errors are normalised to a single `Error` with a `message` string — including Python's `{"detail": "..."}` and Pydantic's `{"detail": [...]}` array form.

| Function | Method | Path |
|---|---|---|
| `checkHealth()` | GET | `/health` |
| `getMetrics()` | GET | `/api/metrics` |
| `getUsers()` | GET | `/api/users` |
| `getUserById(id)` | GET | `/api/users/:id` |
| `createUser({name, email, role})` | POST | `/api/users` |
| `getTasks(status?, userId?)` | GET | `/api/tasks` |
| `createTask({title, status, userId})` | POST | `/api/tasks` |
| `updateTask(id, fields)` | PUT | `/api/tasks/:id` |
| `getStats()` | GET | `/api/stats` |

## State Flow

```
App.jsx
 ├── loadInitialData()   — health + users + tasks + stats + metrics (parallel)
 ├── handleUserCreated() — appends user, refreshes stats + metrics
 ├── handleTaskCreated() — appends task, refreshes stats + metrics
 ├── handleTaskUpdated() — patches single task in list (no refetch)
 ├── handleUserSelect()  — fetches user detail + filters tasks by userId
 └── handleTaskFilter()  — refetches tasks with status query param
```

## Starting the Full Stack

```bash
# Terminal 1 — Python backend
cd ../python-backend
API_KEYS=mykey123 python -m app.main

# Terminal 2 — Node.js backend
cd ../node-backend
PYTHON_API_KEY=mykey123 npm start

# Terminal 3 — React frontend
npm run dev
```

Open `http://localhost:5173`.
