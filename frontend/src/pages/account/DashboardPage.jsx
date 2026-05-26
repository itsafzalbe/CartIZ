import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { getStats, getActivity } from '../../api/account'
import DashboardLayout from '../../components/DashboardLayout'

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats]       = useState(null)
  const [activity, setActivity] = useState([])

  useEffect(() => {
    getStats().then(r => setStats(r.data.data)).catch(() => {})
    getActivity().then(r => setActivity(r.data.data?.activites ?? [])).catch(() => {})
  }, [])

  return (
    <DashboardLayout>
      <div className="max-w-2xl">
        <h2 className="text-xl font-semibold text-gray-900 mb-1">
          Welcome back, {user?.first_name} 👋
        </h2>
        <p className="text-sm text-gray-500 mb-8">Here's a summary of your account.</p>

        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: 'Orders',    value: stats?.total_orders    ?? '—' },
            { label: 'Addresses', value: stats?.total_addresses ?? '—' },
            { label: 'Days active', value: stats?.member_for_days ?? '—' },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white border border-gray-200 rounded-xl p-4">
              <p className="text-xs text-gray-400 mb-1">{label}</p>
              <p className="text-2xl font-semibold text-gray-900">{value}</p>
            </div>
          ))}
        </div>

        {/* Quick links */}
        <div className="grid grid-cols-2 gap-3 mb-8">
          {[
            { to: '/dashboard/profile',   label: 'Edit profile',    desc: 'Update your name, username, avatar' },
            { to: '/dashboard/addresses', label: 'Manage addresses', desc: 'Add or edit shipping addresses'     },
            { to: '/dashboard/security',  label: 'Security',        desc: 'Change password or delete account'  },
          ].map(({ to, label, desc }) => (
            <Link key={to} to={to}
              className="bg-white border border-gray-200 rounded-xl p-4 hover:border-gray-400 transition">
              <p className="text-sm font-medium text-gray-900 mb-0.5">{label}</p>
              <p className="text-xs text-gray-400">{desc}</p>
            </Link>
          ))}
        </div>

        {/* Activity feed */}
        {activity.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Recent activity</h3>
            <div className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100">
              {activity.map((item, i) => (
                <div key={i} className="px-4 py-3">
                  <p className="text-sm text-gray-700">{item.description}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(item.timestamp).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}