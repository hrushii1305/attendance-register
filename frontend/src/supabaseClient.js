import { createClient } from '@supabase/supabase-js'

// Only the PUBLISHABLE key lives in the browser. It can log in, but the
// database tables are locked, so it can't read or change any data.
const url = import.meta.env.VITE_SUPABASE_URL
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY

if (!url || !key) {
  throw new Error('Missing VITE_SUPABASE_URL or VITE_SUPABASE_PUBLISHABLE_KEY in frontend/.env')
}

export const supabase = createClient(url, key)
