import { useEffect, useRef, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { checkEmailExists, registerEmail } from '../../api/auth'
import AuthLayout from '../../components/AuthLayout'
import GoogleIcon from '../../components/GoogleIcon'
import PasswordRequirements, { getPasswordRequirements } from '../../components/PasswordRequirements'
import { extractError, extractFieldErrors } from '../../utils/errors'

const API_URL = import.meta.env.VITE_API_URL ?? ''

export default function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm]   = useState({
    email: '',
    first_name: '',
    last_name: '',
    username: '',
    password: '',
    password_confirm: '',
  })
  const [errors, setErrors]   = useState({})
  const [loading, setLoading] = useState(false)
  const [emailExists, setEmailExists] = useState(false)
  const [checkingEmail, setCheckingEmail] = useState(false)
  const checkTimer = useRef(null)
  const { allMet: passwordReady } = getPasswordRequirements({
    password: form.password,
    confirmPassword: form.password_confirm,
  })
  useEffect(() => {
    const email = form.email.trim()
    if (checkTimer.current) {
      clearTimeout(checkTimer.current)
    }
    if (!email) {
      setEmailExists(false)
      setCheckingEmail(false)
      return
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailExists(false)
      setCheckingEmail(false)
      return
    }

    setCheckingEmail(true)
    checkTimer.current = setTimeout(async () => {
      try {
        const res = await checkEmailExists(email)
        setEmailExists(!!res.data?.data?.exists)
      } catch {
        setEmailExists(false)
      } finally {
        setCheckingEmail(false)
      }
    }, 400)

    return () => clearTimeout(checkTimer.current)
  }, [form.email])

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrors({})
    setLoading(true)
    try {
      await registerEmail(form)
      navigate('/verify-email', { state: { email: form.email } })
    } catch (err) {
      const fieldErrs = extractFieldErrors(err)
      const general = extractError(err, null)
      setErrors({
        ...fieldErrs,
        ...(general ? { _general: general } : {}),
      })
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignUp = () => {
    window.location.href = `${API_URL}/accounts/google/login/`
  }

  return (
    <AuthLayout
      brandHeading="Join CartIZ today"
      brandSubtext="Create your account and start discovering amazing products at the best prices."
    >
      <h1 className="auth-form-title">Create your account</h1>
      <p className="auth-form-subtitle">We'll send a verification code to your email.</p>

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="auth-field-grid">
          <div className="auth-field">
            <label className="auth-label" htmlFor="register-first">First name</label>
            <input
              id="register-first"
              type="text"
              required
              value={form.first_name}
              onChange={set('first_name')}
              placeholder="Alex"
              className="auth-input"
            />
            {errors.first_name && <p className="auth-field-error">{errors.first_name}</p>}
          </div>
          <div className="auth-field">
            <label className="auth-label" htmlFor="register-last">Last name</label>
            <input
              id="register-last"
              type="text"
              required
              value={form.last_name}
              onChange={set('last_name')}
              placeholder="Smith"
              className="auth-input"
            />
            {errors.last_name && <p className="auth-field-error">{errors.last_name}</p>}
          </div>
        </div>

        <div className="auth-field">
          <label className="auth-label" htmlFor="register-email">Email address</label>
          <input
            id="register-email"
            type="email"
            required
            value={form.email}
            onChange={set('email')}
            placeholder="you@example.com"
            className="auth-input"
          />
          {errors.email && <p className="auth-field-error">{errors.email}</p>}
          {!errors.email && emailExists && (
            <p className="auth-field-error">This email is already registered.</p>
          )}
          {!errors.email && !emailExists && checkingEmail && (
            <p className="auth-field-help">Checking email…</p>
          )}
        </div>

        <div className="auth-field">
          <label className="auth-label" htmlFor="register-username">Username</label>
          <input
            id="register-username"
            type="text"
            required
            value={form.username}
            onChange={set('username')}
            placeholder="alex_smith"
            className="auth-input"
          />
          {errors.username && <p className="auth-field-error">{errors.username}</p>}
        </div>

        <div className="auth-field">
          <label className="auth-label" htmlFor="register-password">Password</label>
          <input
            id="register-password"
            type="password"
            required
            value={form.password}
            onChange={set('password')}
            placeholder="••••••••"
            className="auth-input"
          />
          {errors.password && <p className="auth-field-error">{errors.password}</p>}
        </div>

        <PasswordRequirements
          password={form.password}
          confirmPassword={form.password_confirm}
        />

        <div className="auth-field">
          <label className="auth-label" htmlFor="register-password-confirm">Confirm password</label>
          <input
            id="register-password-confirm"
            type="password"
            required
            value={form.password_confirm}
            onChange={set('password_confirm')}
            placeholder="••••••••"
            className="auth-input"
          />
          {errors.password_confirm && (
            <p className="auth-field-error">{errors.password_confirm}</p>
          )}
        </div>

        {(errors.non_field_errors || errors._general) && (
          <p className="auth-error">
            {errors._general || errors.non_field_errors?.[0] || errors.non_field_errors}
          </p>
        )}

        <button
          type="submit"
          disabled={loading || !passwordReady || emailExists || checkingEmail}
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