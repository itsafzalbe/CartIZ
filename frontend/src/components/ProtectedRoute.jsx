import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <span className="text-gray-400 text-sm">Loading…</span>
    </div>
  )
  return user ? children : <Navigate to="/login" replace />
}
