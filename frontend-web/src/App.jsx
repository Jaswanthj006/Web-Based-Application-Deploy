import { useState, useCallback } from 'react'
import { LoginForm } from './LoginForm'
import { Dashboard } from './Dashboard'
import { api } from './api'

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [user, setUser] = useState(() => localStorage.getItem('user') || null)

  const login = useCallback((t, u) => {
    localStorage.setItem('token', t)
    localStorage.setItem('user', u)
    setToken(t)
    setUser(u)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }, [])

  if (!token) {
    return <LoginForm onLogin={login} />
  }

  return <Dashboard user={user} onLogout={logout} />
}
