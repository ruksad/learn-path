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


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------

def test_create_task_returns_task_with_id(fresh_store: DataStore) -> None:
    task = fresh_store.create_task("Do something", "pending", user_id=1)
    assert task.id > 0
    assert task.title == "Do something"
    assert task.status == "pending"
    assert task.userId == 1


def test_create_task_id_greater_than_existing_max(fresh_store: DataStore) -> None:
    existing_max = max(t.id for t in fresh_store.get_tasks())
    task = fresh_store.create_task("New", "pending", user_id=1)
    assert task.id == existing_max + 1


def test_create_task_increments_id_sequentially(fresh_store: DataStore) -> None:
    t1 = fresh_store.create_task("A", "pending", user_id=1)
    t2 = fresh_store.create_task("B", "in-progress", user_id=1)
    assert t2.id == t1.id + 1


def test_create_task_nonexistent_user_raises(fresh_store: DataStore) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        fresh_store.create_task("T", "pending", user_id=9999)


def test_create_task_appears_in_get_tasks(fresh_store: DataStore) -> None:
    before = len(fresh_store.get_tasks())
    fresh_store.create_task("New task", "pending", user_id=1)
    assert len(fresh_store.get_tasks()) == before + 1


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------

def test_update_task_status(fresh_store: DataStore) -> None:
    updated = fresh_store.update_task(1, title=None, status="completed", user_id=None)
    assert updated is not None
    assert updated.status == "completed"


def test_update_task_title(fresh_store: DataStore) -> None:
    updated = fresh_store.update_task(1, title="Renamed", status=None, user_id=None)
    assert updated is not None
    assert updated.title == "Renamed"


def test_update_task_user_id(fresh_store: DataStore) -> None:
    updated = fresh_store.update_task(1, title=None, status=None, user_id=2)
    assert updated is not None
    assert updated.userId == 2


def test_update_task_multiple_fields(fresh_store: DataStore) -> None:
    updated = fresh_store.update_task(1, title="Multi", status="completed", user_id=2)
    assert updated is not None
    assert updated.title == "Multi"
    assert updated.status == "completed"
    assert updated.userId == 2


def test_update_task_unset_fields_unchanged(fresh_store: DataStore) -> None:
    original = fresh_store.get_tasks()
    task1 = next(t for t in original if t.id == 1)
    fresh_store.update_task(1, title=None, status="completed", user_id=None)
    tasks = fresh_store.get_tasks()
    updated = next(t for t in tasks if t.id == 1)
    assert updated.title == task1.title
    assert updated.userId == task1.userId


def test_update_task_not_found_returns_none(fresh_store: DataStore) -> None:
    assert fresh_store.update_task(9999, title="X", status=None, user_id=None) is None


def test_update_task_nonexistent_user_id_raises(fresh_store: DataStore) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        fresh_store.update_task(1, title=None, status=None, user_id=9999)


def test_update_task_is_persisted_in_get_tasks(fresh_store: DataStore) -> None:
    fresh_store.update_task(1, title=None, status="completed", user_id=None)
    tasks = fresh_store.get_tasks()
    task = next(t for t in tasks if t.id == 1)
    assert task.status == "completed"
