from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import List, Optional
from threading import RLock
import os
import re
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_PORT = 8080


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_VALID_ROLES = {"developer", "designer", "manager", "admin", "qa"}


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


class DataStore:
    def __init__(self) -> None:
        self._lock = RLock()
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

    def create_user(self, name: str, email: str, role: str) -> User:
        with self._lock:
            for u in self._users:
                if u.email == email:
                    raise ValueError(f"email '{email}' is already in use")
            new_id = max((u.id for u in self._users), default=0) + 1
            user = User(id=new_id, name=name, email=email, role=role)
            self._users.append(user)
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

            return StatsResponse(
                users=UsersStats(total=users_total),
                tasks=TasksStats(
                    total=tasks_total,
                    pending=pending,
                    inProgress=in_progress,
                    completed=completed,
                ),
            )


store = DataStore()
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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    logger.info(
        "%s %s %d %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", message="Python backend is running")


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


@app.get("/api/tasks", response_model=TasksResponse)
async def get_tasks(status: str = "", userId: str = "") -> TasksResponse:  # noqa: N803
    tasks = store.get_tasks(status=status, user_id=userId)
    return TasksResponse(tasks=tasks, count=len(tasks))


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    return store.get_stats()


def get_port() -> int:
    port_str = os.getenv("PORT", str(DEFAULT_PORT))
    try:
        return int(port_str)
    except ValueError:
        return DEFAULT_PORT


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=get_port(), reload=False)
