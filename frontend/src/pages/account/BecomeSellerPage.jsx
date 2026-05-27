import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { becomeSeller } from '../../api/account'
import { useAuth } from '../../hooks/useAuth'
import DashboardLayout from '../../components/DashboardLayout'

const Field = ({ label, field, value, onChange, error, placeholder, type = 'text', textarea }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
    {textarea
      ? <textarea value={value} onChange={onChange} placeholder={placeholder} rows={3}
          className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-none" />
      : <input type={type} value={value} onChange={onChange} placeholder={placeholder}
          className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent" />
    }
    {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
  </div>
)

export default function BecomeSellerPage() {
  const navigate = useNavigate()
  const { setUser } = useAuth()

  const [form, setForm] = useState({
    market_name: '', description: '',
    business_email: '', business_phone: '',
    business_address: '', tax_id: '',
  })
  const [errors, setErrors]   = useState({})
  const [loading, setLoading] = useState(false)

  const set = (f) => (e) => setForm(v => ({ ...v, [f]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrors({})
    setLoading(true)
    try {
      await becomeSeller(form)
      setUser(u => ({ ...u, is_seller: true }))
      navigate('/dashboard/seller', { replace: true })
    } catch (err) {
      setErrors(err.response?.data?.errors ?? {})
    } finally { setLoading(false) }
  }

  return (
    <DashboardLayout>
      <div className="max-w-lg">
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-1">Become a seller</h2>
          <p className="text-sm text-gray-500">
            Set up your market on Cartiz. Your market will be reviewed before going live.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="Market name" field="market_name" placeholder="My Awesome Store"
            value={form.market_name} onChange={set('market_name')} error={errors.market_name?.[0]} />

          <Field label="Description" field="description" placeholder="Tell buyers about your market…"
            value={form.description} onChange={set('description')} error={errors.description?.[0]} textarea />

          <div className="grid grid-cols-2 gap-4">
            <Field label="Business email" field="business_email" type="email" placeholder="shop@example.com"
              value={form.business_email} onChange={set('business_email')} error={errors.business_email?.[0]} />
            <Field label="Business phone" field="business_phone" placeholder="+1 555 000 0000"
              value={form.business_phone} onChange={set('business_phone')} error={errors.business_phone?.[0]} />
          </div>

          <Field label="Business address" field="business_address" placeholder="123 Main St, City"
            value={form.business_address} onChange={set('business_address')} error={errors.business_address?.[0]} />

          <Field label="Tax ID (optional)" field="tax_id" placeholder="XX-XXXXXXX"
            value={form.tax_id} onChange={set('tax_id')} error={errors.tax_id?.[0]} />

          {errors.non_field_errors && (
            <p className="text-sm text-red-600">{errors.non_field_errors[0]}</p>
          )}

          <div className="pt-2">
            <button type="submit" disabled={loading}
              className="w-full bg-gray-900 text-white text-sm font-medium py-2.5 rounded-lg hover:bg-gray-700 transition disabled:opacity-50">
              {loading ? 'Submitting…' : 'Submit application'}
            </button>
            <p className="text-xs text-gray-400 text-center mt-2">
              Your market starts inactive until reviewed by our team.
            </p>
          </div>
        </form>
      </div>
    </DashboardLayout>
  )
}