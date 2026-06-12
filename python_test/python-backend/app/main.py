from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import List, Optional, Union
from threading import RLock
from collections import deque
import json
import os
import re
import sqlite3
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_PORT = 8080
_START_TIME = time.monotonic()
_STATS_CACHE_TTL = 30.0  # seconds

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_VALID_ROLES = {"developer", "designer", "manager", "admin", "qa"}
_VALID_STATUSES = {"pending", "in-progress", "completed"}

# Per-IP sliding-window rate-limit buckets. Replaced in tests via monkeypatch.
_rate_buckets: dict = {}
_rate_lock = RLock()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class MetricsCollector:
    """Thread-safe request counter and response-time tracker."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._total: int = 0
        self._by_status: dict = {}
        self._by_method: dict = {}
        self._times: list = []
        self._max_samples = 1000  # cap memory use

    def record(self, method: str, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self._total += 1
            self._by_status[status_code] = self._by_status.get(status_code, 0) + 1
            self._by_method[method] = self._by_method.get(method, 0) + 1
            self._times.append(duration_ms)
            if len(self._times) > self._max_samples:
                self._times.pop(0)

    def snapshot(self) -> dict:
        with self._lock:
            times = self._times or [0.0]
            return {
                "total_requests": self._total,
                "by_status": {str(k): v for k, v in sorted(self._by_status.items())},
                "by_method": dict(sorted(self._by_method.items())),
                "errors_4xx": sum(v for k, v in self._by_status.items() if 400 <= k < 500),
                "errors_5xx": sum(v for k, v in self._by_status.items() if k >= 500),
                "response_times_ms": {
                    "avg": round(sum(times) / len(times), 2),
                    "min": round(min(times), 2),
                    "max": round(max(times), 2),
                    "samples": len(times),
                },
            }


# Module-level singleton — replaceable via monkeypatch in tests.
metrics = MetricsCollector()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(BaseModel):
    id: int
    name: str
    email: str
    role: str


class CreateUserRequest(BaseModel):
    name: str
    email: str
    role: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("email is not a valid email address")
        return v

    @field_validator("role")
    @classmethod
    def role_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in _VALID_ROLES:
            raise ValueError(f"role must be one of: {', '.join(sorted(_VALID_ROLES))}")
        return v


class Task(BaseModel):
    id: int
    title: str
    status: str
    userId: int


class CreateTaskRequest(BaseModel):
    title: str
    status: str
    userId: int

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: str) -> str:
        if v not in _VALID_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}")
        return v

    @field_validator("userId")
    @classmethod
    def user_id_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("userId must be a positive integer")
        return v


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    userId: Optional[int] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("title must not be blank")
        return v

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}")
        return v

    @field_validator("userId")
    @classmethod
    def user_id_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("userId must be a positive integer")
        return v


class UsersResponse(BaseModel):
    users: List[User]
    count: int


class TasksResponse(BaseModel):
    tasks: List[Task]
    count: int


class UsersStats(BaseModel):
    total: int


class TasksStats(BaseModel):
    total: int
    pending: int
    inProgress: int
    completed: int


class StatsResponse(BaseModel):
    users: UsersStats
    tasks: TasksStats


class HealthResponse(BaseModel):
    status: str
    message: str
    uptime_seconds: float
    store_users: int
    store_tasks: int


# ---------------------------------------------------------------------------
# DataStore — in-memory with optional JSON file persistence
# ---------------------------------------------------------------------------

class DataStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._data_file: str = os.getenv("DATA_FILE", "data/store.json")
        self._users: List[User] = [
            User(id=1, name="John Doe", email="john@example.com", role="developer"),
            User(id=2, name="Jane Smith", email="jane@example.com", role="designer"),
            User(id=3, name="Bob Johnson", email="bob@example.com", role="manager"),
        ]
        self._tasks: List[Task] = [
            Task(id=1, title="Implement authentication", status="pending", userId=1),
            Task(id=2, title="Design user interface", status="in-progress", userId=2),
            Task(id=3, title="Review code changes", status="completed", userId=3),
        ]
        self._stats_cache: Optional[StatsResponse] = None
        self._stats_cache_expiry: float = 0.0
        self._load()

    def _load(self) -> None:
        if not self._data_file or not os.path.exists(self._data_file):
            return
        try:
            with open(self._data_file, "r") as f:
                data = json.load(f)
            self._users = [User(**u) for u in data.get("users", [])]
            self._tasks = [Task(**t) for t in data.get("tasks", [])]
            logger.info("Loaded persisted data from %s", self._data_file)
        except Exception:
            logger.warning("Could not load %s — using seed data", self._data_file, exc_info=True)

    def _save(self) -> None:
        """Flush state to disk. Must be called while holding self._lock."""
        if not self._data_file:
            return
        try:
            directory = os.path.dirname(self._data_file)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(self._data_file, "w") as f:
                json.dump(
                    {
                        "users": [u.model_dump() for u in self._users],
                        "tasks": [t.model_dump() for t in self._tasks],
                    },
                    f,
                    indent=2,
                )
        except Exception:
            logger.error("Failed to persist data to %s", self._data_file, exc_info=True)

    def _invalidate_stats_cache(self) -> None:
        self._stats_cache = None
        self._stats_cache_expiry = 0.0

    def create_user(self, name: str, email: str, role: str) -> User:
        with self._lock:
            for u in self._users:
                if u.email == email:
                    raise ValueError(f"email '{email}' is already in use")
            new_id = max((u.id for u in self._users), default=0) + 1
            user = User(id=new_id, name=name, email=email, role=role)
            self._users.append(user)
            self._invalidate_stats_cache()
            self._save()
            return user

    def get_users(self) -> List[User]:
        with self._lock:
            return list(self._users)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        with self._lock:
            for user in self._users:
                if user.id == user_id:
                    return user
        return None

    def create_task(self, title: str, status: str, user_id: int) -> Task:
        with self._lock:
            if not any(u.id == user_id for u in self._users):
                raise ValueError(f"user with id {user_id} does not exist")
            new_id = max((t.id for t in self._tasks), default=0) + 1
            task = Task(id=new_id, title=title, status=status, userId=user_id)
            self._tasks.append(task)
            self._invalidate_stats_cache()
            self._save()
            return task

    def update_task(
        self,
        task_id: int,
        title: Optional[str],
        status: Optional[str],
        user_id: Optional[int],
    ) -> Optional[Task]:
        with self._lock:
            for i, task in enumerate(self._tasks):
                if task.id != task_id:
                    continue
                if user_id is not None and not any(u.id == user_id for u in self._users):
                    raise ValueError(f"user with id {user_id} does not exist")
                updates: dict = {}
                if title is not None:
                    updates["title"] = title
                if status is not None:
                    updates["status"] = status
                if user_id is not None:
                    updates["userId"] = user_id
                updated = task.model_copy(update=updates)
                self._tasks[i] = updated
                self._invalidate_stats_cache()
                self._save()
                return updated
            return None

    def get_tasks(self, status: str = "", user_id: str = "") -> List[Task]:
        with self._lock:
            filtered: List[Task] = []
            for task in self._tasks:
                match_status = not status or task.status == status
                match_user_id = True
                if user_id:
                    try:
                        uid = int(user_id)
                        match_user_id = task.userId == uid
                    except ValueError:
                        match_user_id = False
                if match_status and match_user_id:
                    filtered.append(task)
            return filtered

    def get_stats(self) -> StatsResponse:
        with self._lock:
            now = time.monotonic()
            if self._stats_cache is not None and now < self._stats_cache_expiry:
                return self._stats_cache
            users_total = len(self._users)
            tasks_total = len(self._tasks)
            pending = in_progress = completed = 0
            for task in self._tasks:
                if task.status == "pending":
                    pending += 1
                elif task.status == "in-progress":
                    in_progress += 1
                elif task.status == "completed":
                    completed += 1
            result = StatsResponse(
                users=UsersStats(total=users_total),
                tasks=TasksStats(
                    total=tasks_total,
                    pending=pending,
                    inProgress=in_progress,
                    completed=completed,
                ),
            )
            self._stats_cache = result
            self._stats_cache_expiry = now + _STATS_CACHE_TTL
            return result


# ---------------------------------------------------------------------------
# SQLiteDataStore — full SQLite backend, same public interface as DataStore
# ---------------------------------------------------------------------------

class SQLiteDataStore:
    """Persistent store backed by SQLite. Drop-in replacement for DataStore."""

    def __init__(self, db_path: str) -> None:
        self._lock = RLock()
        self._db_path = db_path
        if db_path not in (":memory:", ""):
            directory = os.path.dirname(db_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        # WAL mode allows concurrent reads alongside a single writer.
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()
        self._seed_if_empty()
        self._stats_cache: Optional[StatsResponse] = None
        self._stats_cache_expiry: float = 0.0
        logger.info("SQLite store initialised at '%s'", db_path)

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    name  TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    role  TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    title   TEXT NOT NULL,
                    status  TEXT NOT NULL,
                    user_id INTEGER NOT NULL REFERENCES users(id)
                );
            """)

    def _seed_if_empty(self) -> None:
        with self._lock:
            if self._conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
                return
            self._conn.executemany(
                "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
                [
                    ("John Doe", "john@example.com", "developer"),
                    ("Jane Smith", "jane@example.com", "designer"),
                    ("Bob Johnson", "bob@example.com", "manager"),
                ],
            )
            self._conn.executemany(
                "INSERT INTO tasks (title, status, user_id) VALUES (?, ?, ?)",
                [
                    ("Implement authentication", "pending", 1),
                    ("Design user interface", "in-progress", 2),
                    ("Review code changes", "completed", 3),
                ],
            )
            self._conn.commit()

    def _invalidate_stats_cache(self) -> None:
        self._stats_cache = None
        self._stats_cache_expiry = 0.0

    def create_user(self, name: str, email: str, role: str) -> User:
        with self._lock:
            if self._conn.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone():
                raise ValueError(f"email '{email}' is already in use")
            cursor = self._conn.execute(
                "INSERT INTO users (name, email, role) VALUES (?, ?, ?)", (name, email, role)
            )
            self._conn.commit()
            self._invalidate_stats_cache()
            return User(id=cursor.lastrowid, name=name, email=email, role=role)

    def get_users(self) -> List[User]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, name, email, role FROM users ORDER BY id"
            ).fetchall()
            return [User(id=r[0], name=r[1], email=r[2], role=r[3]) for r in rows]

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, name, email, role FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return User(id=row[0], name=row[1], email=row[2], role=row[3]) if row else None

    def create_task(self, title: str, status: str, user_id: int) -> Task:
        with self._lock:
            if not self._conn.execute(
                "SELECT id FROM users WHERE id = ?", (user_id,)
            ).fetchone():
                raise ValueError(f"user with id {user_id} does not exist")
            cursor = self._conn.execute(
                "INSERT INTO tasks (title, status, user_id) VALUES (?, ?, ?)",
                (title, status, user_id),
            )
            self._conn.commit()
            self._invalidate_stats_cache()
            return Task(id=cursor.lastrowid, title=title, status=status, userId=user_id)

    def update_task(
        self,
        task_id: int,
        title: Optional[str],
        status: Optional[str],
        user_id: Optional[int],
    ) -> Optional[Task]:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, title, status, user_id FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if row is None:
                return None
            if user_id is not None and not self._conn.execute(
                "SELECT id FROM users WHERE id = ?", (user_id,)
            ).fetchone():
                raise ValueError(f"user with id {user_id} does not exist")
            new_title = title if title is not None else row[1]
            new_status = status if status is not None else row[2]
            new_user_id = user_id if user_id is not None else row[3]
            self._conn.execute(
                "UPDATE tasks SET title = ?, status = ?, user_id = ? WHERE id = ?",
                (new_title, new_status, new_user_id, task_id),
            )
            self._conn.commit()
            self._invalidate_stats_cache()
            return Task(id=task_id, title=new_title, status=new_status, userId=new_user_id)

    def get_tasks(self, status: str = "", user_id: str = "") -> List[Task]:
        with self._lock:
            query = "SELECT id, title, status, user_id FROM tasks WHERE 1=1"
            params: list = []
            if status:
                query += " AND status = ?"
                params.append(status)
            if user_id:
                try:
                    uid = int(user_id)
                    query += " AND user_id = ?"
                    params.append(uid)
                except ValueError:
                    return []
            rows = self._conn.execute(query, params).fetchall()
            return [Task(id=r[0], title=r[1], status=r[2], userId=r[3]) for r in rows]

    def get_stats(self) -> StatsResponse:
        with self._lock:
            now = time.monotonic()
            if self._stats_cache is not None and now < self._stats_cache_expiry:
                return self._stats_cache
            users_total = self._conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            counts = dict(
                self._conn.execute(
                    "SELECT status, COUNT(*) FROM tasks GROUP BY status"
                ).fetchall()
            )
            tasks_total = sum(counts.values())
            result = StatsResponse(
                users=UsersStats(total=users_total),
                tasks=TasksStats(
                    total=tasks_total,
                    pending=counts.get("pending", 0),
                    inProgress=counts.get("in-progress", 0),
                    completed=counts.get("completed", 0),
                ),
            )
            self._stats_cache = result
            self._stats_cache_expiry = now + _STATS_CACHE_TTL
            return result


