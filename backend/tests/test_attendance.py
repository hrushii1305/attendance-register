def _add(client, auth, name):
    return client.post("/students", json={"name": name}, headers=auth).json()["id"]


def test_unsaved_date_returns_null_for_everyone(client, auth):
    _add(client, auth, "Amit")
    rows = client.get("/attendance?date=2026-11-06", headers=auth).json()
    assert rows == [{"student_id": rows[0]["student_id"], "name": "Amit", "present": None}]


def test_save_then_load_and_resave_overwrites(client, auth):
    a = _add(client, auth, "Amit")
    body = {"date": "2026-11-06", "records": [{"student_id": a, "present": True}]}
    assert client.put("/attendance", json=body, headers=auth).json() == {"saved": 1}
    body["records"][0]["present"] = False
    client.put("/attendance", json=body, headers=auth)
    assert client.get("/attendance?date=2026-11-06", headers=auth).json()[0]["present"] is False


def test_student_added_later_is_null_on_saved_date(client, auth):
    a = _add(client, auth, "Amit")
    client.put("/attendance", json={"date": "2026-11-05", "records": [{"student_id": a, "present": True}]}, headers=auth)
    _add(client, auth, "Bela")
    rows = {r["name"]: r["present"] for r in client.get("/attendance?date=2026-11-05", headers=auth).json()}
    assert rows == {"Amit": True, "Bela": None}


def test_saved_dates_newest_first_without_duplicates(client, auth):
    a = _add(client, auth, "Amit")
    for d in ["2026-11-04", "2026-11-06", "2026-11-04"]:
        client.put("/attendance", json={"date": d, "records": [{"student_id": a, "present": True}]}, headers=auth)
    assert client.get("/attendance/dates", headers=auth).json() == ["2026-11-06", "2026-11-04"]


def test_bad_or_missing_date_is_422(client, auth):
    assert client.get("/attendance?date=11/06/2026", headers=auth).status_code == 422
    assert client.get("/attendance", headers=auth).status_code == 422


def test_unknown_student_is_400(client, auth):
    body = {"date": "2026-11-06", "records": [{"student_id": 999, "present": True}]}
    assert client.put("/attendance", json=body, headers=auth).status_code == 400


def test_attendance_routes_require_token(client):
    assert client.get("/attendance?date=2026-11-06").status_code == 401
    assert client.put("/attendance", json={"date": "2026-11-06", "records": []}).status_code == 401
    assert client.get("/attendance/dates").status_code == 401
