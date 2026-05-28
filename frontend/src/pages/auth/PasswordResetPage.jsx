import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { passwordResetRequest, passwordResetConfirm } from '../../api/auth'
import AuthLayout from '../../components/AuthLayout'
import PasswordRequirements, { getPasswordRequirements } from '../../components/PasswordRequirements'
import { extractError, extractFieldErrors } from '../../utils/errors'

export default function PasswordResetPage() {
  const [searchParams] = useSearchParams()
  const uid   = searchParams.get('uid')
  const token = searchParams.get('token')
  const isConfirm = !!(uid && token)
  const tokenKey = isConfirm ? `pw_reset_done:${uid}:${token}` : null

  // Request state
  const [email, setEmail]     = useState('')
  const [sent, setSent]       = useState(false)

  // Confirm state
  const [form, setForm]       = useState({ new_password: '', new_password_confirm: '' })
  const [done, setDone]       = useState(false)

  const [errors, setErrors]   = useState({})
  const [loading, setLoading] = useState(false)
  const { allMet: resetReady } = getPasswordRequirements({
    password: form.new_password,
    confirmPassword: form.new_password_confirm,
  })

  useEffect(() => {
    if (!tokenKey) return
    const alreadyDone = sessionStorage.getItem(tokenKey)
    if (alreadyDone) setDone(true)
  }, [tokenKey])

  const handleRequest = async (e) => {
    e.preventDefault()
    setLoading(true)
    setErrors({})
    try {
      await passwordResetRequest(email)
      setSent(true)
    } catch {
      setSent(true) // always show success per your backend spec
    } finally {
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
      // Safe to show real errors here — user already has the reset link
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

  // ── Confirm: success ──────────────────────────────────────────────────────
  if (isConfirm && done) return (
    <AuthLayout
      brandHeading="You're all set"
      brandSubtext="Your password has been updated successfully."
    >
      <div className="auth-success-icon">✓</div>
      <div className="auth-success-text">
        <h1>Password reset</h1>
        <p>Your password has been updated. You can now log in.</p>
        <Link to="/login" replace className="auth-btn-link-block">
          Go to login
        </Link>
      </div>
    </AuthLayout>
  )

  // ── Confirm: form ─────────────────────────────────────────────────────────
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
            value={form.new_password}
            onChange={e => setForm(f => ({ ...f, new_password: e.target.value }))}
            placeholder="••••••••"
            className="auth-input"
          />
          {errors.new_password && <p className="auth-field-error">{errors.new_password}</p>}
        </div>

        <PasswordRequirements
          password={form.new_password}
          confirmPassword={form.new_password_confirm}
        />

        <div className="auth-field">
          <label className="auth-label" htmlFor="reset-new-password-confirm">Confirm password</label>
          <input
            id="reset-new-password-confirm"
            type="password"
            required
            value={form.new_password_confirm}
            onChange={e => setForm(f => ({ ...f, new_password_confirm: e.target.value }))}
            placeholder="••••••••"
            className="auth-input"
          />
          {errors.new_password_confirm && (
            <p className="auth-field-error">{errors.new_password_confirm}</p>
          )}
        </div>

        {errors._general && <p className="auth-error">{errors._general}</p>}

        <button type="submit" disabled={loading || !resetReady} className="auth-btn-primary">
          {loading ? 'Saving…' : 'Reset password'}
        </button>
      </form>
    </AuthLayout>
  )

  // ── Request: sent ─────────────────────────────────────────────────────────
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
        </p>
        <Link to="/login" replace className="auth-btn-text">Back to login</Link>
      </div>
    </AuthLayout>
  )

  // ── Request: form ─────────────────────────────────────────────────────────
  return (
    <AuthLayout
      brandHeading="Reset your password"
      brandSubtext="Happens to the best of us. We'll help you get back into your account."
    >
      <h1 className="auth-form-title">Reset your password</h1>
      <p className="auth-form-subtitle">Enter your email and we'll send you a reset link.</p>

      <form onSubmit={handleRequest} className="auth-form">
        <div className="auth-field">
          <label className="auth-label" htmlFor="reset-email">Email address</label>
          <input
            id="reset-email"
            type="email"
            required
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="auth-input"
          />
        </div>

        <button type="submit" disabled={loading} className="auth-btn-primary">
          {loading ? 'Sending…' : 'Send reset link'}
        </button>
      </form>

      <p className="auth-footer">
        <Link to="/login" replace>Back to login</Link>
      </p>
    </AuthLayout>
  )
}