# ---------------------------------------------------------------------------
# Store factory
# ---------------------------------------------------------------------------

def create_store() -> Union[DataStore, SQLiteDataStore]:
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("sqlite:///"):
        path = db_url[len("sqlite:///"):]
        return SQLiteDataStore(path)
    return DataStore()


store: Union[DataStore, SQLiteDataStore] = create_store()


# ---------------------------------------------------------------------------
# App & exception handlers
# ---------------------------------------------------------------------------

app = FastAPI(title="Python Backend Test Project")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = [f"{' -> '.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in exc.errors()]
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, errors)
    return JSONResponse(status_code=400, content={"detail": errors})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    # Log full traceback but never expose internal detail to callers.
    logger.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ---------------------------------------------------------------------------
# Middleware
#
# FastAPI applies @app.middleware decorators in REVERSE definition order:
# last-defined = outermost (processes request first, response last).
#
# Execution order (outermost → innermost):
#   log_requests_and_metrics → check_api_key → check_rate_limit → require_json_content_type
#
# This means auth/rate/CT rejections are all timed and counted by the
# outermost layer.
# ---------------------------------------------------------------------------

@app.middleware("http")
async def require_json_content_type(request: Request, call_next):
    if request.method in ("POST", "PUT"):
        ct = request.headers.get("content-type", "")
        if not ct.startswith("application/json"):
            logger.warning(
                "Rejected %s %s — Content-Type '%s' is not application/json",
                request.method, request.url.path, ct,
            )
            return JSONResponse(
                status_code=415,
                content={"detail": "Content-Type must be application/json"},
            )
    return await call_next(request)


