export default function AuthButton({ children, loading, loadingText, type = 'submit', onClick, variant = 'primary' }) {
  const isPrimary = variant === 'primary'
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={loading}
      style={{
        backgroundColor: isPrimary ? '#e0ff4f' : 'white',
        color: '#00272b',
        borderColor: isPrimary ? '#e0ff4f' : '#e5e7eb',
      }}
      className={`w-full py-3.5 rounded-xl text-sm font-bold border-2 transition-all duration-200
        hover:opacity-80 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed`}
    >
      {loading ? (loadingText ?? 'Loading…') : children}
    </button>
  )
}