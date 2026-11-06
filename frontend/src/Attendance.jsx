import { useEffect, useRef, useState } from 'react'
import { getAttendance, saveAttendance } from './api'
import { initialStatuses, recordsToSave } from './attendanceState'

export default function Attendance({ date, onDateChange, students, onSaved }) {
  const [rows, setRows] = useState([])
  const [statuses, setStatuses] = useState({})
  const [loadedFor, setLoadedFor] = useState({ date: null, students: null })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [savedMessage, setSavedMessage] = useState(false)
  const loadedDate = useRef(null)

  // Load the chosen date. Runs again when the date changes or a student is added.
  useEffect(() => {
    if (!date) return
    let cancelled = false
    getAttendance(date)
      .then((data) => {
        if (cancelled) return
        // Decide NOW whether this is the same date reloaded (a student was added).
        // Don't read the ref inside the setStatuses updater: React may run that
        // updater later, after the ref has already changed.
        const sameDate = loadedDate.current === date
        loadedDate.current = date
        const fresh = initialStatuses(data)
        if (sameDate) {
          // Keep the clicks already made for students who are still listed.
          setStatuses((prev) => {
            const kept = Object.fromEntries(Object.entries(prev).filter(([id]) => id in fresh))
            return { ...fresh, ...kept }
          })
        } else {
          setStatuses(fresh)
          setSavedMessage(false)
        }
        setError('')
        setRows(data)
        setLoadedFor({ date, students })
      })
      .catch((err) => {
        if (cancelled) return
        // Clear the old date's rows so they can't be saved under this date.
        loadedDate.current = null
        setRows([])
        setStatuses({})
        setError(err.message)
        setLoadedFor({ date, students })
      })
    return () => {
      cancelled = true
    }
  }, [date, students])

  // Hide the "Saved" message after a few seconds.
  useEffect(() => {
    if (!savedMessage) return
    const timer = setTimeout(() => setSavedMessage(false), 3000)
    return () => clearTimeout(timer)
  }, [savedMessage])

  function setStatus(studentId, present) {
    setStatuses((prev) => ({ ...prev, [studentId]: present }))
    setSavedMessage(false)
  }

  function markAllPresent() {
    setStatuses(Object.fromEntries(rows.map((r) => [r.student_id, true])))
    setSavedMessage(false)
  }

  async function handleSave() {
    setSaving(true)
    setError('')
    try {
      await saveAttendance(date, recordsToSave(statuses))
      setSavedMessage(true)
      onSaved()
    } catch (err) {
      setError(err.message)
    }
    setSaving(false)
  }

  // Still loading if the last finished load was for a different date or student list.
  const loading = Boolean(date) && (loadedFor.date !== date || loadedFor.students !== students)
  const disabled = !date || loading || saving || rows.length === 0

  return (
    <section className="card">
      <div className="section-head">
        <h2>Attendance</h2>
        <input
          type="date"
          aria-label="Attendance date"
          value={date}
          onChange={(e) => onDateChange(e.target.value)}
        />
      </div>

      {!date && <p className="muted">Pick a date.</p>}
      {date && students.length === 0 && <p className="muted">Add a student first.</p>}

      {date && rows.length > 0 && (
        <ul className="attendance-list">
          {rows.map((r) => {
            const status = statuses[r.student_id] ?? null
            return (
              <li key={r.student_id}>
                <span className="student-name">
                  {r.name}
                  {status === null && <span className="not-recorded">Not recorded</span>}
                </span>
                <span className="toggle" role="group" aria-label={`Attendance for ${r.name}`}>
                  <button
                    className={status === true ? 'present selected' : 'present'}
                    aria-pressed={status === true}
                    onClick={() => setStatus(r.student_id, true)}
                    disabled={loading}
                  >
                    Present
                  </button>
                  <button
                    className={status === false ? 'absent selected' : 'absent'}
                    aria-pressed={status === false}
                    onClick={() => setStatus(r.student_id, false)}
                    disabled={loading}
                  >
                    Absent
                  </button>
                </span>
              </li>
            )
          })}
        </ul>
      )}

      {error && <p className="error" role="alert">{error}</p>}

      <div className="actions">
        <button onClick={markAllPresent} disabled={disabled}>
          Mark all present
        </button>
        <button className="primary" onClick={handleSave} disabled={disabled}>
          {saving ? 'Saving…' : 'Save'}
        </button>
        {savedMessage && <span className="saved" role="status">Saved ✓</span>}
      </div>
    </section>
  )
}
