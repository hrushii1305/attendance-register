# Attendance Register — Design

Date: 2026-11-06
Status: approved

## Intent

This is a course assignment: a small web app one teacher uses on a laptop at
the start of class to take attendance for a single class. The person building
it is learning, so every part should be simple and easy to explain. Doing
less, and doing it clearly, is better than adding extra features.

## Goals

1. The teacher logs in with an email and password.
2. The teacher can add students and see the student list.
3. The teacher picks a date and marks each student present or absent. A "Mark
   all present" button sets everyone to present in one click. A Save button
   stores the result.
4. The teacher can look back at attendance saved for earlier dates.

## Non-goals (do not build)

- A sign-up page, password reset, or more than one user. The teacher's account
  is created by hand in the Supabase dashboard.
- More than one class, or any idea of a "class" in the data.
- Editing or deleting students.
- Reports, statistics, exports, or charts.
- Deploying the app. It only has to run on the local machine.
- Phone layouts. A laptop screen is the target, though the page shouldn't break
  if the window is narrow.

## Anti-goals (would count as failure even if the app works)

- Any secret key in the frontend code or committed to git.
- The browser talking to the database directly. Only FastAPI reads or writes
  data.
- Extra features or frameworks the assignment didn't ask for, which make the
  code harder for a beginner to understand.

## Constraints

- Required stack (set by the assignment): **React**, **Python**, **Supabase**.
- Frontend: React (created with Vite), JavaScript, plain CSS, in `/frontend`.
- Backend: Python with FastAPI, in `/backend`.
- Database and login: Supabase (Postgres plus Supabase Auth).
- Secrets go in `.env` files, which `.gitignore` already excludes. Each folder
  gets a committed `.env.example` that lists the setting names with no values.
- Windows with PowerShell. Every setup and run command must work there.
- `CLAUDE.md` currently says "NO login". The user has since asked for login
  explicitly in their final scope (Supabase Auth, email + password, no sign-up
  page). Login is **in scope**. The plan includes a small edit to the Scope
  section of `CLAUDE.md` so it matches this design.

## How it works (decided by the user)

**Login.** React uses `supabase-js` with the Supabase **publishable** key to log
in with email and password (`signInWithPassword`). After login, React sends
the session's access token to FastAPI on every request in the header
`Authorization: Bearer <token>`.

**Token check.** FastAPI checks the token with Supabase on **every** endpoint.
If the header is missing or the token is invalid, it returns **401**.

**Database access.** Only FastAPI talks to the database. It uses the Supabase
**secret** key, which is stored in `backend/.env`.

## How it works (builder's calls; the user can change these)

### Data: two tables

```sql
create table students (
  id         bigint generated always as identity primary key,
  name       text not null,
  created_at timestamptz not null default now()
);

create table attendance (
  id         bigint generated always as identity primary key,
  student_id bigint not null references students(id) on delete cascade,
  date       date not null,
  present    boolean not null,
  unique (student_id, date)
);

alter table students   enable row level security;
alter table attendance enable row level security;
-- No policies on purpose. The publishable key (which is in the browser) can
-- then read or write nothing. The secret key that FastAPI uses skips these
-- checks, which enforces "only FastAPI talks to the database".
```

The SQL goes in `backend/schema.sql`. The user pastes it into the Supabase SQL
editor once.

### API (FastAPI): every route requires a valid token

| Method & path | What it does |
|---|---|
| `GET /students` | Returns all students, sorted by name. |
| `POST /students` body `{"name": "..."}` | Adds a student. An empty or whitespace-only name returns 400. |
| `GET /attendance?date=YYYY-MM-DD` | Returns every student with that date's status: `present` is `true`, `false`, or `null` if not saved yet. |
| `PUT /attendance` body `{"date": "...", "records": [{"student_id": 1, "present": true}, ...]}` | Saves the date's attendance with an upsert on `(student_id, date)`, so saving the same date again overwrites it. |
| `GET /attendance/dates` | Returns the dates that have saved attendance, newest first. Used for "view past dates". |

- **Token check:** a single FastAPI dependency reads the Bearer token and calls
  `supabase.auth.get_user(token)`. If that fails, the request gets 401. Every
  route uses this dependency.
- **CORS:** allows the Vite dev server only (`http://localhost:5173`).
- **Libraries:** `fastapi`, `uvicorn`, `supabase` (supabase-py), and
  `python-dotenv`, listed in `backend/requirements.txt` and installed in a
  `venv`.
- **`backend/.env`:** `SUPABASE_URL` and `SUPABASE_SECRET_KEY`.

### Frontend (React + Vite)

- **React** app created with **Vite** (the React + JavaScript template).
  Components are written in JavaScript (`.jsx`, not TypeScript) and styled with
  plain CSS files. No router, CSS framework, or UI component library.
- **`frontend/.env`:** `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, and
  `VITE_API_URL` (default `http://localhost:8000`).
- **Login screen:** fields for email and password and a Log in button. Shows an
  error if login fails.
- **Main screen**, on a single page:
  - **Header:** app name and a Log out button.
  - **Students:** a box to type a name, an Add button, and the student list.
  - **Attendance:** a date picker that starts on today, then one row per
    student with Present and Absent toggles, a "Mark all present" button, and a
    Save button. A short "Saved" message appears after a successful save.
  - **Past dates:** a list of dates that have saved attendance. Clicking one
    loads it into the Attendance section.
- **Unsaved students** (builder's call, so history stays accurate):
  - **New date** (nothing saved yet for that date): every student starts as
    **Absent**.
  - **Date that already has saved attendance:** a student with no record, such
    as one added after that day, shows as **"Not recorded"** (no toggle
    selected).
  - **Save** sends only the students who have Present or Absent set. A "Not
    recorded" student is never saved as Absent by accident.
  - **"Mark all present"** sets every student to Present, including any that
    were "Not recorded".
- **Expired session:** if the API returns 401, the app logs out and shows the
  login screen.
- **Look:** clean and simple, with readable spacing and clear buttons.

### Testing (light, to fit a course assignment)

- A few `pytest` tests for the backend that check:
  - a missing or bad token returns 401;
  - adding a student with an empty name returns 400;
  - the attendance endpoints return the expected shape.
- These tests swap the Supabase calls for fakes, so they don't need the
  internet.
- No frontend tests. Check the frontend by hand in the browser.

## Left to the builder

- File and folder layout inside `/backend` and `/frontend`.
- The exact styling.
- Error message wording.
- A `README.md` with plain Windows/PowerShell steps: create the tables, create
  the teacher user, fill in both `.env` files, start the backend, start the
  frontend.
