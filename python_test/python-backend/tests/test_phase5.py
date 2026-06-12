"""Tests for Phase 5 features: API key auth, rate limiting, metrics, SQLite store."""
import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app, DataStore, MetricsCollector, SQLiteDataStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _authed_client(monkeypatch: pytest.MonkeyPatch, key: str = "test-key") -> TestClient:
    monkeypatch.setenv("DATA_FILE", "")
    monkeypatch.setenv("API_KEYS", key)
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "0")
    monkeypatch.setattr(main_module, "store", DataStore())
    monkeypatch.setattr(main_module, "metrics", MetricsCollector())
    monkeypatch.setattr(main_module, "_rate_buckets", {})
    return TestClient(app)


def _rate_limited_client(
    monkeypatch: pytest.MonkeyPatch, limit: int = 3, window: int = 60
) -> TestClient:
    monkeypatch.setenv("DATA_FILE", "")
    monkeypatch.setenv("API_KEYS", "")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", str(limit))
    monkeypatch.setenv("RATE_LIMIT_WINDOW", str(window))
    monkeypatch.setattr(main_module, "store", DataStore())
    monkeypatch.setattr(main_module, "metrics", MetricsCollector())
    monkeypatch.setattr(main_module, "_rate_buckets", {})
    return TestClient(app)


# ---------------------------------------------------------------------------
# API key authentication
# ---------------------------------------------------------------------------

def test_api_request_without_key_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _authed_client(monkeypatch)
    assert client.get("/api/users").status_code == 401


