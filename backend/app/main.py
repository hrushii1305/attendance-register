import datetime
import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.deps import get_store, require_user
from app.store import Store

app = FastAPI(title="Attendance Register API")
logger = logging.getLogger("uvicorn.error")  # shows up in the backend window


# Turn any unexpected crash into a JSON "server error" reply.
# This is added BEFORE the CORS middleware, so it sits inside it and the reply
# still gets CORS headers. Without that, the browser hides the reply and the
# app wrongly says "Can't reach the server".
@app.middleware("http")
async def server_errors_as_json(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unexpected error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Server error. Check the backend window for details."},
        )


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
