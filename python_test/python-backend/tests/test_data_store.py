"""Unit tests for DataStore — no HTTP layer involved."""
import pytest
from app.main import DataStore


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

def test_create_user_returns_user_with_assigned_id(fresh_store: DataStore) -> None:
    user = fresh_store.create_user("Alice", "alice@example.com", "developer")
    assert user.id > 0
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.role == "developer"


def test_create_user_id_is_greater_than_existing_max(fresh_store: DataStore) -> None:
    existing_max = max(u.id for u in fresh_store.get_users())
    user = fresh_store.create_user("Bob", "bob_new@example.com", "designer")
    assert user.id == existing_max + 1


def test_create_user_increments_id_for_each_new_user(fresh_store: DataStore) -> None:
    u1 = fresh_store.create_user("A", "a@x.com", "admin")
    u2 = fresh_store.create_user("B", "b@x.com", "admin")
    assert u2.id == u1.id + 1


def test_create_user_duplicate_email_raises(fresh_store: DataStore) -> None:
    fresh_store.create_user("First", "dup@example.com", "developer")
    with pytest.raises(ValueError, match="already in use"):
        fresh_store.create_user("Second", "dup@example.com", "designer")


def test_create_user_appears_in_get_users(fresh_store: DataStore) -> None:
    before = len(fresh_store.get_users())
    fresh_store.create_user("New", "new@example.com", "qa")
    after = fresh_store.get_users()
    assert len(after) == before + 1
    assert any(u.email == "new@example.com" for u in after)


# ---------------------------------------------------------------------------
# get_users / get_user_by_id
# ---------------------------------------------------------------------------

def test_get_users_returns_all_seeded_users(fresh_store: DataStore) -> None:
    users = fresh_store.get_users()
    assert len(users) == 3


def test_get_users_returns_a_copy_not_the_internal_list(fresh_store: DataStore) -> None:
    list1 = fresh_store.get_users()
    list2 = fresh_store.get_users()
    assert list1 is not list2


def test_get_user_by_id_found(fresh_store: DataStore) -> None:
    user = fresh_store.get_user_by_id(1)
    assert user is not None
    assert user.id == 1


def test_get_user_by_id_not_found_returns_none(fresh_store: DataStore) -> None:
    assert fresh_store.get_user_by_id(9999) is None


# ---------------------------------------------------------------------------
# get_tasks (filtering)
# ---------------------------------------------------------------------------

def test_get_tasks_no_filter_returns_all(fresh_store: DataStore) -> None:
    tasks = fresh_store.get_tasks()
    assert len(tasks) == 3


def test_get_tasks_filter_by_status_pending(fresh_store: DataStore) -> None:
    tasks = fresh_store.get_tasks(status="pending")
    assert all(t.status == "pending" for t in tasks)
    assert len(tasks) >= 1


def test_get_tasks_filter_by_status_no_match_returns_empty(fresh_store: DataStore) -> None:
    tasks = fresh_store.get_tasks(status="nonexistent-status")
    assert tasks == []


def test_get_tasks_filter_by_user_id(fresh_store: DataStore) -> None:
    tasks = fresh_store.get_tasks(user_id="1")
    assert all(t.userId == 1 for t in tasks)


def test_get_tasks_filter_by_invalid_user_id_returns_empty(fresh_store: DataStore) -> None:
    tasks = fresh_store.get_tasks(user_id="not-a-number")
    assert tasks == []


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------

def test_get_stats_totals_match_store_contents(fresh_store: DataStore) -> None:
    stats = fresh_store.get_stats()
    assert stats.users.total == len(fresh_store.get_users())
    assert stats.tasks.total == len(fresh_store.get_tasks())


def test_get_stats_task_counts_sum_to_total(fresh_store: DataStore) -> None:
    stats = fresh_store.get_stats()
    t = stats.tasks
    assert t.pending + t.inProgress + t.completed == t.total
