"""Integration tests for POST /api/tasks and PUT /api/tasks/{id}."""
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# POST /api/tasks — happy path
# ---------------------------------------------------------------------------

def test_create_task_returns_201(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"title": "New task", "status": "pending", "userId": 1})
    assert resp.status_code == 201


def test_create_task_response_has_expected_fields(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"title": "New task", "status": "pending", "userId": 1})
    body = resp.json()
    assert "id" in body
    assert body["title"] == "New task"
    assert body["status"] == "pending"
    assert body["userId"] == 1


def test_create_task_id_is_positive_integer(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"title": "T", "status": "in-progress", "userId": 2})
    assert isinstance(resp.json()["id"], int)
    assert resp.json()["id"] > 0


def test_create_task_all_valid_statuses_accepted(client: TestClient) -> None:
    for status in ("pending", "in-progress", "completed"):
        resp = client.post("/api/tasks", json={"title": "T", "status": status, "userId": 1})
        assert resp.status_code == 201, f"expected 201 for status={status}"


def test_created_task_appears_in_get_tasks(client: TestClient) -> None:
    client.post("/api/tasks", json={"title": "Visible task", "status": "pending", "userId": 1})
    tasks = client.get("/api/tasks").json()["tasks"]
    assert any(t["title"] == "Visible task" for t in tasks)


def test_create_task_count_increases(client: TestClient) -> None:
    before = client.get("/api/tasks").json()["count"]
    client.post("/api/tasks", json={"title": "Extra", "status": "pending", "userId": 1})
    assert client.get("/api/tasks").json()["count"] == before + 1


# ---------------------------------------------------------------------------
# POST /api/tasks — validation errors (400)
# ---------------------------------------------------------------------------

def test_create_task_missing_title_returns_400(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"status": "pending", "userId": 1})
    assert resp.status_code == 400


def test_create_task_missing_status_returns_400(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"title": "T", "userId": 1})
    assert resp.status_code == 400


def test_create_task_missing_user_id_returns_400(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"title": "T", "status": "pending"})
    assert resp.status_code == 400


def test_create_task_blank_title_returns_400(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"title": "   ", "status": "pending", "userId": 1})
    assert resp.status_code == 400


def test_create_task_invalid_status_returns_400(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"title": "T", "status": "doing", "userId": 1})
    assert resp.status_code == 400


def test_create_task_invalid_status_error_lists_valid_values(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"title": "T", "status": "doing", "userId": 1})
    body = str(resp.json())
    assert "pending" in body


def test_create_task_nonexistent_user_id_returns_400(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"title": "T", "status": "pending", "userId": 9999})
    assert resp.status_code == 400


def test_create_task_nonexistent_user_id_error_is_meaningful(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"title": "T", "status": "pending", "userId": 9999})
    assert "9999" in resp.json()["detail"]


def test_create_task_zero_user_id_returns_400(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"title": "T", "status": "pending", "userId": 0})
    assert resp.status_code == 400


def test_create_task_empty_body_returns_400(client: TestClient) -> None:
    assert client.post("/api/tasks", json={}).status_code == 400


# ---------------------------------------------------------------------------
# PUT /api/tasks/{id} — happy path
# ---------------------------------------------------------------------------

def test_update_task_status_returns_200(client: TestClient) -> None:
    resp = client.put("/api/tasks/1", json={"status": "completed"})
    assert resp.status_code == 200


def test_update_task_status_is_persisted(client: TestClient) -> None:
    client.put("/api/tasks/1", json={"status": "completed"})
    tasks = client.get("/api/tasks").json()["tasks"]
    task = next(t for t in tasks if t["id"] == 1)
    assert task["status"] == "completed"


def test_update_task_title_only(client: TestClient) -> None:
    resp = client.put("/api/tasks/1", json={"title": "Renamed task"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Renamed task"


def test_update_task_user_id_only(client: TestClient) -> None:
    resp = client.put("/api/tasks/1", json={"userId": 2})
    assert resp.status_code == 200
    assert resp.json()["userId"] == 2


def test_update_task_multiple_fields_at_once(client: TestClient) -> None:
    resp = client.put("/api/tasks/1", json={"title": "Updated", "status": "completed", "userId": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Updated"
    assert body["status"] == "completed"
    assert body["userId"] == 2


def test_update_task_unspecified_fields_are_unchanged(client: TestClient) -> None:
    original = client.get("/api/tasks").json()["tasks"]
    task1 = next(t for t in original if t["id"] == 1)
    original_title = task1["title"]

    client.put("/api/tasks/1", json={"status": "completed"})

    tasks = client.get("/api/tasks").json()["tasks"]
    updated = next(t for t in tasks if t["id"] == 1)
    assert updated["title"] == original_title


def test_update_task_empty_body_returns_200_unchanged(client: TestClient) -> None:
    # Empty patch is valid — caller chose to update nothing
    resp = client.put("/api/tasks/1", json={})
    assert resp.status_code == 200


def test_update_task_response_contains_full_task(client: TestClient) -> None:
    body = client.put("/api/tasks/1", json={"status": "in-progress"}).json()
    assert all(k in body for k in ("id", "title", "status", "userId"))


# ---------------------------------------------------------------------------
# PUT /api/tasks/{id} — error cases
# ---------------------------------------------------------------------------

def test_update_task_not_found_returns_404(client: TestClient) -> None:
    resp = client.put("/api/tasks/9999", json={"status": "pending"})
    assert resp.status_code == 404


def test_update_task_not_found_detail_is_meaningful(client: TestClient) -> None:
    resp = client.put("/api/tasks/9999", json={"status": "pending"})
    assert "not found" in resp.json()["detail"].lower()


def test_update_task_invalid_status_returns_400(client: TestClient) -> None:
    resp = client.put("/api/tasks/1", json={"status": "doing"})
    assert resp.status_code == 400


def test_update_task_blank_title_returns_400(client: TestClient) -> None:
    resp = client.put("/api/tasks/1", json={"title": "   "})
    assert resp.status_code == 400


def test_update_task_nonexistent_user_id_returns_400(client: TestClient) -> None:
    resp = client.put("/api/tasks/1", json={"userId": 9999})
    assert resp.status_code == 400


def test_update_task_nonexistent_user_id_error_is_meaningful(client: TestClient) -> None:
    resp = client.put("/api/tasks/1", json={"userId": 9999})
    assert "9999" in resp.json()["detail"]


def test_update_task_zero_user_id_returns_400(client: TestClient) -> None:
    resp = client.put("/api/tasks/1", json={"userId": 0})
    assert resp.status_code == 400
