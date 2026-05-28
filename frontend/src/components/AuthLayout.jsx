import './AuthLayout.css'

export default function AuthLayout({
  brandHeading = 'Welcome to CartIZ',
  brandSubtext = 'Your smart shopping companion — discover, compare, and save.',
  children,
}) {
  return (
    <div className="auth-layout">
      {/* ── Mobile top bar (visible < 768px) ─────────────────── */}
      <div className="auth-mobile-bar">
        <div className="auth-brand-logo-icon">C</div>
        <span className="auth-brand-logo-text">CartIZ</span>
      </div>

      {/* ── Branding panel (left) ────────────────────────────── */}
      <div className="auth-brand-panel">
        <div className="auth-brand-dots" />
        <div className="auth-brand-shape auth-brand-shape--1" />
        <div className="auth-brand-shape auth-brand-shape--2" />
        <div className="auth-brand-shape auth-brand-shape--3" />

        <div className="auth-brand-content">
          <div className="auth-brand-logo">
            <div className="auth-brand-logo-icon">C</div>
            <span className="auth-brand-logo-text">CartIZ</span>
          </div>

          <h2 className="auth-brand-heading">{brandHeading}</h2>
          <p className="auth-brand-subtext">{brandSubtext}</p>
          <div className="auth-brand-accent-bar" />
        </div>
      </div>

      {/* ── Form panel (right) ───────────────────────────────── */}
      <div className="auth-form-panel">
        <div className="auth-form-container">
          {children}
        </div>
      </div>
    </div>
  )
}
