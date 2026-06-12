import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app, DataStore


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Each test gets a fresh DataStore so tests never share state."""
    monkeypatch.setattr(main_module, "store", DataStore())
    return TestClient(app)


@pytest.fixture()
def fresh_store() -> DataStore:
    """Bare DataStore for unit-testing store methods in isolation."""
    return DataStore()
