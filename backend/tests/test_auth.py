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
