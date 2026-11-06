# Attendance Register

A simple attendance register for one teacher and one class. The teacher logs
in, adds students, marks each student present or absent for a date, and can
look back at past dates.

- **Frontend:** React (Vite), JavaScript, plain CSS, in `frontend/`
- **Backend:** Python + FastAPI, in `backend/`
- **Database and login:** Supabase (Postgres + Supabase Auth)

The browser logs in with Supabase and sends its login token to FastAPI. FastAPI
checks the token on every request and is the only part that reads or writes the
database.

## What you need

- Python 3.10 or newer
- Node.js 20.19 or newer
- A free Supabase account: https://supabase.com

All commands below are for **PowerShell on Windows**, run from the project folder.

## 1. Set up Supabase (once)

1. Create a new Supabase project.
2. Open **SQL Editor**, paste in everything from `backend/schema.sql`, and click
   **Run**. This creates the `students` and `attendance` tables and locks them
   so the browser can't read them directly.
3. Create the teacher account: **Authentication → Users → Add user → Create new
   user**. Enter an email and password and tick **Auto Confirm User**.
   (There is no sign-up page in the app on purpose.)

## 2. Fill in the secret settings

Find these values in Supabase:

- **Project URL:** under **Project Settings → Data API**
- **Publishable key** (starts with `sb_publishable_`) and **Secret key** (starts
  with `sb_secret_`): under **Project Settings → API Keys**

Then copy the example files:

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

Open each `.env` file and fill it in:

| File | Setting | Value |
|---|---|---|
| `backend/.env` | `SUPABASE_URL` | Project URL |
| `backend/.env` | `SUPABASE_SECRET_KEY` | Secret key (**never** put this in the frontend) |
| `frontend/.env` | `VITE_SUPABASE_URL` | Project URL |
| `frontend/.env` | `VITE_SUPABASE_PUBLISHABLE_KEY` | Publishable key |
| `frontend/.env` | `VITE_API_URL` | `http://localhost:8000` (already filled in) |

`.env` files are listed in `.gitignore`, so git never commits them.

## 3. Install (once)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..\frontend
npm install
cd ..
```

If PowerShell refuses to run `Activate.ps1`, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 4. Run the app

Use two PowerShell windows.

**Window 1: backend** (http://localhost:8000)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Window 2: frontend** (http://localhost:5173)

```powershell
cd frontend
npm run dev
```

Open http://localhost:5173 and log in with the teacher account.

## 5. Run the tests

The backend tests use a fake, in-memory Supabase, so they need no internet and
no `.env`:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest -v
```

## Project layout

```
backend/
  schema.sql       tables + security (paste into Supabase once)
  app/main.py      API routes
  app/deps.py      login-token check, database connection
  app/store.py     all database reads and writes
  tests/           pytest tests (with fake Supabase)
frontend/
  src/App.jsx           login screen or main screen
  src/Login.jsx         email + password form
  src/Attendance.jsx    mark present/absent for a date
  src/PastDates.jsx     list of saved dates
  src/Students.jsx      add and list students
  src/api.js            talks to the backend
  src/attendanceState.js  small date/attendance helpers
```

## API

Every route needs the header `Authorization: Bearer <token>`. Without a valid
token, it answers **401**.

| Method & path | What it does |
|---|---|
| `GET /students` | All students, A–Z |
| `POST /students` `{"name": "Amit"}` | Add a student (blank name → 400) |
| `GET /attendance?date=YYYY-MM-DD` | Every student with `present`: `true`, `false`, or `null` (not recorded) |
| `PUT /attendance` `{"date": "...", "records": [{"student_id": 1, "present": true}]}` | Save a day (saving again overwrites) |
| `GET /attendance/dates` | Dates with saved attendance, newest first |
