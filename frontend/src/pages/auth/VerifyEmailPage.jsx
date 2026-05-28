import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { verifyEmail, resendOTP } from '../../api/auth'
import AuthLayout from '../../components/AuthLayout'
import { extractError } from '../../utils/errors'
import { useAuth } from '../../hooks/useAuth'

export default function VerifyEmailPage() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const { login } = useAuth()
  const email     = location.state?.email

  const [code, setCode]         = useState(['', '', '', '', ''])
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [cooldown, setCooldown] = useState(60)
  const [resending, setResending] = useState(false)
  const inputs = useRef([])

  // redirect if landed here without email
  useEffect(() => {
    if (!email) navigate('/register', { replace: true })
  }, [email, navigate])

  // countdown timer
  useEffect(() => {
    if (cooldown <= 0) return
    const t = setTimeout(() => setCooldown(c => c - 1), 1000)
    return () => clearTimeout(t)
  }, [cooldown])

  const handleChange = (i, val) => {
    if (!/^\d?$/.test(val)) return
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
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 5)
    if (pasted.length === 5) {
      setCode(pasted.split(''))
      inputs.current[4]?.focus()
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const fullCode = code.join('')
    if (fullCode.length < 5) return
    setError('')
    setLoading(true)
    try {
      const res = await verifyEmail(email, fullCode)
      const { access, refresh, user } = res.data.data
      login({ access, refresh }, user)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      // Safe: user already owns the email — show real backend messages
      setError(extractError(err, 'Verification failed. Please try again.'))
      setCode(['', '', '', '', ''])
      inputs.current[0]?.focus()
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (cooldown > 0) return
    setResending(true)
    setError('')
    try {
      await resendOTP(email)
      setCooldown(60)
    } catch (err) {
      setError(extractError(err, 'Could not resend code. Please try again.'))
    } finally {
      setResending(false)
    }
  }

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
        <div className="auth-otp-group" onPaste={handlePaste}>
          {code.map((digit, i) => (
            <input
              key={i}
              ref={el => inputs.current[i] = el}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={e => handleChange(i, e.target.value)}
              onKeyDown={e => handleKeyDown(i, e)}
              className="auth-otp-input"
              aria-label={`Digit ${i + 1}`}
            />
          ))}
        </div>

        {error && <p className="auth-error">{error}</p>}

        <button
          type="submit"
          disabled={loading || code.join('').length < 5}
          className="auth-btn-primary"
        >
          {loading ? 'Verifying…' : 'Verify email'}
        </button>
      </form>

      <div className="auth-action-center" style={{ marginTop: '20px' }}>
        {cooldown > 0 ? (
          <p>Resend code in {cooldown}s</p>
        ) : (
          <button onClick={handleResend} disabled={resending} className="auth-btn-text">
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