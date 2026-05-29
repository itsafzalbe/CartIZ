import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { registerEmail, checkEmailExists } from '../../api/auth'
import AuthLayout from '../../components/AuthLayout'
import GoogleIcon from '../../components/GoogleIcon'
import { extractError, extractFieldErrors } from '../../utils/errors'

const API_URL = import.meta.env.VITE_API_URL ?? ''

export default function RegisterPage() {
  const navigate = useNavigate()

  const [email, setEmail]               = useState('')
  const [errors, setErrors]             = useState({})
  const [loading, setLoading]           = useState(false)
  const [emailExists, setEmailExists]   = useState(false)
  const [checkingEmail, setCheckingEmail] = useState(false)

  const checkTimer = useRef(null)

  // ── Debounced email-exists check ──────────────────────────────────────────
  useEffect(() => {
    if (checkTimer.current) clearTimeout(checkTimer.current)

    const trimmed = email.trim()
    if (!trimmed || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
      setEmailExists(false)
      setCheckingEmail(false)
      return
    }

    setCheckingEmail(true)
    checkTimer.current = setTimeout(async () => {
      try {
        const res = await checkEmailExists(trimmed)
        setEmailExists(!!res.data?.data?.exists)
      } catch {
        setEmailExists(false)
      } finally {
        setCheckingEmail(false)
      }
    }, 400)

    return () => clearTimeout(checkTimer.current)
  }, [email])

  // ── Submit ─────────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrors({})
    setLoading(true)
    try {
      await registerEmail(email.trim())
      navigate('/verify-email', { state: { email: email.trim() } })
    } catch (err) {
      const fieldErrs = extractFieldErrors(err)
      const general   = extractError(err, null)
      setErrors({
        ...fieldErrs,
        ...(Object.keys(fieldErrs).length === 0 && general ? { _general: general } : {}),
      })
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignUp = () => {
    window.location.href = `${API_URL}/accounts/google/redirect/`
  }

  const canSubmit = email.trim() && !emailExists && !checkingEmail && !loading

  return (
    <AuthLayout
      brandHeading="Join CartIZ today"
      brandSubtext="Create your account and start discovering amazing products at the best prices."
    >
      <h1 className="auth-form-title">Create your account</h1>
      <p className="auth-form-subtitle">
        We'll send a 5-digit verification code to your email.
      </p>

      <form onSubmit={handleSubmit} className="auth-form">

        {/* Email */}
        <div className="auth-field">
          <label className="auth-label" htmlFor="register-email">Email address</label>
          <input
            id="register-email"
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="auth-input"
          />
          {/* Field-level errors from backend */}
          {errors.email && (
            <p className="auth-field-error">{errors.email[0]}</p>
          )}
          {/* Client-side email-exists warning */}
          {!errors.email && emailExists && (
            <p className="auth-field-error">
              This email is already registered.{' '}
              <Link to="/login" style={{ fontWeight: 600 }}>Sign in instead?</Link>
            </p>
          )}
          {!errors.email && !emailExists && checkingEmail && (
            <p className="auth-field-help">Checking…</p>
          )}
        </div>

        {/* General / non-field error */}
        {errors._general && (
          <p className="auth-error">{errors._general}</p>
        )}

        <button
          type="submit"
          disabled={!canSubmit}
          className="auth-btn-primary"
        >
          {loading ? 'Sending code…' : 'Continue'}
        </button>

        <div className="auth-divider">
          <span className="auth-divider-text">or</span>
        </div>

        <button type="button" onClick={handleGoogleSignUp} className="auth-btn-google">
          <GoogleIcon />
          Continue with Google
        </button>
      </form>

      <p className="auth-footer">
        Already have an account?{' '}
        <Link to="/login">Sign in</Link>
      </p>
    </AuthLayout>
  )
}