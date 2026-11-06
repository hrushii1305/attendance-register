"""In-memory stand-ins for Supabase, so tests run without the internet."""
from types import SimpleNamespace

GOOD_TOKEN = "good-token"


class _FakeAuth:
    def get_user(self, token):
        if token == GOOD_TOKEN:
            return SimpleNamespace(user=SimpleNamespace(id="teacher-1", email="teacher@example.com"))
        raise Exception("Invalid JWT")


class FakeClient:
    """Pretends to be a supabase Client. Only .auth.get_user is used."""

    def __init__(self):
        self.auth = _FakeAuth()


class FakeStore:
    """Same methods as app.store.Store, but keeps data in Python lists."""

    def __init__(self):
        self.students = []
        self.records = {}  # (student_id, "YYYY-MM-DD") -> present
        self._next_id = 1

    def list_students(self):
        return sorted(self.students, key=lambda s: s["name"])

    def add_student(self, name):
        student = {"id": self._next_id, "name": name}
        self._next_id += 1
        self.students.append(student)
        return student

    def attendance_for(self, day):
        return [
            {"student_id": s["id"], "name": s["name"], "present": self.records.get((s["id"], day.isoformat()))}
            for s in self.list_students()
        ]

    def save_attendance(self, day, records):
        known = {s["id"] for s in self.students}
        if any(r["student_id"] not in known for r in records):
            raise ValueError("Unknown student")
        for r in records:
            self.records[(r["student_id"], day.isoformat())] = r["present"]

    def saved_dates(self):
        return sorted({d for (_, d) in self.records}, reverse=True)
