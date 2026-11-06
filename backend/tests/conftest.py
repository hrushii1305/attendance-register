import pytest
from fastapi.testclient import TestClient

from app.deps import get_client, get_store
from app.main import app
from tests.fakes import GOOD_TOKEN, FakeClient, FakeStore


@pytest.fixture
def store():
    return FakeStore()


@pytest.fixture
def client(store):
    app.dependency_overrides[get_client] = FakeClient
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth():
    return {"Authorization": f"Bearer {GOOD_TOKEN}"}
