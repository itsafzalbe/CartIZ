import './PasswordRequirements.css'

const hasLowercase = (value) => /[a-z]/.test(value)
const hasUppercase = (value) => /[A-Z]/.test(value)
const hasNumber = (value) => /\d/.test(value)

export const getPasswordRequirements = ({
  password = '',
  confirmPassword = '',
  showMatch = true,
} = {}) => {
  const hasInput = password.length > 0
  const hasConfirm = typeof confirmPassword === 'string' && confirmPassword.length > 0

  const requirements = [
    {
      key: 'lowercase',
      label: 'At least one lowercase letter',
      met: hasLowercase(password),
      active: hasInput,
    },
    {
      key: 'length',
      label: 'Minimum 8 characters',
      met: password.length >= 8,
      active: hasInput,
    },
    {
      key: 'uppercase',
      label: 'At least one uppercase letter',
      met: hasUppercase(password),
      active: hasInput,
    },
    {
      key: 'number',
      label: 'At least one number',
      met: hasNumber(password),
      active: hasInput,
    },
  ]

  if (showMatch) {
    requirements.push({
      key: 'match',
      label: 'Passwords match',
      met: hasConfirm && password === confirmPassword,
      active: hasConfirm,
    })
  }

  const allMet = requirements.every((req) => req.met)

  return { requirements, allMet }
}

export default function PasswordRequirements({
  password = '',
  confirmPassword = '',
  showMatch = true,
}) {
  const { requirements } = getPasswordRequirements({
    password,
    confirmPassword,
    showMatch,
  })

  return (
    <div className="pw-reqs" aria-live="polite">
      <ul className="pw-reqs-list">
        {requirements.map(({ key, label, met, active }) => {
          const status = active ? (met ? 'met' : 'unmet') : 'idle'
          const icon = met && active ? '✓' : '✕'
          return (
            <li key={key} className={`pw-reqs-item pw-reqs-item--${status}`}>
              <span className="pw-reqs-icon" aria-hidden="true">{icon}</span>
              <span>{label}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}