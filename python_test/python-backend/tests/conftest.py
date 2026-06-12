import pytest
from pathlib import Path
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app, DataStore


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Each test gets a fresh in-memory DataStore with persistence disabled."""
    monkeypatch.setenv("DATA_FILE", "")
    monkeypatch.setattr(main_module, "store", DataStore())
    return TestClient(app)


@pytest.fixture()
def fresh_store(monkeypatch: pytest.MonkeyPatch) -> DataStore:
    """Bare DataStore for unit-testing store methods in isolation."""
    monkeypatch.setenv("DATA_FILE", "")
    return DataStore()


@pytest.fixture()
def persisted_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> DataStore:
    """DataStore that writes to a temp file — use for persistence tests."""
    data_file = str(tmp_path / "store.json")
    monkeypatch.setenv("DATA_FILE", data_file)
    return DataStore()
