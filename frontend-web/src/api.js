const BASE = '/api'

function getToken() {
  return localStorage.getItem('token')
}

function headers(includeAuth = false) {
  const h = { 'Content-Type': 'application/json' }
  if (includeAuth) {
    const t = getToken()
    if (t) h['Authorization'] = `Token ${t}`
  }
  return h
}

export const api = {
  async login(username, password) {
    const res = await fetch(`${BASE}/auth/login/`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || 'Login failed')
    }
    return res.json()
  },

  async register(username, password) {
    const res = await fetch(`${BASE}/auth/register/`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || 'Registration failed')
    }
    return res.json()
  },

  async upload(file, name) {
    const form = new FormData()
    form.append('file', file)
    if (name) form.append('name', name)
    const res = await fetch(`${BASE}/upload/`, {
      method: 'POST',
      headers: { Authorization: `Token ${getToken()}` },
      body: form,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || 'Upload failed')
    }
    return res.json()
  },

  async history() {
    const res = await fetch(`${BASE}/history/`)
    if (!res.ok) throw new Error('Failed to load history')
    return res.json()
  },

  async summary(id) {
    const res = await fetch(`${BASE}/summary/${id}/`)
    if (!res.ok) throw new Error('Failed to load summary')
    return res.json()
  },

  async data(id) {
    const res = await fetch(`${BASE}/data/${id}/`)
    if (!res.ok) throw new Error('Failed to load data')
    return res.json()
  },

  reportPdfUrl(id) {
    return `${BASE}/report/${id}/pdf/?token=${getToken()}`
  },
}
