# Attendance Register Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local web app where one teacher logs in, adds students, and marks and reviews daily attendance for one class.

**Architecture:**
- A React (Vite) single page logs in through Supabase Auth with the publishable key.
- It then calls a FastAPI backend with `Authorization: Bearer <token>`.
- FastAPI checks the token with Supabase on every route and is the only thing that touches the database, using the secret key.
- Database access sits behind a small `Store` class, so tests can swap in an in-memory fake.

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, uvicorn, supabase-py 2.x, python-dotenv, pytest, httpx.
- Frontend: React (Vite, JavaScript template), @supabase/supabase-js 2.x, plain CSS.
- Database: Supabase Postgres.

**Spec:** `docs/superpowers/specs/2026-11-06-attendance-register-design.md`

## Global Constraints

- Required stack: **React**, **Python**, **Supabase**. Frontend is React created with Vite, JavaScript (`.jsx`, not TypeScript), plain CSS. No router, CSS framework, or UI component library.
- Frontend lives in `/frontend`, backend in `/backend`.
- Secrets only in `.env` files, never committed. Commit `backend/.env.example` and `frontend/.env.example` with names only.
- `backend/.env`: `SUPABASE_URL`, `SUPABASE_SECRET_KEY`. `frontend/.env`: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, `VITE_API_URL` (default `http://localhost:8000`).
- The browser never reads/writes tables; RLS is enabled with no policies.
- Every API route requires a valid Supabase access token; otherwise **401**.
- CORS allows only `http://localhost:5173`.
- No sign-up page, no editing/deleting students, no multiple classes, no reports, no deployment.
- Windows + PowerShell: every command in this plan and the README must work in PowerShell.
- The user is learning: after each task, explain what was built in plain, simple words.

## Review Focus

1. **Bad Authorization header** (missing, `Basic ...`, `Bearer ` with empty token, expired token) → 401, never 500. *Tested in Task 1.*
2. **Blank or whitespace-only student name** → 400, and names are saved trimmed. *Tested in Task 1.*
3. **Malformed date** (`?date=11/06/2026`, missing date) → 422 from FastAPI validation, not 500. *Tested in Task 2.*
4. **Saving a record for a student id that doesn't exist** → 400 with a clear message, not 500. *Tested in Task 2.*
5. **"Today" near midnight / in non-UTC time zones** → the date picker must use the laptop's local date, not `toISOString()` (UTC). *Manual check in Task 4.*

---

## File Structure

```
backend/
  requirements.txt      dependencies
  .env.example          SUPABASE_URL=, SUPABASE_SECRET_KEY=
  schema.sql            tables + RLS (from spec, verbatim)
  app/__init__.py
  app/deps.py           get_client(), get_store(), require_user()
  app/store.py          Store: all database reads/writes
  app/main.py           FastAPI app, CORS, routes
  tests/__init__.py
  tests/fakes.py        FakeClient, FakeStore (in-memory)
  tests/conftest.py     TestClient with fakes injected
  tests/test_auth.py
  tests/test_students.py
  tests/test_attendance.py
frontend/               (scaffolded by Vite)
  .env.example
  src/supabaseClient.js supabase-js client
  src/api.js            fetch wrapper + one function per endpoint
  src/attendanceState.js todayLocal(), initialStatuses(), recordsToSave()
  src/App.jsx           session handling; Login or main screen
  src/Login.jsx
  src/Students.jsx
  src/Attendance.jsx
  src/PastDates.jsx
  src/App.css, src/index.css
README.md
CLAUDE.md               (Scope section updated)
```

---

### Task 1: Backend foundation, token check, and students endpoints

**Files:**
- Create: `backend/requirements.txt`, `backend/.env.example`, `backend/schema.sql`, `backend/app/__init__.py`, `backend/app/deps.py`, `backend/app/store.py`, `backend/app/main.py`
- Test: `backend/tests/__init__.py`, `backend/tests/fakes.py`, `backend/tests/conftest.py`, `backend/tests/test_auth.py`, `backend/tests/test_students.py`

