"""Tests for Phase 3 features: enhanced health, content-type middleware, caching, persistence."""
import json
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import DataStore, _STATS_CACHE_TTL


# ---------------------------------------------------------------------------
# Enhanced health check
# ---------------------------------------------------------------------------

def test_health_returns_200(client: TestClient) -> None:
    assert client.get("/health").status_code == 200


def test_health_has_uptime_seconds(client: TestClient) -> None:
    body = client.get("/health").json()
    assert "uptime_seconds" in body
    assert isinstance(body["uptime_seconds"], float)
    assert body["uptime_seconds"] >= 0


def test_health_has_store_users(client: TestClient) -> None:
    body = client.get("/health").json()
    assert "store_users" in body
    assert body["store_users"] == 3  # seed data


def test_health_has_store_tasks(client: TestClient) -> None:
    body = client.get("/health").json()
    assert "store_tasks" in body
    assert body["store_tasks"] == 3  # seed data


def test_health_store_users_increases_after_create(client: TestClient) -> None:
    before = client.get("/health").json()["store_users"]
    client.post("/api/users", json={"name": "New", "email": "new@x.com", "role": "developer"})
    assert client.get("/health").json()["store_users"] == before + 1


def test_health_store_tasks_increases_after_create(client: TestClient) -> None:
    before = client.get("/health").json()["store_tasks"]
    client.post("/api/tasks", json={"title": "T", "status": "pending", "userId": 1})
    assert client.get("/health").json()["store_tasks"] == before + 1


# ---------------------------------------------------------------------------
# Content-Type middleware (415)
# ---------------------------------------------------------------------------

def test_post_without_json_content_type_returns_415(client: TestClient) -> None:
    resp = client.post(
        "/api/users",
        content=b'{"name":"A","email":"a@x.com","role":"developer"}',
        headers={"Content-Type": "text/plain"},
    )
    assert resp.status_code == 415


def test_post_with_form_content_type_returns_415(client: TestClient) -> None:
    resp = client.post(
        "/api/tasks",
        content=b"title=T&status=pending&userId=1",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 415


def test_put_without_json_content_type_returns_415(client: TestClient) -> None:
    resp = client.put(
        "/api/tasks/1",
        content=b'{"status":"completed"}',
        headers={"Content-Type": "text/plain"},
    )
    assert resp.status_code == 415


def test_415_response_has_meaningful_detail(client: TestClient) -> None:
    resp = client.post(
        "/api/users",
        content=b"{}",
        headers={"Content-Type": "text/plain"},
    )
    assert "application/json" in resp.json()["detail"]


def test_get_requests_do_not_require_content_type(client: TestClient) -> None:
    # GET /api/users should work fine with no Content-Type header
    assert client.get("/api/users").status_code == 200


def test_post_with_json_content_type_passes_middleware(client: TestClient) -> None:
    resp = client.post(
        "/api/users",
        json={"name": "A", "email": "a@x.com", "role": "developer"},
    )
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Stats caching
# ---------------------------------------------------------------------------

def test_stats_cache_returns_same_object_on_repeat_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_FILE", "")
    store = DataStore()
    result1 = store.get_stats()
    result2 = store.get_stats()
    # Second call must return the cached object (same identity)
    assert result1 is result2


def test_stats_cache_is_invalidated_after_create_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_FILE", "")
    store = DataStore()
    result1 = store.get_stats()
    store.create_task("New task", "pending", user_id=1)
    result2 = store.get_stats()
    # A new task was created so the cache must have been rebuilt
    assert result1 is not result2
    assert result2.tasks.total == result1.tasks.total + 1


def test_stats_cache_is_invalidated_after_create_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_FILE", "")
    store = DataStore()
    result1 = store.get_stats()
    store.create_user("New", "new@x.com", "developer")
    result2 = store.get_stats()
    assert result1 is not result2
    assert result2.users.total == result1.users.total + 1


def test_stats_cache_is_invalidated_after_update_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_FILE", "")
    store = DataStore()
    result1 = store.get_stats()
    store.update_task(1, title=None, status="completed", user_id=None)
    result2 = store.get_stats()
    assert result1 is not result2


def test_stats_cache_expires_after_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_FILE", "")
    store = DataStore()
    result1 = store.get_stats()
    # Force-expire the cache by rewinding the expiry time
    store._stats_cache_expiry = time.monotonic() - 1.0
    result2 = store.get_stats()
    assert result1 is not result2


# ---------------------------------------------------------------------------
# JSON persistence
# ---------------------------------------------------------------------------

def test_persist_new_user_survives_reload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data_file = str(tmp_path / "store.json")
    monkeypatch.setenv("DATA_FILE", data_file)

    store1 = DataStore()
    store1.create_user("Persisted", "persisted@x.com", "developer")

    # Create a fresh DataStore that reads the same file
    store2 = DataStore()
    emails = [u.email for u in store2.get_users()]
    assert "persisted@x.com" in emails


def test_persist_new_task_survives_reload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data_file = str(tmp_path / "store.json")
    monkeypatch.setenv("DATA_FILE", data_file)

    store1 = DataStore()
    store1.create_task("Persisted task", "pending", user_id=1)

    store2 = DataStore()
    titles = [t.title for t in store2.get_tasks()]
    assert "Persisted task" in titles


def test_persist_updated_task_survives_reload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data_file = str(tmp_path / "store.json")
    monkeypatch.setenv("DATA_FILE", data_file)

    store1 = DataStore()
    store1.update_task(1, title=None, status="completed", user_id=None)

    store2 = DataStore()
    task = next(t for t in store2.get_tasks() if t.id == 1)
    assert task.status == "completed"


def test_persist_data_file_is_valid_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data_file = str(tmp_path / "store.json")
    monkeypatch.setenv("DATA_FILE", data_file)

    store = DataStore()
    store.create_user("A", "a@x.com", "developer")

    with open(data_file) as f:
        data = json.load(f)
    assert "users" in data
    assert "tasks" in data


def test_persist_missing_file_falls_back_to_seed_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data_file = str(tmp_path / "nonexistent.json")
    monkeypatch.setenv("DATA_FILE", data_file)

    store = DataStore()
    # Should have the 3 seed users even though no file exists
    assert len(store.get_users()) == 3


def test_persist_data_file_created_in_subdirectory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data_file = str(tmp_path / "subdir" / "store.json")
    monkeypatch.setenv("DATA_FILE", data_file)

    store = DataStore()
    store.create_user("A", "a@x.com", "developer")

    assert os.path.exists(data_file)
