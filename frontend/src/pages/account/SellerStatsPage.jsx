import { useEffect, useState } from 'react'
import { getSellerStats } from '../../api/account'
import DashboardLayout from '../../components/DashboardLayout'

export default function SellerStatsPage() {
  const [stats, setStats]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSellerStats()
      .then(r => setStats(r.data.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <DashboardLayout>
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-400 text-sm">Loading stats…</p>
      </div>
    </DashboardLayout>
  )

  const cards = [
    { label: 'Total sales',     value: stats?.total_sales    ?? '—' },
    { label: 'Rating',          value: stats?.rating_average ?? '—' },
    { label: 'Days as seller',  value: stats?.member_for_days ?? '—' },
  ]

  return (
    <DashboardLayout>
      <div className="max-w-2xl">
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-1">Market stats</h2>
          <p className="text-sm text-gray-500">{stats?.market_name}</p>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-8">
          {cards.map(({ label, value }) => (
            <div key={label} className="bg-white border border-gray-200 rounded-xl p-5">
              <p className="text-xs text-gray-400 mb-1">{label}</p>
              <p className="text-2xl font-semibold text-gray-900">{value}</p>
            </div>
          ))}
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-400 mb-1">Status</p>
              <span className={`text-sm font-medium px-2 py-0.5 rounded-full
                ${stats?.is_active ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                {stats?.is_active ? 'Active' : 'Under review'}
              </span>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1">Verified</p>
              <span className={`text-sm font-medium px-2 py-0.5 rounded-full
                ${stats?.is_verified ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}>
                {stats?.is_verified ? 'Verified' : 'Not verified'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}