**Interfaces:**
- Produces:
  - `app.deps.get_client() -> supabase.Client` — cached; reads `SUPABASE_URL`, `SUPABASE_SECRET_KEY` via `load_dotenv()`.
  - `app.deps.get_store(client = Depends(get_client)) -> Store`
  - `app.deps.require_user(authorization: str | None = Header(None), client = Depends(get_client))` — returns the Supabase user or raises `HTTPException(401, "Not logged in")`.
  - `app.store.Store(client)` with methods:
    - `list_students() -> list[dict]` — `[{"id": int, "name": str}]`, sorted by name
    - `add_student(name: str) -> dict` — `{"id", "name"}`
    - `attendance_for(day: date) -> list[dict]` — `[{"student_id", "name", "present": bool | None}]`, sorted by name (Task 2)
    - `save_attendance(day: date, records: list[dict]) -> None` — raises `ValueError` for unknown student ids (Task 2)
    - `saved_dates() -> list[str]` — ISO dates, newest first, no duplicates (Task 2)
  - `app.main.app` — the FastAPI instance.
  - `tests.fakes.FakeClient` — `.auth.get_user(token)` returns an object with `.user` when the token is `"good-token"`, else raises.
  - `tests.fakes.FakeStore` — in-memory implementation of every `Store` method above.
  - `tests.conftest` fixtures: `client` (TestClient with fakes injected), `auth` (= `{"Authorization": "Bearer good-token"}`), `store` (the FakeStore instance).

- [ ] **Step 1: Set up the backend folder**
  - Write `requirements.txt`: `fastapi`, `uvicorn[standard]`, `supabase`, `python-dotenv`, `pytest`, `httpx`.
  - Write `.env.example` with the two names and empty values.
  - Copy the SQL block from the spec into `schema.sql` verbatim.
  - Then run in PowerShell:

  ```powershell
  cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt
  ```
  Expected: installs without errors. (If activation is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.)

- [ ] **Step 2: Write the fakes, the conftest, and the failing tests**

```python
# tests/test_auth.py
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

# tests/test_students.py
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
```

`conftest.py` uses `app.dependency_overrides` to replace `get_client` with a `FakeClient()` and `get_store` with a shared `FakeStore()`.

- [ ] **Step 3: Run the tests and check that they fail**

Run: `python -m pytest -v` (from `backend`, with venv active)
Expected: FAIL / collection errors, because `app.main` doesn't exist yet.

- [ ] **Step 4: Implement `deps.py`, `store.py` (students methods), and `main.py`**
  - `require_user`:
    - accepts only `Bearer <non-empty token>`;
    - calls `client.auth.get_user(token)`;
    - treats any exception or an empty `.user` as 401.
  - `Store.list_students` uses `table("students").select("id,name").order("name")`.
  - `Store.add_student` inserts and returns `data[0]`.
  - Routes:
    - `GET /students` returns `200`, `POST /students` returns `201`.
    - The POST body is a Pydantic model `{name: str}`.
    - The name is stripped before saving; if it's empty after stripping, return `HTTPException(400, "Name is required")`.
  - Every route declares `user = Depends(require_user)`.
  - Add `CORSMiddleware` with `allow_origins=["http://localhost:5173"]`, all methods, and all headers.

- [ ] **Step 5: Run the tests and check that they pass**

Run: `python -m pytest -v`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add backend; git commit -m "Add FastAPI backend with token check and students endpoints"
```
(Check `git status` first: `backend/venv/` and `backend/.env` must NOT be staged.)

---

### Task 2: Attendance endpoints

**Files:**
- Modify: `backend/app/store.py`, `backend/app/main.py`, `backend/tests/fakes.py`
- Test: `backend/tests/test_attendance.py`

**Interfaces:**
- Consumes: `Store`, `FakeStore`, and the `client`/`auth`/`store` fixtures from Task 1.
- Produces (HTTP, used by Task 3's `api.js`):
  - `GET /attendance?date=YYYY-MM-DD` → `[{"student_id": int, "name": str, "present": true|false|null}]`
  - `PUT /attendance` with body `{"date": "YYYY-MM-DD", "records": [{"student_id": int, "present": bool}]}` → `{"saved": <count>}`
  - `GET /attendance/dates` → `["YYYY-MM-DD", ...]`, newest first

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_attendance.py
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
```

