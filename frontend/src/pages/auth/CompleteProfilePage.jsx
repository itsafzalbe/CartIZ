import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { completeProfile } from '../../api/auth'
import { useAuth } from '../../hooks/useAuth'
import AuthLayout from '../../components/AuthLayout'
import PasswordRequirements, { getPasswordRequirements } from '../../components/PasswordRequirements'
import { extractError, extractFieldErrors } from '../../utils/errors'

const Field = ({ label, id, type = 'text', placeholder, value, onChange, error }) => (
  <div className="auth-field">
    <label className="auth-label" htmlFor={id}>{label}</label>
    <input
      id={id}
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className="auth-input"
    />
    {error && <p className="auth-field-error">{error}</p>}
  </div>
)

export default function CompleteProfilePage() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const { login } = useAuth()
  const { user_id, email } = location.state ?? {}

  const [form, setForm] = useState({
    first_name: '', last_name: '', username: '',
    password: '', password_confirm: '',
  })
  const [errors, setErrors]   = useState({})
  const [loading, setLoading] = useState(false)
  const { allMet: passwordReady } = getPasswordRequirements({
    password: form.password,
    confirmPassword: form.password_confirm,
  })

  if (!user_id) {
    navigate('/register', { replace: true })
    return null
  }

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrors({})
    setLoading(true)
    try {
      const res = await completeProfile(user_id, form)
      const { access, refresh } = res.data.data
      login({ access, refresh }, { email })
      navigate('/dashboard', { replace: true })
    } catch (err) {
      // Safe: user has already verified their email, show real field errors
      const fieldErrs = extractFieldErrors(err)
      const general   = extractError(err, null)
      setErrors({
        ...fieldErrs,
        // store general (non-field) error under a special key so JSX can render it
        ...(Object.keys(fieldErrs).length === 0 && general ? { _general: general } : {}),
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      brandHeading="Set up your profile"
      brandSubtext="Just a few more details and you're all set to start shopping."
    >
      <h1 className="auth-form-title">Complete your profile</h1>
      <p className="auth-form-subtitle">Just a few more details to get started.</p>

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="auth-field-grid">
          <Field label="First name" id="profile-first" placeholder="Alex"
            value={form.first_name} onChange={set('first_name')} error={errors.first_name?.[0]} />
          <Field label="Last name" id="profile-last" placeholder="Smith"
            value={form.last_name} onChange={set('last_name')} error={errors.last_name?.[0]} />
        </div>

        <Field label="Username" id="profile-username" placeholder="alex_smith"
          value={form.username} onChange={set('username')} error={errors.username?.[0]} />

        <Field label="Password" id="profile-password" type="password" placeholder="••••••••"
          value={form.password} onChange={set('password')} error={errors.password?.[0]} />

        <PasswordRequirements
          password={form.password}
          confirmPassword={form.password_confirm}
        />

        <Field label="Confirm password" id="profile-password-confirm" type="password" placeholder="••••••••"
          value={form.password_confirm} onChange={set('password_confirm')} error={errors.password_confirm?.[0]} />

        {(errors.non_field_errors || errors._general) && (
          <p className="auth-error">
            {errors._general || errors.non_field_errors?.[0] || errors.non_field_errors}
          </p>
        )}

        <button type="submit" disabled={loading || !passwordReady} className="auth-btn-primary">
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </form>
    </AuthLayout>
  )
}