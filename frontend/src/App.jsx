import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/auth/ProtectedRoute'

import LoginPage           from './pages/auth/LoginPage'
import RegisterPage        from './pages/auth/RegisterPage'
import VerifyEmailPage     from './pages/auth/VerifyEmailPage'
import CompleteProfilePage from './pages/auth/CompleteProfilePage'
import ForgotPasswordPage  from './pages/auth/ForgotPasswordPage'
import PasswordResetPage   from './pages/auth/PasswordResetPage'

import DashboardPage    from './pages/account/DashboardPage'
import ProfilePage      from './pages/account/ProfilePage'
import AddressesPage    from './pages/account/AddressesPage'
import SecurityPage     from './pages/account/SecurityPage'
import BecomeSellerPage from './pages/account/BecomeSellerPage'
import SellerPage       from './pages/account/SellerPage'
import SellerStatsPage  from './pages/account/SellerStatsPage'

import GoogleCallbackPage from './pages/auth/GoogleCallbackPage'

export default function App() {
  return (
    <Routes>
      {/* Auth */}
      <Route path="/login"             element={<LoginPage />} />
      <Route path="/register"          element={<RegisterPage />} />
      <Route path="/verify-email"      element={<VerifyEmailPage />} />
      <Route path="/complete-profile"  element={<CompleteProfilePage />} />
      <Route path="/forgot-password"   element={<ForgotPasswordPage />} />
      <Route path="/reset-password"    element={<PasswordResetPage />} />

      {/* Dashboard */}
      <Route path="/dashboard"                element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/dashboard/profile"        element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
      <Route path="/dashboard/addresses"      element={<ProtectedRoute><AddressesPage /></ProtectedRoute>} />
      <Route path="/dashboard/security"       element={<ProtectedRoute><SecurityPage /></ProtectedRoute>} />
      <Route path="/dashboard/become-seller"  element={<ProtectedRoute><BecomeSellerPage /></ProtectedRoute>} />
      <Route path="/dashboard/seller"         element={<ProtectedRoute><SellerPage /></ProtectedRoute>} />
      <Route path="/dashboard/seller/stats"   element={<ProtectedRoute><SellerStatsPage /></ProtectedRoute>} />

      <Route path="/auth/callback" element={<GoogleCallbackPage />} />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}