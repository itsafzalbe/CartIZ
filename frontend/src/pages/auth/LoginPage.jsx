import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login as loginApi } from '../../api/auth'
import { useAuth } from '../../hooks/useAuth'
import AuthLayout from '../../components/AuthLayout'
import GoogleIcon from '../../components/GoogleIcon'
import { extractError } from '../../utils/errors'

const API_URL = import.meta.env.VITE_API_URL ?? ''

export default function LoginPage() {
  const navigate   = useNavigate()
  const { login }  = useAuth()

  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  // ── Submit ─────────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await loginApi(email, password)
      const { access, refresh, user } = res.data.data
      login({ access, refresh }, user)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      // The backend returns non_field_errors for bad credentials / lock-outs
      const data   = err.response?.data
      const errors = data?.errors ?? {}
      setError(
        errors.non_failed_errors?.[0] ??
        errors.non_field_errors?.[0]  ??
        errors.email?.[0]             ??
        extractError(err, 'Login failed. Please try again.')
      )
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignIn = () => {
    window.location.href = `${API_URL}/accounts/google/redirect/`
  }

  return (
    <AuthLayout
      brandHeading="Welcome back to CartIZ"
      brandSubtext="Sign in to access your cart, track orders, and discover great deals."
    >
      <h1 className="auth-form-title">Welcome back</h1>
      <p className="auth-form-subtitle">Sign in to your CartIZ account.</p>

      <form onSubmit={handleSubmit} className="auth-form">

        {/* Email */}
        <div className="auth-field">
          <label className="auth-label" htmlFor="login-email">Email address</label>
          <input
            id="login-email"
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="auth-input"
          />
        </div>

        {/* Password */}
        <div className="auth-field">
          <div className="auth-label-row">
            <label className="auth-label" htmlFor="login-password">Password</label>
            <Link to="/reset-password" className="auth-link-small">
              Forgot password?
            </Link>
          </div>
          <input
            id="login-password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="auth-input"
          />
        </div>

        {error && <p className="auth-error">{error}</p>}

        <button
          type="submit"
          disabled={loading || !email || !password}
          className="auth-btn-primary"
        >
          {loading ? 'Signing in…' : 'Sign in'}
        </button>

        <div className="auth-divider">
          <span className="auth-divider-text">or</span>
        </div>

        <button type="button" onClick={handleGoogleSignIn} className="auth-btn-google">
          <GoogleIcon />
          Continue with Google
        </button>
      </form>

      <p className="auth-footer">
        Don't have an account?{' '}
        <Link to="/register">Sign up</Link>
      </p>
    </AuthLayout>
  )
}