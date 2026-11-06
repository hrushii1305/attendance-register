// Small helpers for the attendance screen.
// A "status" is true (Present), false (Absent) or null (Not recorded).

// Today's date as "YYYY-MM-DD" on the laptop's own calendar.
// (toISOString() would use UTC time and can give yesterday or tomorrow.)
export function todayLocal(now = new Date()) {
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// rows: [{ student_id, name, present }] from the API.
// New date (nothing saved for anyone) -> everyone starts Absent.
// Date already saved -> keep what was saved; null stays "Not recorded".
export function initialStatuses(rows) {
  const isNewDate = rows.every((r) => r.present === null)
  return Object.fromEntries(rows.map((r) => [r.student_id, isNewDate ? false : r.present]))
}

// Only students marked Present or Absent are sent; "Not recorded" is left alone.
export function recordsToSave(statuses) {
  return Object.entries(statuses)
    .filter(([, present]) => present !== null)
    .map(([id, present]) => ({ student_id: Number(id), present }))
}

// "2026-11-06" -> "Fri, 6 Nov 2026" (read as a local date, not UTC).
export function formatDate(isoDate) {
  const [y, m, d] = isoDate.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
