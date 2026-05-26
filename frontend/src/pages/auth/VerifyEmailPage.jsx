import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { verifyEmail, resendOTP } from '../../api/auth'

export default function VerifyEmailPage() {
  const navigate  = useNavigate()
  const location  = useLocation()
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
      const { user_id } = res.data.data
      navigate('/complete-profile', { state: { email, user_id } })
    } catch (err) {
      const errors = err.response?.data?.errors
      setError(errors?.code?.[0] || errors?.non_field_errors?.[0] || 'Verification failed.')
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
      const errors = err.response?.data?.errors
      setError(errors?.email?.[0] || 'Could not resend code.')
    } finally {
      setResending(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-gray-200 p-8">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Check your email</h1>
        <p className="text-sm text-gray-500 mb-6">
          We sent a 5-digit code to <span className="font-medium text-gray-700">{email}</span>
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex gap-2 justify-between" onPaste={handlePaste}>
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
                className="w-12 h-12 text-center text-lg font-semibold rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
              />
            ))}
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={loading || code.join('').length < 5}
            className="w-full bg-gray-900 text-white text-sm font-medium py-2.5 rounded-lg hover:bg-gray-700 transition disabled:opacity-50"
          >
            {loading ? 'Verifying…' : 'Verify email'}
          </button>
        </form>

        <div className="mt-4 text-center">
          {cooldown > 0 ? (
            <p className="text-sm text-gray-400">Resend code in {cooldown}s</p>
          ) : (
            <button
              onClick={handleResend}
              disabled={resending}
              className="text-sm text-gray-900 font-medium hover:underline disabled:opacity-50"
            >
              {resending ? 'Resending…' : 'Resend code'}
            </button>
          )}
        </div>

        <p className="mt-4 text-center text-sm text-gray-500">
          Wrong email?{' '}
          <Link to="/register" className="text-gray-900 font-medium hover:underline">Go back</Link>
        </p>
      </div>
    </div>
  )
}