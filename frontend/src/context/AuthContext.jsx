import { createContext, useState, useEffect } from 'react'
import { getAccess, setTokens, clearTokens } from '../utils/token'
import client from '../api/client'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (getAccess()) {
      client.get('/accounts/me/')
        .then(res => setUser(res.data.data))
        .catch(() => clearTokens())
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = (tokens, userData) => {
    setTokens(tokens)
    setUser(userData)
  }

  const logout = () => {
    clearTokens()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, setUser, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}
