import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { passwordResetRequest, passwordResetConfirm } from '../../api/auth'
import AuthLayout from '../../components/AuthLayout'
import PasswordRequirements, { getPasswordRequirements } from '../../components/PasswordRequirements'
import { extractError, extractFieldErrors } from '../../utils/errors'

export default function PasswordResetPage() {
  const [searchParams] = useSearchParams()
  const uid   = searchParams.get('uid')
  const token = searchParams.get('token')

  // If both uid + token are in the URL we're in "confirm" mode,
  // otherwise we show the "request" (enter email) form.
  const isConfirm = !!(uid && token)

  // ── Request state ─────────────────────────────────────────────────────────
  const [email, setEmail]   = useState('')
  const [sent, setSent]     = useState(false)

  // ── Confirm state ─────────────────────────────────────────────────────────
  const [form, setForm]     = useState({ new_password: '', new_password_confirm: '' })
  const [done, setDone]     = useState(false)

  // ── Shared state ──────────────────────────────────────────────────────────
  const [errors, setErrors]   = useState({})
  const [loading, setLoading] = useState(false)

  const { allMet: resetReady } = getPasswordRequirements({
    password:        form.new_password,
    confirmPassword: form.new_password_confirm,
  })

  // Guard: prevent replaying a used reset link (stored in sessionStorage)
  const tokenKey = isConfirm ? `pw_reset_done:${uid}:${token}` : null
  useEffect(() => {
    if (!tokenKey) return
    if (sessionStorage.getItem(tokenKey)) setDone(true)
  }, [tokenKey])

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleRequest = async (e) => {
    e.preventDefault()
    setLoading(true)
    setErrors({})
    try {
      await passwordResetRequest(email.trim())
    } catch {
      // Backend always returns 200 to prevent user enumeration — swallow error
    } finally {
      setSent(true)
      setLoading(false)
    }
  }

  const handleConfirm = async (e) => {
    e.preventDefault()
    setLoading(true)
    setErrors({})
    try {
      await passwordResetConfirm(uid, token, form.new_password, form.new_password_confirm)
      if (tokenKey) sessionStorage.setItem(tokenKey, '1')
      setDone(true)
    } catch (err) {
      const fieldErrs = extractFieldErrors(err)
      if (Object.keys(fieldErrs).length > 0) {
        setErrors(fieldErrs)
      } else {
        setErrors({ _general: extractError(err, 'Reset failed. The link may have expired.') })
      }
    } finally {
      setLoading(false)
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // CONFIRM — success screen
  // ─────────────────────────────────────────────────────────────────────────
  if (isConfirm && done) return (
    <AuthLayout
      brandHeading="You're all set"
      brandSubtext="Your password has been updated successfully."
    >
      <div className="auth-success-icon">✓</div>
      <div className="auth-success-text">
        <h1>Password reset</h1>
        <p>Your password has been updated. You can now log in with your new password.</p>
        <Link to="/login" replace className="auth-btn-link-block">
          Go to login
        </Link>
      </div>
    </AuthLayout>
  )

  // ─────────────────────────────────────────────────────────────────────────
  // CONFIRM — set new password form
  // ─────────────────────────────────────────────────────────────────────────
  if (isConfirm) return (
    <AuthLayout
      brandHeading="Set new password"
      brandSubtext="Choose a strong, unique password to protect your account."
    >
      <h1 className="auth-form-title">Set new password</h1>
      <p className="auth-form-subtitle">Choose a strong password for your account.</p>

      <form onSubmit={handleConfirm} className="auth-form">

        <div className="auth-field">
          <label className="auth-label" htmlFor="reset-new-password">New password</label>
          <input
            id="reset-new-password"
            type="password"
            required
            autoFocus
            value={form.new_password}
            onChange={(e) => setForm((f) => ({ ...f, new_password: e.target.value }))}
            placeholder="••••••••"
            className="auth-input"
          />
          {errors.new_password && (
            <p className="auth-field-error">{errors.new_password[0]}</p>
          )}
        </div>

        {/* Show checklist as soon as user starts typing */}
        {form.new_password && (
          <PasswordRequirements
            password={form.new_password}
            confirmPassword={form.new_password_confirm}
          />
        )}

        <div className="auth-field">
          <label className="auth-label" htmlFor="reset-confirm-password">Confirm password</label>
          <input
            id="reset-confirm-password"
            type="password"
            required
            value={form.new_password_confirm}
            onChange={(e) => setForm((f) => ({ ...f, new_password_confirm: e.target.value }))}
            placeholder="••••••••"
            className="auth-input"
          />
          {errors.new_password_confirm && (
            <p className="auth-field-error">{errors.new_password_confirm[0]}</p>
          )}
        </div>

        {errors._general && <p className="auth-error">{errors._general}</p>}

        <button
          type="submit"
          disabled={loading || !resetReady}
          className="auth-btn-primary"
        >
          {loading ? 'Saving…' : 'Reset password'}
        </button>
      </form>
    </AuthLayout>
  )

  // ─────────────────────────────────────────────────────────────────────────
  // REQUEST — email sent success screen
  // ─────────────────────────────────────────────────────────────────────────
  if (sent) return (
    <AuthLayout
      brandHeading="Check your inbox"
      brandSubtext="We've sent a password reset link to your email address."
    >
      <div className="auth-success-icon">✉</div>
      <div className="auth-success-text">
        <h1>Check your inbox</h1>
        <p>
          If <strong>{email}</strong> is registered, you'll receive a reset link shortly.
          Don't forget to check your spam folder.
        </p>
        <Link to="/login" replace className="auth-btn-text">
          ← Back to login
        </Link>
      </div>
    </AuthLayout>
  )

  // ─────────────────────────────────────────────────────────────────────────
  // REQUEST — enter email form
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <AuthLayout
      brandHeading="Reset your password"
      brandSubtext="Happens to the best of us. We'll help you get back into your account."
    >
      <h1 className="auth-form-title">Forgot password?</h1>
      <p className="auth-form-subtitle">
        Enter your email and we'll send you a reset link.
      </p>

      <form onSubmit={handleRequest} className="auth-form">
        <div className="auth-field">
          <label className="auth-label" htmlFor="reset-email">Email address</label>
          <input
            id="reset-email"
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="auth-input"
          />
        </div>

        <button
          type="submit"
          disabled={loading || !email.trim()}
          className="auth-btn-primary"
        >
          {loading ? 'Sending…' : 'Send reset link'}
        </button>
      </form>

      <p className="auth-footer">
        <Link to="/login">← Back to login</Link>
      </p>
    </AuthLayout>
  )
}