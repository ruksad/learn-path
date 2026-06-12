"""Integration tests for POST /api/users and GET /api/users endpoints."""
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# POST /api/users — happy path
# ---------------------------------------------------------------------------

def test_create_user_returns_201(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "Alice", "email": "alice@example.com", "role": "developer"})
    assert resp.status_code == 201


def test_create_user_response_body_has_expected_fields(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "Alice", "email": "alice@x.com", "role": "designer"})
    body = resp.json()
    assert "id" in body
    assert body["name"] == "Alice"
    assert body["email"] == "alice@x.com"
    assert body["role"] == "designer"


def test_create_user_id_is_positive_integer(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "Bob", "email": "bob@x.com", "role": "manager"})
    assert isinstance(resp.json()["id"], int)
    assert resp.json()["id"] > 0


def test_create_user_email_normalised_to_lowercase(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "Carol", "email": "Carol@X.COM", "role": "admin"})
    assert resp.json()["email"] == "carol@x.com"


def test_create_user_role_normalised_to_lowercase(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "Dave", "email": "dave@x.com", "role": "DEVELOPER"})
    assert resp.json()["role"] == "developer"


def test_created_user_appears_in_get_users(client: TestClient) -> None:
    client.post("/api/users", json={"name": "Eve", "email": "eve@x.com", "role": "qa"})
    resp = client.get("/api/users")
    emails = [u["email"] for u in resp.json()["users"]]
    assert "eve@x.com" in emails


def test_get_users_count_increases_after_create(client: TestClient) -> None:
    before = client.get("/api/users").json()["count"]
    client.post("/api/users", json={"name": "Frank", "email": "frank@x.com", "role": "developer"})
    after = client.get("/api/users").json()["count"]
    assert after == before + 1


# ---------------------------------------------------------------------------
# POST /api/users — validation errors (400)
# ---------------------------------------------------------------------------

def test_create_user_missing_name_returns_400(client: TestClient) -> None:
    resp = client.post("/api/users", json={"email": "a@x.com", "role": "developer"})
    assert resp.status_code == 400


def test_create_user_missing_email_returns_400(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "A", "role": "developer"})
    assert resp.status_code == 400


def test_create_user_missing_role_returns_400(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "A", "email": "a@x.com"})
    assert resp.status_code == 400


def test_create_user_empty_body_returns_400(client: TestClient) -> None:
    resp = client.post("/api/users", json={})
    assert resp.status_code == 400


def test_create_user_blank_name_returns_400(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "   ", "email": "a@x.com", "role": "developer"})
    assert resp.status_code == 400


def test_create_user_invalid_email_no_at_returns_400(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "A", "email": "notanemail", "role": "developer"})
    assert resp.status_code == 400


def test_create_user_invalid_email_no_domain_returns_400(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "A", "email": "a@", "role": "developer"})
    assert resp.status_code == 400


def test_create_user_invalid_role_returns_400(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "A", "email": "a@x.com", "role": "wizard"})
    assert resp.status_code == 400


def test_create_user_invalid_role_error_lists_valid_roles(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "A", "email": "a@x.com", "role": "wizard"})
    body = str(resp.json())
    assert "developer" in body


def test_create_user_duplicate_email_returns_400(client: TestClient) -> None:
    payload = {"name": "A", "email": "dup@x.com", "role": "developer"}
    client.post("/api/users", json=payload)
    resp = client.post("/api/users", json={**payload, "name": "B"})
    assert resp.status_code == 400


def test_create_user_duplicate_email_error_message_is_meaningful(client: TestClient) -> None:
    payload = {"name": "A", "email": "dup2@x.com", "role": "developer"}
    client.post("/api/users", json=payload)
    resp = client.post("/api/users", json={**payload, "name": "B"})
    assert "already in use" in resp.json()["detail"]


def test_create_user_400_detail_is_not_internal_traceback(client: TestClient) -> None:
    resp = client.post("/api/users", json={"name": "A", "email": "bad", "role": "developer"})
    body = str(resp.json())
    assert "Traceback" not in body
    assert "Exception" not in body


# ---------------------------------------------------------------------------
# GET /api/users
# ---------------------------------------------------------------------------

def test_get_users_returns_200(client: TestClient) -> None:
    assert client.get("/api/users").status_code == 200


def test_get_users_response_has_users_and_count(client: TestClient) -> None:
    body = client.get("/api/users").json()
    assert "users" in body
    assert "count" in body


def test_get_users_count_matches_users_list_length(client: TestClient) -> None:
    body = client.get("/api/users").json()
    assert body["count"] == len(body["users"])