@app.middleware("http")
async def check_rate_limit(request: Request, call_next):
    limit = int(os.getenv("RATE_LIMIT_REQUESTS", "0"))
    if limit <= 0:
        return await call_next(request)

    window = float(os.getenv("RATE_LIMIT_WINDOW", "60"))
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()

    with _rate_lock:
        if client_ip not in _rate_buckets:
            _rate_buckets[client_ip] = deque()
        bucket = _rate_buckets[client_ip]
        # Evict timestamps that have fallen outside the window.
        while bucket and bucket[0] < now - window:
            bucket.popleft()
        if len(bucket) >= limit:
            logger.warning(
                "Rate limit exceeded for %s on %s %s (%d/%d in %.0fs)",
                client_ip, request.method, request.url.path, len(bucket), limit, window,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests — please slow down"},
                headers={"Retry-After": str(int(window))},
            )
        bucket.append(now)

    return await call_next(request)


@app.middleware("http")
async def check_api_key(request: Request, call_next):
    raw = os.getenv("API_KEYS", "")
    if not raw:
        # Auth is disabled when API_KEYS is not configured.
        return await call_next(request)

    # /health and /metrics are always public so monitoring tools work without a key.
    if request.url.path in ("/health", "/metrics"):
        return await call_next(request)

    api_keys = frozenset(k.strip() for k in raw.split(",") if k.strip())
    provided = request.headers.get("X-API-Key", "")

    if not provided:
        logger.warning("Missing X-API-Key on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=401, content={"detail": "Missing X-API-Key header"})

    if provided not in api_keys:
        logger.warning("Invalid X-API-Key on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=403, content={"detail": "Invalid API key"})

    return await call_next(request)


@app.middleware("http")
async def log_requests_and_metrics(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    logger.info(
        "%s %s %d %.1fms",
        request.method, request.url.path, response.status_code, duration_ms,
    )
    metrics.record(request.method, response.status_code, duration_ms)
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        message="Python backend is running",
        uptime_seconds=round(time.monotonic() - _START_TIME, 1),
        store_users=len(store.get_users()),
        store_tasks=len(store.get_tasks()),
    )


@app.get("/metrics")
async def get_metrics() -> dict:
    snap = metrics.snapshot()
    return {
        "uptime_seconds": round(time.monotonic() - _START_TIME, 1),
        "requests": snap,
        "store": {
            "users": len(store.get_users()),
            "tasks": len(store.get_tasks()),
        },
    }


@app.post("/api/users", response_model=User, status_code=201)
async def create_user(body: CreateUserRequest) -> User:
    """Create a new user. Returns 400 on validation errors or duplicate email."""
    try:
        return store.create_user(name=body.name, email=body.email, role=body.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/users", response_model=UsersResponse)
async def get_users() -> UsersResponse:
    users = store.get_users()
    return UsersResponse(users=users, count=len(users))


@app.get("/api/users/{user_id}", response_model=User)
async def get_user_by_id(user_id: int) -> User:
    user = store.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/api/tasks", response_model=Task, status_code=201)
async def create_task(body: CreateTaskRequest) -> Task:
    """Create a new task. Returns 400 if userId does not exist or input is invalid."""
    try:
        return store.create_task(title=body.title, status=body.status, user_id=body.userId)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/tasks", response_model=TasksResponse)
async def get_tasks(status: str = "", userId: str = "") -> TasksResponse:  # noqa: N803
    tasks = store.get_tasks(status=status, user_id=userId)
    return TasksResponse(tasks=tasks, count=len(tasks))


@app.put("/api/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, body: UpdateTaskRequest) -> Task:
    """Partially update a task. Returns 404 if not found, 400 for invalid fields."""
    try:
        updated = store.update_task(
            task_id=task_id,
            title=body.title,
            status=body.status,
            user_id=body.userId,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    return store.get_stats()


# ---------------------------------------------------------------------------
# Startup helpers
# ---------------------------------------------------------------------------

def get_port() -> int:
    port_str = os.getenv("PORT", str(DEFAULT_PORT))
    try:
        return int(port_str)
    except ValueError:
        return DEFAULT_PORT


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=get_port(), reload=False)
