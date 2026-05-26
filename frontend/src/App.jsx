import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'

import LoginPage           from './pages/auth/LoginPage'
import RegisterPage        from './pages/auth/RegisterPage'
import VerifyEmailPage     from './pages/auth/VerifyEmailPage'
import CompleteProfilePage from './pages/auth/CompleteProfilePage'
import PasswordResetPage   from './pages/auth/PasswordResetPage'

import DashboardPage  from './pages/account/DashboardPage'
import ProfilePage    from './pages/account/ProfilePage'
import AddressesPage  from './pages/account/AddressesPage'
import SecurityPage   from './pages/account/SecurityPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login"            element={<LoginPage />} />
      <Route path="/register"         element={<RegisterPage />} />
      <Route path="/verify-email"     element={<VerifyEmailPage />} />
      <Route path="/complete-profile" element={<CompleteProfilePage />} />
      <Route path="/reset-password"   element={<PasswordResetPage />} />

      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/dashboard/profile"   element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
      <Route path="/dashboard/addresses" element={<ProtectedRoute><AddressesPage /></ProtectedRoute>} />
      <Route path="/dashboard/security"  element={<ProtectedRoute><SecurityPage /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}