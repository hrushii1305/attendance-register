import { useEffect, useState } from 'react'
import { supabase } from './supabaseClient'
import Login from './Login'
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

  return (
    <div className="app">
      <header className="topbar">
        <h1>Attendance Register</h1>
        <button onClick={() => supabase.auth.signOut()}>Log out</button>
      </header>
      <main>
        <p>Logged in as {session.user.email}.</p>
      </main>
    </div>
  )
}