- [ ] **Step 2: Run the tests and check that they fail**

Run: `python -m pytest tests/test_attendance.py -v`
Expected: FAIL with 404 / 405, because the routes don't exist yet.

- [ ] **Step 3: Implement the three `Store` methods, the matching `FakeStore` methods, and the routes**
  - `attendance_for`:
    - reads all students, plus the `attendance` rows where `date = day`;
    - merges them in Python;
    - `present` is `None` where there's no row.
  - `save_attendance`:
    - uses `upsert(rows, on_conflict="student_id,date")`;
    - catches `postgrest.exceptions.APIError`;
    - re-raises it as `ValueError("Unknown student")`.
  - `saved_dates`: select `date`, deduplicate, sort descending.
  - `FakeStore.save_attendance` raises `ValueError` for ids that aren't in its students list.
  - Route parameters: the query param is `date: datetime.date` (required); the PUT body model uses `datetime.date`.
  - The `ValueError` from `save_attendance` → `HTTPException(400, str(e))`.
  - Declare `GET /attendance/dates` *before* any route that could shadow it.

- [ ] **Step 4: Run all tests and check that they pass**

Run: `python -m pytest -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend; git commit -m "Add attendance endpoints"
```

---

### Task 3: Frontend scaffold, login, and API client

**Files:**
- Create (via Vite): `frontend/` with the React + JavaScript template
- Create: `frontend/.env.example`, `frontend/src/supabaseClient.js`, `frontend/src/api.js`, `frontend/src/Login.jsx`
- Modify: `frontend/src/App.jsx`, `frontend/src/App.css`, `frontend/src/index.css` (remove the Vite demo content)

**Interfaces:**
- Consumes: the HTTP endpoints from Tasks 1–2.
- Produces:
  - `supabaseClient.js`: `export const supabase` (from `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`).
  - `api.js`: `getStudents()`, `addStudent(name)`, `getAttendance(date)`, `saveAttendance(date, records)`, `getSavedDates()`.
    - Each is async and returns the parsed JSON.
    - On a non-OK response, each throws `Error(detail)`.
    - On a 401, each first calls `supabase.auth.signOut()`.
  - `App.jsx`: holds `session` state from `supabase.auth.getSession()` and `onAuthStateChange`. With no session it renders `<Login />`; otherwise it renders the main screen (a placeholder until Task 4).

- [ ] **Step 1: Scaffold and install**

```powershell
npm create vite@latest frontend -- --template react; cd frontend; npm install; npm install @supabase/supabase-js
```
Expected: `npm run dev` serves the Vite demo page at http://localhost:5173.

- [ ] **Step 2: Write `.env.example` and the three modules, then strip the demo content**
  - `.env.example` lists the three `VITE_` names with empty values, except `VITE_API_URL=http://localhost:8000`.
  - `api.js`:
    - reads the token from `(await supabase.auth.getSession()).data.session?.access_token`;
    - sends it as `Authorization: Bearer <token>`, plus `Content-Type: application/json` on bodies.
  - `Login.jsx`:
    - has an email field, a password field, and a "Log in" button;
    - calls `supabase.auth.signInWithPassword`;
    - shows `error.message` on failure.
  - `App.jsx`, once logged in: a header with "Attendance Register" and a "Log out" button (`supabase.auth.signOut()`).

- [ ] **Step 3: Manual check (needs `frontend/.env` filled in, the teacher user created, and the backend running)**
  - A wrong password shows an error message.
  - The right password shows the header and the Log out button.
  - Refreshing the page stays logged in.
  - Log out returns to the login screen.
  - `npm run build` succeeds.

- [ ] **Step 4: Commit**

```powershell
git add frontend; git commit -m "Add React frontend with Supabase login and API client"
```
(Confirm `frontend/node_modules/` and `frontend/.env` are not staged.)

---

### Task 4: Main screen — students, attendance, past dates

