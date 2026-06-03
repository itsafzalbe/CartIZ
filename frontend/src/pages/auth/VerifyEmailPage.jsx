import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { verifyEmail, resendOTP } from '../../api/auth'
import AuthLayout from '../../components/auth/AuthLayout'
import { extractError } from '../../utils/errors'

export default function VerifyEmailPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const email    = location.state?.email

  const [code, setCode]           = useState(['', '', '', '', ''])
  const [error, setError]         = useState('')
  const [loading, setLoading]     = useState(false)
  const [cooldown, setCooldown]   = useState(60)
  const [resending, setResending] = useState(false)

  const inputs = useRef([])

  // ── Guard: must arrive with email in state ────────────────────────────────
  useEffect(() => {
    if (!email) navigate('/register', { replace: true })
  }, [email, navigate])

  // ── Resend countdown ──────────────────────────────────────────────────────
  useEffect(() => {
    if (cooldown <= 0) return
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000)
    return () => clearTimeout(t)
  }, [cooldown])

  // ── OTP input handlers ────────────────────────────────────────────────────
  const handleChange = (i, val) => {
    if (!/^\d?$/.test(val)) return          // digits only
    const next = [...code]
    next[i] = val
    setCode(next)
    if (val && i < 4) inputs.current[i + 1]?.focus()
  }

  const handleKeyDown = (i, e) => {
    if (e.key === 'Backspace' && !code[i] && i > 0) {
      inputs.current[i - 1]?.focus()
    }
  }

  const handlePaste = (e) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 5)
    if (!pasted.length) return
    const next = [...'     '].map((_, i) => pasted[i] ?? '')
    setCode(next)
    const focusIdx = Math.min(pasted.length, 4)
    inputs.current[focusIdx]?.focus()
  }

  // ── Verify ────────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault()
    const fullCode = code.join('')
    if (fullCode.length < 5) return
    setError('')
    setLoading(true)
    try {
      const res = await verifyEmail(email, fullCode)
      navigate('/complete-profile', {
        replace: true,
        state: {
          user_id: res.data.data.user_id,
          email,
        },
      })
    } catch (err) {
      // Safe to show real backend error — user already owns this email
      setError(extractError(err, 'Verification failed. Please try again.'))
      setCode(['', '', '', '', ''])
      inputs.current[0]?.focus()
    } finally {
      setLoading(false)
    }
  }

  // ── Resend ────────────────────────────────────────────────────────────────
  const handleResend = async () => {
    if (cooldown > 0 || resending) return
    setResending(true)
    setError('')
    try {
      await resendOTP(email)
      setCooldown(60)
      setCode(['', '', '', '', ''])
      inputs.current[0]?.focus()
    } catch (err) {
      setError(extractError(err, 'Could not resend code. Please try again.'))
    } finally {
      setResending(false)
    }
  }

  const codeComplete = code.join('').length === 5

  return (
    <AuthLayout
      brandHeading="Almost there"
      brandSubtext="We just need to verify your email to keep your account secure."
    >
      <h1 className="auth-form-title">Check your email</h1>
      <p className="auth-form-subtitle">
        We sent a 5-digit code to <strong>{email}</strong>
      </p>

      <form onSubmit={handleSubmit} className="auth-form">

        {/* OTP boxes */}
        <div className="auth-otp-group" onPaste={handlePaste}>
          {code.map((digit, i) => (
            <input
              key={i}
              ref={(el) => (inputs.current[i] = el)}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              className="auth-otp-input"
              aria-label={`Digit ${i + 1}`}
              autoFocus={i === 0}
            />
          ))}
        </div>

        {error && <p className="auth-error">{error}</p>}

        <button
          type="submit"
          disabled={loading || !codeComplete}
          className="auth-btn-primary"
        >
          {loading ? 'Verifying…' : 'Verify email'}
        </button>
      </form>

      {/* Resend */}
      <div className="auth-action-center" style={{ marginTop: '20px' }}>
        {cooldown > 0 ? (
          <p>Resend code in {cooldown}s</p>
        ) : (
          <button
            onClick={handleResend}
            disabled={resending}
            className="auth-btn-text"
          >
            {resending ? 'Resending…' : 'Resend code'}
          </button>
        )}
      </div>

      <p className="auth-footer">
        Wrong email?{' '}
        <Link to="/register">Go back</Link>
      </p>
    </AuthLayout>
  )
}