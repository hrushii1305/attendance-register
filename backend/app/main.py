import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.deps import get_store, require_user
from app.store import Store

app = FastAPI(title="Attendance Register API")

# Only the React dev server may call this API from a browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewStudent(BaseModel):
    name: str


class Record(BaseModel):
    student_id: int
    present: bool


class DayAttendance(BaseModel):
    date: datetime.date
    records: list[Record]


@app.get("/students")
def list_students(user=Depends(require_user), store: Store = Depends(get_store)):
    return store.list_students()


@app.post("/students", status_code=201)
def add_student(body: NewStudent, user=Depends(require_user), store: Store = Depends(get_store)):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    return store.add_student(name)


@app.get("/attendance/dates")
def saved_dates(user=Depends(require_user), store: Store = Depends(get_store)):
    return store.saved_dates()


@app.get("/attendance")
def get_attendance(date: datetime.date, user=Depends(require_user), store: Store = Depends(get_store)):
    return store.attendance_for(date)


@app.put("/attendance")
def save_attendance(body: DayAttendance, user=Depends(require_user), store: Store = Depends(get_store)):
    records = [r.model_dump() for r in body.records]
    try:
        store.save_attendance(body.date, records)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"saved": len(records)}
