import { supabase } from './supabaseClient'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Sends a request to the FastAPI backend with the teacher's login token.
async function request(path, { method = 'GET', body } = {}) {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token

  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let res
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new Error("Can't reach the server. Is the backend running?")
  }

  if (res.status === 401) {
    // Token missing or expired: log out, which sends the teacher back to the login screen.
    await supabase.auth.signOut()
    throw new Error('Your session has ended. Please log in again.')
  }

  const payload = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = payload?.detail
    throw new Error(typeof detail === 'string' ? detail : `Request failed (${res.status})`)
  }
  return payload
}

export const getStudents = () => request('/students')

export const addStudent = (name) => request('/students', { method: 'POST', body: { name } })

export const getAttendance = (date) => request(`/attendance?date=${encodeURIComponent(date)}`)

export const saveAttendance = (date, records) =>
  request('/attendance', { method: 'PUT', body: { date, records } })

export const getSavedDates = () => request('/attendance/dates')
