import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { completeProfile } from '../../api/auth'
import { useAuth } from '../../hooks/useAuth'

const Field = ({ label, field, type = 'text', placeholder, value, onChange, error }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
    />
    {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
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
      setErrors(err.response?.data?.errors ?? {})
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-gray-200 p-8">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Complete your profile</h1>
        <p className="text-sm text-gray-500 mb-6">Just a few more details to get started.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Field label="First name" field="first_name" placeholder="Alex"
              value={form.first_name} onChange={set('first_name')} error={errors.first_name?.[0]} />
            <Field label="Last name" field="last_name" placeholder="Smith"
              value={form.last_name} onChange={set('last_name')} error={errors.last_name?.[0]} />
          </div>
          <Field label="Username" field="username" placeholder="alex_smith"
            value={form.username} onChange={set('username')} error={errors.username?.[0]} />
          <Field label="Password" field="password" type="password" placeholder="••••••••"
            value={form.password} onChange={set('password')} error={errors.password?.[0]} />
          <Field label="Confirm password" field="password_confirm" type="password" placeholder="••••••••"
            value={form.password_confirm} onChange={set('password_confirm')} error={errors.password_confirm?.[0]} />

          {errors.non_field_errors && (
            <p className="text-sm text-red-600">{errors.non_field_errors[0]}</p>
          )}

          <button type="submit" disabled={loading}
            className="w-full bg-gray-900 text-white text-sm font-medium py-2.5 rounded-lg hover:bg-gray-700 transition disabled:opacity-50 mt-2">
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>
      </div>
    </div>
  )
}