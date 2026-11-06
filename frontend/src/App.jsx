import { useCallback, useEffect, useState } from 'react'
import { supabase } from './supabaseClient'
import { addStudent, getSavedDates, getStudents } from './api'
import { todayLocal } from './attendanceState'
import Login from './Login'
import Students from './Students'
import Attendance from './Attendance'
import PastDates from './PastDates'
import './App.css'

export default function App() {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Is someone already logged in (e.g. after a page refresh)?
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setLoading(false)
    })
    // Keep `session` up to date when the teacher logs in or out.
    const { data } = supabase.auth.onAuthStateChange((_event, newSession) => setSession(newSession))
    return () => data.subscription.unsubscribe()
  }, [])

  if (loading) return null
  if (!session) return <Login />
  return <MainScreen email={session.user.email} />
}

function MainScreen({ email }) {
  const [students, setStudents] = useState([])
  const [savedDates, setSavedDates] = useState([])
  const [date, setDate] = useState(todayLocal())
  const [error, setError] = useState('')

  const loadStudents = useCallback(() => getStudents().then(setStudents), [])
  const loadSavedDates = useCallback(
    () => getSavedDates().then(setSavedDates).catch((err) => setError(err.message)),
    [],
  )

  useEffect(() => {
    loadStudents().catch((err) => setError(err.message))
    loadSavedDates()
  }, [loadStudents, loadSavedDates])

  async function handleAdd(name) {
    await addStudent(name) // errors are shown by the Students section
    await loadStudents()
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>Attendance Register</h1>
        <div className="who">
          <span className="muted">{email}</span>
          <button onClick={() => supabase.auth.signOut()}>Log out</button>
        </div>
      </header>
      {error && <p className="error" role="alert">{error}</p>}
      <Attendance date={date} onDateChange={setDate} students={students} onSaved={loadSavedDates} />
      <PastDates dates={savedDates} selected={date} onPick={setDate} />
      <Students students={students} onAdd={handleAdd} />
    </div>
  )
}
