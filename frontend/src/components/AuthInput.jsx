export default function AuthInput({
  label, type = 'text', value, onChange,
  placeholder, error, required = true, right
}) {
  return (
    <div>
      {(label || right) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && (
            <label className="text-sm font-semibold" style={{ color: '#00272b' }}>
              {label}
            </label>
          )}
          {right}
        </div>
      )}
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        style={{
          backgroundColor: 'white',
          borderColor: error ? '#ef4444' : '#e5e7eb',
          color: '#00272b',
          outline: 'none',
        }}
        className="w-full px-4 py-3.5 rounded-xl border-2 text-sm transition-all duration-200 placeholder-gray-300"
        onFocus={e => {
          e.target.style.borderColor = '#e0ff4f'
          e.target.style.boxShadow = '0 0 0 4px rgba(224,255,79,0.15)'
        }}
        onBlur={e => {
          e.target.style.borderColor = error ? '#ef4444' : '#e5e7eb'
          e.target.style.boxShadow = 'none'
        }}
      />
      {error && (
        <p className="text-xs mt-1.5 font-medium" style={{ color: '#ef4444' }}>{error}</p>
      )}
    </div>
  )
}