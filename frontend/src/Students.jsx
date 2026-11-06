import { useState } from 'react'

export default function Students({ students, onAdd }) {
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await onAdd(name)
      setName('')
    } catch (err) {
      setError(err.message)
    }
    setBusy(false)
  }

  return (
    <section className="card">
      <h2>Students ({students.length})</h2>
      <form className="add-student" onSubmit={handleSubmit}>
        <input
          aria-label="Student name"
          placeholder="Student name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button type="submit" className="primary" disabled={busy}>
          Add
        </button>
      </form>
      {error && <p className="error" role="alert">{error}</p>}
      {students.length === 0 ? (
        <p className="muted">No students yet.</p>
      ) : (
        <ul className="student-list">
          {students.map((s) => (
            <li key={s.id}>{s.name}</li>
          ))}
        </ul>
      )}
    </section>
  )
}
