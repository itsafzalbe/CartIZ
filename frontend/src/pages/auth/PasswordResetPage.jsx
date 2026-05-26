import { useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { passwordResetRequest, passwordResetConfirm } from '../../api/auth'

export default function PasswordResetPage() {
  const [searchParams] = useSearchParams()
  const uid   = searchParams.get('uid')
  const token = searchParams.get('token')
  const isConfirm = !!(uid && token)

  // Request state
  const [email, setEmail]     = useState('')
  const [sent, setSent]       = useState(false)

  // Confirm state
  const [form, setForm]       = useState({ new_password: '', new_password_confirm: '' })
  const [done, setDone]       = useState(false)

  const [errors, setErrors]   = useState({})
  const [loading, setLoading] = useState(false)

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
      setDone(true)
    } catch (err) {
      setErrors(err.response?.data?.errors ?? {})
    } finally {
      setLoading(false)
    }
  }

  // ── Confirm: success ──────────────────────────────────────────────────────
  if (isConfirm && done) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-gray-200 p-8 text-center">
        <div className="text-3xl mb-4">✓</div>
        <h1 className="text-xl font-semibold text-gray-900 mb-2">Password reset</h1>
        <p className="text-sm text-gray-500 mb-6">Your password has been updated. You can now log in.</p>
        <Link to="/login" className="block w-full bg-gray-900 text-white text-sm font-medium py-2.5 rounded-lg hover:bg-gray-700 transition text-center">
          Go to login
        </Link>
      </div>
    </div>
  )

  // ── Confirm: form ─────────────────────────────────────────────────────────
  if (isConfirm) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-gray-200 p-8">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Set new password</h1>
        <p className="text-sm text-gray-500 mb-6">Choose a strong password for your account.</p>
        <form onSubmit={handleConfirm} className="space-y-4">
          {['new_password', 'new_password_confirm'].map((field, i) => (
            <div key={field}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {i === 0 ? 'New password' : 'Confirm password'}
              </label>
              <input
                type="password"
                required
                value={form[field]}
                onChange={e => setForm(f => ({ ...f, [field]: e.target.value }))}
                placeholder="••••••••"
                className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
              />
              {errors[field] && <p className="text-xs text-red-600 mt-1">{errors[field][0]}</p>}
            </div>
          ))}
          {errors.non_field_errors && <p className="text-sm text-red-600">{errors.non_field_errors[0]}</p>}
          <button type="submit" disabled={loading}
            className="w-full bg-gray-900 text-white text-sm font-medium py-2.5 rounded-lg hover:bg-gray-700 transition disabled:opacity-50">
            {loading ? 'Saving…' : 'Reset password'}
          </button>
        </form>
      </div>
    </div>
  )

  // ── Request: sent ─────────────────────────────────────────────────────────
  if (sent) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-gray-200 p-8 text-center">
        <div className="text-3xl mb-4">✉️</div>
        <h1 className="text-xl font-semibold text-gray-900 mb-2">Check your inbox</h1>
        <p className="text-sm text-gray-500 mb-6">
          If <span className="font-medium text-gray-700">{email}</span> is registered, you'll receive a reset link shortly.
        </p>
        <Link to="/login" className="text-sm text-gray-900 font-medium hover:underline">Back to login</Link>
      </div>
    </div>
  )

  // ── Request: form ─────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-gray-200 p-8">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Reset your password</h1>
        <p className="text-sm text-gray-500 mb-6">Enter your email and we'll send you a reset link.</p>
        <form onSubmit={handleRequest} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
            <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent" />
          </div>
          <button type="submit" disabled={loading}
            className="w-full bg-gray-900 text-white text-sm font-medium py-2.5 rounded-lg hover:bg-gray-700 transition disabled:opacity-50">
            {loading ? 'Sending…' : 'Send reset link'}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-gray-500">
          <Link to="/login" className="text-gray-900 font-medium hover:underline">Back to login</Link>
        </p>
      </div>
    </div>
  )
}