import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { completeProfile } from '../../api/auth'
import { useAuth } from '../../hooks/useAuth'
import AuthLayout from '../../components/auth/AuthLayout'
import PasswordRequirements, { getPasswordRequirements } from '../../components/auth/PasswordRequirements'
import { extractError, extractFieldErrors } from '../../utils/errors'

// ── Reusable field ─────────────────────────────────────────────────────────
function Field({ label, id, type = 'text', placeholder, value, onChange, error, autoFocus }) {
  return (
    <div className="auth-field">
      <label className="auth-label" htmlFor={id}>{label}</label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="auth-input"
        autoFocus={autoFocus}
      />
      {error && <p className="auth-field-error">{error}</p>}
    </div>
  )
}

export default function CompleteProfilePage() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const { login } = useAuth()

  // Must arrive with user_id + email passed via router state from VerifyEmailPage
  const { user_id, email } = location.state ?? {}

  const [form, setForm] = useState({
    first_name:       '',
    last_name:        '',
    username:         '',
    password:         '',
    password_confirm: '',
  })
  const [errors, setErrors]   = useState({})
  const [loading, setLoading] = useState(false)

  // ── Guard: must have user_id ───────────────────────────────────────────────
  if (!user_id) {
    navigate('/register', { replace: true })
    return null
  }

  const { allMet: passwordReady } = getPasswordRequirements({
    password:        form.password,
    confirmPassword: form.password_confirm,
  })

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))

  // ── Submit ─────────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrors({})
    setLoading(true)
    try {
      const res = await completeProfile(user_id, form)
      const { access, refresh } = res.data.data
      // Log the user in immediately — backend issues tokens on profile completion
      login({ access, refresh }, { email })
      navigate('/dashboard', { replace: true })
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

  const canSubmit =
    form.first_name.trim() &&
    form.last_name.trim() &&
    form.username.trim() &&
    passwordReady &&
    !loading

  return (
    <AuthLayout
      brandHeading="Almost done!"
      brandSubtext="Just a few more details and you're all set to start shopping."
    >
      <h1 className="auth-form-title">Complete your profile</h1>
      <p className="auth-form-subtitle">
        Setting up account for <strong>{email}</strong>
      </p>

      <form onSubmit={handleSubmit} className="auth-form">

        {/* First + Last name side by side */}
        <div className="auth-field-grid">
          <Field
            label="First name"
            id="profile-first"
            placeholder="Alex"
            value={form.first_name}
            onChange={set('first_name')}
            error={errors.first_name?.[0]}
            autoFocus
          />
          <Field
            label="Last name"
            id="profile-last"
            placeholder="Smith"
            value={form.last_name}
            onChange={set('last_name')}
            error={errors.last_name?.[0]}
          />
        </div>

        {/* Username */}
        <Field
          label="Username"
          id="profile-username"
          placeholder="alex_smith"
          value={form.username}
          onChange={set('username')}
          error={errors.username?.[0]}
        />

        {/* Password */}
        <Field
          label="Password"
          id="profile-password"
          type="password"
          placeholder="••••••••"
          value={form.password}
          onChange={set('password')}
          error={errors.password?.[0]}
        />

        {/* Password strength checklist — shown as soon as user starts typing */}
        {form.password && (
          <PasswordRequirements
            password={form.password}
            confirmPassword={form.password_confirm}
          />
        )}

        {/* Confirm password */}
        <Field
          label="Confirm password"
          id="profile-password-confirm"
          type="password"
          placeholder="••••••••"
          value={form.password_confirm}
          onChange={set('password_confirm')}
          error={errors.password_confirm?.[0]}
        />

        {/* General / non-field error */}
        {(errors.non_field_errors || errors._general) && (
          <p className="auth-error">
            {errors._general || errors.non_field_errors?.[0]}
          </p>
        )}

        <button
          type="submit"
          disabled={!canSubmit}
          className="auth-btn-primary"
        >
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </form>
    </AuthLayout>
  )
}