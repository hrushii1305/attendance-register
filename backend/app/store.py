"""Every read and write to the database lives here."""
from datetime import date

from postgrest.exceptions import APIError

PAGE_SIZE = 1000  # Supabase returns at most 1000 rows per request by default
FOREIGN_KEY_VIOLATION = "23503"  # Postgres error code: the student id doesn't exist


class Store:
    def __init__(self, client):
        self.client = client

    def list_students(self) -> list[dict]:
        return self.client.table("students").select("id,name").order("name").execute().data

    def add_student(self, name: str) -> dict:
        row = self.client.table("students").insert({"name": name}).execute().data[0]
        return {"id": row["id"], "name": row["name"]}

    def attendance_for(self, day: date) -> list[dict]:
        """Every student, with present = True/False, or None if not saved for that day."""
        rows = (
            self.client.table("attendance")
            .select("student_id,present")
            .eq("date", day.isoformat())
            .execute()
            .data
        )
        saved = {r["student_id"]: r["present"] for r in rows}
        return [
            {"student_id": s["id"], "name": s["name"], "present": saved.get(s["id"])}
            for s in self.list_students()
        ]

    def save_attendance(self, day: date, records: list[dict]) -> None:
        """Insert or overwrite one row per student for that day."""
        if not records:
            return
        rows = [
            {"student_id": r["student_id"], "date": day.isoformat(), "present": r["present"]}
            for r in records
        ]
        try:
            self.client.table("attendance").upsert(rows, on_conflict="student_id,date").execute()
        except APIError as e:
            if e.code == FOREIGN_KEY_VIOLATION:
                raise ValueError("Unknown student") from e
            raise  # any other database problem is a real server error

    def saved_dates(self) -> list[str]:
        """Dates that have any saved attendance, newest first."""
        dates, start = set(), 0
        while True:
            page = (
                self.client.table("attendance")
                .select("date")
                .order("date", desc=True)
                .range(start, start + PAGE_SIZE - 1)
                .execute()
                .data
            )
            dates.update(r["date"] for r in page)
            if len(page) < PAGE_SIZE:
                return sorted(dates, reverse=True)
            start += PAGE_SIZE
