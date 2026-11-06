import pytest


def test_list_starts_empty(client, auth):
    assert client.get("/students", headers=auth).json() == []


def test_add_student_trims_name_and_lists_sorted(client, auth):
    r = client.post("/students", json={"name": "  Zara "}, headers=auth)
    assert r.status_code == 201
    assert r.json()["name"] == "Zara"
    client.post("/students", json={"name": "Amit"}, headers=auth)
    assert [s["name"] for s in client.get("/students", headers=auth).json()] == ["Amit", "Zara"]


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_name_rejected(client, auth, name):
    assert client.post("/students", json={"name": name}, headers=auth).status_code == 400


def test_post_requires_token(client):
    assert client.post("/students", json={"name": "Amit"}).status_code == 401
