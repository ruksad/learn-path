"""Integration tests for pre-existing read-only endpoints."""
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

def test_health_returns_200(client: TestClient) -> None:
    assert client.get("/health").status_code == 200


def test_health_response_status_is_ok(client: TestClient) -> None:
    assert client.get("/health").json()["status"] == "ok"


# ---------------------------------------------------------------------------
# GET /api/users/{id}
# ---------------------------------------------------------------------------

def test_get_user_by_id_found_returns_200(client: TestClient) -> None:
    assert client.get("/api/users/1").status_code == 200


def test_get_user_by_id_returns_correct_user(client: TestClient) -> None:
    body = client.get("/api/users/1").json()
    assert body["id"] == 1


def test_get_user_by_id_not_found_returns_404(client: TestClient) -> None:
    assert client.get("/api/users/9999").status_code == 404


def test_get_user_by_id_404_detail_is_meaningful(client: TestClient) -> None:
    resp = client.get("/api/users/9999")
    assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# GET /api/tasks
# ---------------------------------------------------------------------------

def test_get_tasks_returns_200(client: TestClient) -> None:
    assert client.get("/api/tasks").status_code == 200


def test_get_tasks_response_has_tasks_and_count(client: TestClient) -> None:
    body = client.get("/api/tasks").json()
    assert "tasks" in body
    assert "count" in body


def test_get_tasks_count_matches_tasks_list_length(client: TestClient) -> None:
    body = client.get("/api/tasks").json()
    assert body["count"] == len(body["tasks"])


def test_get_tasks_filter_status_pending(client: TestClient) -> None:
    body = client.get("/api/tasks?status=pending").json()
    assert all(t["status"] == "pending" for t in body["tasks"])


def test_get_tasks_filter_status_in_progress(client: TestClient) -> None:
    body = client.get("/api/tasks?status=in-progress").json()
    assert all(t["status"] == "in-progress" for t in body["tasks"])


def test_get_tasks_filter_status_completed(client: TestClient) -> None:
    body = client.get("/api/tasks?status=completed").json()
    assert all(t["status"] == "completed" for t in body["tasks"])


def test_get_tasks_filter_unknown_status_returns_empty(client: TestClient) -> None:
    body = client.get("/api/tasks?status=unknown").json()
    assert body["tasks"] == []
    assert body["count"] == 0


def test_get_tasks_filter_by_user_id(client: TestClient) -> None:
    body = client.get("/api/tasks?userId=1").json()
    assert all(t["userId"] == 1 for t in body["tasks"])


def test_get_tasks_filter_by_nonexistent_user_id_returns_empty(client: TestClient) -> None:
    body = client.get("/api/tasks?userId=9999").json()
    assert body["tasks"] == []


# ---------------------------------------------------------------------------
# GET /api/stats
# ---------------------------------------------------------------------------

def test_get_stats_returns_200(client: TestClient) -> None:
    assert client.get("/api/stats").status_code == 200


def test_get_stats_users_total_is_positive(client: TestClient) -> None:
    assert client.get("/api/stats").json()["users"]["total"] > 0


def test_get_stats_task_counts_sum_to_total(client: TestClient) -> None:
    t = client.get("/api/stats").json()["tasks"]
    assert t["pending"] + t["inProgress"] + t["completed"] == t["total"]
