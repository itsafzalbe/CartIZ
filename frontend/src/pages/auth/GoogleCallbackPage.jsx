import { useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import client from '../../api/client'

export default function GoogleCallbackPage() {
  const navigate      = useNavigate()
  const [searchParams] = useSearchParams()
  const { login }     = useAuth()
  const called        = useRef(false)

  useEffect(() => {
    if (called.current) return   // strict mode guard
    called.current = true

    const code = searchParams.get('code')
    if (!code) {
      navigate('/login', { replace: true })
      return
    }

    client.post('/accounts/google/callback/', {
      code,
      redirect_uri: 'http://localhost:80/auth/callback',
    })
      .then((res) => {
        const { access, refresh, ...user } = res.data.data
        login({ access, refresh }, user)
        navigate('/dashboard', { replace: true })
      })
      .catch(() => {
        navigate('/login?error=google_failed', { replace: true })
      })
  }, [])

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#fffcdc',
      fontFamily: 'Inter, sans-serif',
      color: '#00272b',
      fontSize: 15,
    }}>
      Signing you in with Google…
    </div>
  )
}