**Files:**
- Create: `frontend/src/attendanceState.js`, `frontend/src/Students.jsx`, `frontend/src/Attendance.jsx`, `frontend/src/PastDates.jsx`
- Modify: `frontend/src/App.jsx`, `frontend/src/App.css`

**Interfaces:**
- Consumes: the `api.js` functions from Task 3.
- Produces:
  - `attendanceState.js`:
    - `todayLocal() -> "YYYY-MM-DD"` — built from `getFullYear/getMonth/getDate`, never `toISOString`.
    - `initialStatuses(rows) -> {[student_id]: true|false|null}` — if every row's `present` is `null` (a new date), every student is `false` (Absent); otherwise it keeps the values, with `null` meaning "Not recorded".
    - `recordsToSave(statuses) -> [{student_id, present}]` — only non-null entries.
  - `App.jsx` owns: `students`, `date` (starting at `todayLocal()`), and `savedDates`. It reloads students after an add, and saved dates after a save.

- [ ] **Step 1: Implement `attendanceState.js` and the three components, then wire them into `App.jsx`**
  - **Students:** a name input and an "Add" button. Enter submits; the input clears on success; API errors show inline. Below it, the student list.
  - **Attendance:**
    - a date `<input type="date">`; changing the date loads `getAttendance(date)`;
    - one row per student with Present and Absent toggle buttons, where the selected one is highlighted and a null status shows "Not recorded";
    - "Mark all present" sets every status to `true`;
    - "Save" sends `recordsToSave(...)` and then shows "Saved" for a few seconds;
    - with no students, it shows "Add a student first".
  - **PastDates:** shows the `savedDates` list. Clicking a date sets `date`, which loads it into Attendance.
  - **CSS:** clean and simple; a centred column about 720px wide; clear buttons; no horizontal scroll on a narrow window.

- [ ] **Step 2: Manual check against real Supabase (backend running, logged in)**
  - Add "Amit" and "Bela". Both appear sorted. A blank name shows an error.
  - Today's date is pre-selected and matches the laptop's calendar (Review Focus 5).
  - On a new date, both students show Absent. "Mark all present" turns both Present. Save shows "Saved", and today appears in Past dates.
  - Add "Chen". Click today in Past dates: Chen shows "Not recorded". Save without touching Chen, reload the page, and Chen is still "Not recorded".
  - Mark Amit Absent, save, and reload: the change persisted.
  - `npm run build` succeeds.

- [ ] **Step 3: Commit**

```powershell
git add frontend; git commit -m "Add students, attendance, and past dates screens"
```

---

### Task 5: README, CLAUDE.md scope, final check

**Files:**
- Create: `README.md`
- Modify: `CLAUDE.md` (Scope section only)

- [ ] **Step 1: Update `CLAUDE.md`**
  - Replace the Scope bullets with ones that match the spec's goals:
    - teacher login with Supabase Auth email + password, with no sign-up page;
    - add/list students;
    - mark present/absent for a date, with "mark all present";
    - view past dates.
  - Keep "NO extra features unless I ask".
  - Leave the other sections untouched.

- [ ] **Step 2: Write `README.md`** with these PowerShell steps, in order:
  1. Create a Supabase project.
  2. Run `backend/schema.sql` in the SQL editor.
  3. Create the teacher user (Authentication → Users → Add user).
  4. Copy `backend/.env.example` to `backend/.env` and fill in the values (where to find the URL and secret key).
  5. Copy `frontend/.env.example` to `frontend/.env` and fill in the values (where to find the publishable key).
  6. Start the backend: `cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000`.
  7. Start the frontend: `cd frontend; npm run dev`, then open http://localhost:5173.
  8. Run the tests: `python -m pytest`.

- [ ] **Step 3: Final verification**
  - Run `python -m pytest -v` (all PASS) and `npm run build` (succeeds).
  - Follow the README from a fresh terminal and repeat the Task 4 manual check once.
  - Run `git status` and confirm no `.env` file is tracked: `git ls-files | Select-String "\.env"` should list only the two `.env.example` files.

- [ ] **Step 4: Commit**

```powershell
git add README.md CLAUDE.md; git commit -m "Add README and update project scope"
```
