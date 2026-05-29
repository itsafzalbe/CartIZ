import { useState } from 'react'
import { Link } from 'react-router-dom'
import AuthLayout from '../../components/AuthLayout'
import AuthInput from '../../components/AuthInput'
import AuthButton from '../../components/AuthButton'
import { passwordResetRequest } from '../../api/auth'

export default function ForgotPasswordPage() {
  const [email, setEmail]     = useState('')
  const [sent, setSent]       = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async e => {
    e.preventDefault()
    setLoading(true)
    try { await passwordResetRequest(email) } catch {}
    finally { setSent(true); setLoading(false) }
  }

  if (sent) return (
    <AuthLayout title="Check inbox" subtitle={"Reset link\nsent"}>
      <div className="text-center">
        <div className="w-20 h-20 rounded-2xl flex items-center justify-center text-4xl mx-auto mb-6"
          style={{ backgroundColor: '#e0ff4f' }}>
          ✉️
        </div>
        <h1 className="text-3xl font-black mb-3" style={{ color: '#00272b' }}>Check your inbox</h1>
        <p className="text-sm mb-2" style={{ color: '#00272b', opacity: 0.45 }}>
          If <span className="font-bold opacity-100" style={{ color: '#00272b' }}>{email}</span> is registered,
          you'll receive a reset link shortly.
        </p>
        <p className="text-xs mb-8" style={{ color: '#00272b', opacity: 0.35 }}>
          Don't forget to check your spam folder.
        </p>
        <Link to="/login"
          className="text-sm font-bold hover:underline"
          style={{ color: '#00272b' }}>
          ← Back to sign in
        </Link>
      </div>
    </AuthLayout>
  )

  return (
    <AuthLayout title="Forgot password" subtitle={"Reset your\npassword"}>
      <div>
        <h1 className="text-3xl font-black mb-1" style={{ color: '#00272b' }}>Forgot password?</h1>
        <p className="text-sm mb-8" style={{ color: '#00272b', opacity: 0.45 }}>
          Enter your email and we'll send you a reset link.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <AuthInput
            label="Email address"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
          <div className="pt-1">
            <AuthButton loading={loading} loadingText="Sending link…">
              Send reset link
            </AuthButton>
          </div>
        </form>

        <p className="mt-6 text-center text-sm" style={{ color: '#00272b', opacity: 0.5 }}>
          <Link to="/login" className="font-bold hover:underline" style={{ color: '#00272b', opacity: 1 }}>
            ← Back to sign in
          </Link>
        </p>
      </div>
    </AuthLayout>
  )
}