def test_api_request_with_invalid_key_returns_403(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _authed_client(monkeypatch, key="secret")
    resp = client.get("/api/users", headers={"X-API-Key": "wrong"})
    assert resp.status_code == 403


def test_api_request_with_valid_key_returns_200(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _authed_client(monkeypatch, key="secret")
    resp = client.get("/api/users", headers={"X-API-Key": "secret"})
    assert resp.status_code == 200


def test_multiple_valid_keys_any_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _authed_client(monkeypatch, key="key1,key2,key3")
    for key in ("key1", "key2", "key3"):
        assert client.get("/api/users", headers={"X-API-Key": key}).status_code == 200


def test_health_does_not_require_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _authed_client(monkeypatch)
    assert client.get("/health").status_code == 200


def test_metrics_does_not_require_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _authed_client(monkeypatch)
    assert client.get("/metrics").status_code == 200


def test_auth_disabled_when_api_keys_env_not_set(client: TestClient) -> None:
    # The base client fixture sets API_KEYS="" which disables auth.
    assert client.get("/api/users").status_code == 200


def test_401_detail_mentions_header_name(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _authed_client(monkeypatch)
    assert "X-API-Key" in client.get("/api/users").json()["detail"]


def test_post_with_valid_key_creates_user(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _authed_client(monkeypatch, key="secret")
    resp = client.post(
        "/api/users",
        json={"name": "A", "email": "a@x.com", "role": "developer"},
        headers={"X-API-Key": "secret"},
    )
    assert resp.status_code == 201


def test_post_without_key_returns_401_not_400(monkeypatch: pytest.MonkeyPatch) -> None:
    # Auth check runs before Content-Type check, so missing key → 401, not 415.
    client = _authed_client(monkeypatch)
    resp = client.post("/api/users", content=b"{}", headers={"Content-Type": "text/plain"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def test_requests_under_limit_are_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _rate_limited_client(monkeypatch, limit=5)
    for _ in range(5):
        assert client.get("/api/users").status_code == 200


def test_request_over_limit_returns_429(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _rate_limited_client(monkeypatch, limit=3)
    for _ in range(3):
        client.get("/api/users")
    assert client.get("/api/users").status_code == 429


def test_429_has_retry_after_header(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _rate_limited_client(monkeypatch, limit=2, window=30)
    client.get("/api/users")
    client.get("/api/users")
    resp = client.get("/api/users")
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
    assert resp.headers["Retry-After"] == "30"


def test_429_has_meaningful_detail(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _rate_limited_client(monkeypatch, limit=1)
    client.get("/api/users")
    resp = client.get("/api/users")
    assert "too many" in resp.json()["detail"].lower()


def test_rate_limit_disabled_by_default(client: TestClient) -> None:
    # The base client fixture sets RATE_LIMIT_REQUESTS=0 which disables limiting.
    for _ in range(20):
        assert client.get("/api/users").status_code == 200


# ---------------------------------------------------------------------------
# Metrics endpoint
# ---------------------------------------------------------------------------

def test_metrics_returns_200(client: TestClient) -> None:
    assert client.get("/metrics").status_code == 200


def test_metrics_has_required_top_level_keys(client: TestClient) -> None:
    body = client.get("/metrics").json()
    assert "uptime_seconds" in body
    assert "requests" in body
    assert "store" in body


def test_metrics_requests_has_expected_keys(client: TestClient) -> None:
    body = client.get("/metrics").json()["requests"]
    for key in ("total_requests", "by_status", "by_method", "errors_4xx", "errors_5xx", "response_times_ms"):
        assert key in body, f"missing key: {key}"


def test_metrics_total_increases_after_requests(client: TestClient) -> None:
    before = client.get("/metrics").json()["requests"]["total_requests"]
    client.get("/api/users")
    client.get("/api/users")
    after = client.get("/metrics").json()["requests"]["total_requests"]
    assert after >= before + 2


def test_metrics_tracks_200_status(client: TestClient) -> None:
    client.get("/api/users")
    body = client.get("/metrics").json()["requests"]
    assert "200" in body["by_status"]


def test_metrics_tracks_404_status(client: TestClient) -> None:
    client.get("/api/users/9999")
    body = client.get("/metrics").json()["requests"]
    assert "404" in body["by_status"]
    assert body["errors_4xx"] >= 1


def test_metrics_tracks_get_method(client: TestClient) -> None:
    client.get("/api/users")
    body = client.get("/metrics").json()["requests"]
    assert "GET" in body["by_method"]


def test_metrics_response_times_are_non_negative(client: TestClient) -> None:
    client.get("/api/users")
    times = client.get("/metrics").json()["requests"]["response_times_ms"]
    assert times["min"] >= 0
    assert times["max"] >= times["min"]
    assert times["avg"] >= 0


def test_metrics_store_counts_match_data(client: TestClient) -> None:
    store_info = client.get("/metrics").json()["store"]
    assert store_info["users"] == 3  # seed data
    assert store_info["tasks"] == 3  # seed data


# ---------------------------------------------------------------------------
# SQLiteDataStore — same interface as DataStore
# ---------------------------------------------------------------------------

@pytest.fixture()
def sqlite_store() -> SQLiteDataStore:
    """In-memory SQLite store for unit tests — no files, no cleanup needed."""
    return SQLiteDataStore(":memory:")


def test_sqlite_seed_data_loaded(sqlite_store: SQLiteDataStore) -> None:
    assert len(sqlite_store.get_users()) == 3
    assert len(sqlite_store.get_tasks()) == 3


def test_sqlite_create_user_returns_user(sqlite_store: SQLiteDataStore) -> None:
    user = sqlite_store.create_user("Alice", "alice@x.com", "developer")
    assert user.id > 0
    assert user.email == "alice@x.com"


def test_sqlite_create_user_appears_in_get_users(sqlite_store: SQLiteDataStore) -> None:
    sqlite_store.create_user("Alice", "alice@x.com", "developer")
    assert any(u.email == "alice@x.com" for u in sqlite_store.get_users())


def test_sqlite_create_user_duplicate_email_raises(sqlite_store: SQLiteDataStore) -> None:
    sqlite_store.create_user("A", "dup@x.com", "developer")
    with pytest.raises(ValueError, match="already in use"):
        sqlite_store.create_user("B", "dup@x.com", "designer")


def test_sqlite_get_user_by_id_found(sqlite_store: SQLiteDataStore) -> None:
    user = sqlite_store.get_user_by_id(1)
    assert user is not None
    assert user.id == 1


def test_sqlite_get_user_by_id_not_found(sqlite_store: SQLiteDataStore) -> None:
    assert sqlite_store.get_user_by_id(9999) is None


def test_sqlite_create_task_returns_task(sqlite_store: SQLiteDataStore) -> None:
    task = sqlite_store.create_task("New task", "pending", user_id=1)
    assert task.id > 0
    assert task.title == "New task"
    assert task.userId == 1


def test_sqlite_create_task_nonexistent_user_raises(sqlite_store: SQLiteDataStore) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        sqlite_store.create_task("T", "pending", user_id=9999)


def test_sqlite_update_task_status(sqlite_store: SQLiteDataStore) -> None:
    updated = sqlite_store.update_task(1, title=None, status="completed", user_id=None)
    assert updated is not None
    assert updated.status == "completed"


def test_sqlite_update_task_not_found_returns_none(sqlite_store: SQLiteDataStore) -> None:
    assert sqlite_store.update_task(9999, title=None, status="pending", user_id=None) is None


def test_sqlite_update_task_unchanged_fields_preserved(sqlite_store: SQLiteDataStore) -> None:
    original = sqlite_store.get_user_by_id(1)
    tasks_before = [t for t in sqlite_store.get_tasks() if t.id == 1]
    original_title = tasks_before[0].title
    sqlite_store.update_task(1, title=None, status="completed", user_id=None)
    updated = next(t for t in sqlite_store.get_tasks() if t.id == 1)
    assert updated.title == original_title


def test_sqlite_get_tasks_filter_by_status(sqlite_store: SQLiteDataStore) -> None:
    tasks = sqlite_store.get_tasks(status="pending")
    assert all(t.status == "pending" for t in tasks)


def test_sqlite_get_tasks_filter_by_user_id(sqlite_store: SQLiteDataStore) -> None:
    tasks = sqlite_store.get_tasks(user_id="1")
    assert all(t.userId == 1 for t in tasks)


def test_sqlite_get_stats_totals_correct(sqlite_store: SQLiteDataStore) -> None:
    stats = sqlite_store.get_stats()
    assert stats.users.total == len(sqlite_store.get_users())
    assert stats.tasks.total == len(sqlite_store.get_tasks())


def test_sqlite_get_stats_counts_sum_to_total(sqlite_store: SQLiteDataStore) -> None:
    t = sqlite_store.get_stats().tasks
    assert t.pending + t.inProgress + t.completed == t.total


def test_sqlite_persists_across_connections(tmp_path) -> None:
    db_path = str(tmp_path / "test.db")
    store1 = SQLiteDataStore(db_path)
    store1.create_user("Persistent", "p@x.com", "developer")
    store2 = SQLiteDataStore(db_path)
    assert any(u.email == "p@x.com" for u in store2.get_users())


def test_sqlite_via_api_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_FILE", "")
    monkeypatch.setenv("API_KEYS", "")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "0")
    monkeypatch.setattr(main_module, "store", SQLiteDataStore(":memory:"))
    monkeypatch.setattr(main_module, "metrics", MetricsCollector())
    monkeypatch.setattr(main_module, "_rate_buckets", {})
    client = TestClient(app)
    resp = client.post(
        "/api/users",
        json={"name": "SQLite User", "email": "sq@x.com", "role": "developer"},
    )
    assert resp.status_code == 201
    users = client.get("/api/users").json()["users"]
    assert any(u["email"] == "sq@x.com" for u in users)
