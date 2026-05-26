import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { logout as logoutApi } from '../api/auth'
import { getRefresh, clearTokens } from '../utils/token'

const links = [
  { to: '/dashboard',           icon: '▤', label: 'Overview'  },
  { to: '/dashboard/profile',   icon: '◉', label: 'Profile'   },
  { to: '/dashboard/addresses', icon: '⌖', label: 'Addresses' },
  { to: '/dashboard/security',  icon: '⚿', label: 'Security'  },
]

export default function DashboardLayout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try { await logoutApi(getRefresh()) } catch {}
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col py-6 px-4 fixed h-full">
        <div className="mb-8 px-2">
          <h1 className="text-lg font-semibold text-gray-900">Cartiz</h1>
          <p className="text-xs text-gray-400 mt-0.5 truncate">{user?.email}</p>
        </div>

        <nav className="flex-1 space-y-1">
          {links.map(({ to, icon, label }) => (
            <NavLink key={to} to={to} end={to === '/dashboard'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition
                ${isActive
                  ? 'bg-gray-900 text-white font-medium'
                  : 'text-gray-600 hover:bg-gray-100'}`
              }>
              <span className="text-base">{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-gray-200 pt-4 mt-4">
          <div className="flex items-center gap-3 px-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium text-gray-600">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-xs text-gray-400 truncate">@{user?.username}</p>
            </div>
          </div>
          <button onClick={handleLogout}
            className="w-full text-left px-3 py-2 text-sm text-red-500 hover:bg-red-50 rounded-lg transition">
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-56 flex-1 p-8">
        {children}
      </main>
    </div>
  )
}