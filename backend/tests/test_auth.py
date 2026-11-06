import pytest


@pytest.mark.parametrize("headers", [
    {},
    {"Authorization": "Basic abc"},
    {"Authorization": "Bearer "},
    {"Authorization": "Bearer bad-token"},
])
def test_students_requires_valid_token(client, headers):
    assert client.get("/students", headers=headers).status_code == 401


def test_valid_token_is_accepted(client, auth):
    assert client.get("/students", headers=auth).status_code == 200


# A problem on OUR side must not look like "not logged in" (401), because the
# frontend logs the teacher out on 401 and unsaved marks would be lost.
@pytest.mark.parametrize("token", ["supabase-down", "broken-config"])
def test_server_side_auth_failure_is_503_not_401(client, token):
    r = client.get("/students", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 503
    assert "Supabase" in r.json()["detail"]
