"""Tests for the real Store's error handling, using a tiny fake supabase client."""
from datetime import date

import pytest
from postgrest.exceptions import APIError

from app.store import Store


class _FailingTable:
    def __init__(self, error):
        self.error = error

    def upsert(self, rows, on_conflict):
        return self

    def execute(self):
        raise self.error


class _FailingClient:
    def __init__(self, error):
        self.error = error

    def table(self, name):
        return _FailingTable(self.error)


def _api_error(code, message):
    return APIError({"message": message, "code": code, "details": None, "hint": None})


def test_foreign_key_violation_means_unknown_student():
    # Postgres code 23503 = foreign key violation: that student id doesn't exist.
    store = Store(_FailingClient(_api_error("23503", "violates foreign key constraint")))
    with pytest.raises(ValueError, match="Unknown student"):
        store.save_attendance(date(2026, 11, 6), [{"student_id": 999, "present": True}])


def test_other_database_errors_are_not_called_unknown_student():
    # 42P01 = table doesn't exist (e.g. schema.sql was never run).
    store = Store(_FailingClient(_api_error("42P01", 'relation "attendance" does not exist')))
    with pytest.raises(APIError):
        store.save_attendance(date(2026, 11, 6), [{"student_id": 1, "present": True}])
