"""An unexpected crash must reach the browser as a readable "server error",
not be blocked by CORS (which made the app say "Can't reach the server")."""
import pytest
from fastapi.testclient import TestClient

from app.deps import get_client, get_store
from app.main import app
from tests.fakes import GOOD_TOKEN, FakeClient, FakeStore

ORIGIN = "http://localhost:5173"


@pytest.fixture
def crashing_client():
    store = FakeStore()

    def crash():
        raise RuntimeError("database exploded")

    store.list_students = crash
    app.dependency_overrides[get_client] = FakeClient
    app.dependency_overrides[get_store] = lambda: store
    # Behave like the real server: turn crashes into responses instead of raising in the test.
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def test_crash_returns_json_500_that_the_browser_can_read(crashing_client):
    r = crashing_client.get(
        "/students",
        headers={"Authorization": f"Bearer {GOOD_TOKEN}", "Origin": ORIGIN},
    )
    assert r.status_code == 500
    assert r.headers.get("access-control-allow-origin") == ORIGIN
    assert "Server error" in r.json()["detail"]
