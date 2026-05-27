import { useEffect, useState, useRef } from 'react'
import { getSellerProfile, updateSeller } from '../../api/account'
import DashboardLayout from '../../components/DashboardLayout'

const Field = ({ label, value, onChange, error, placeholder, textarea }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
    {textarea
      ? <textarea value={value} onChange={onChange} placeholder={placeholder} rows={3}
          className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-none" />
      : <input value={value} onChange={onChange} placeholder={placeholder}
          className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent" />
    }
    {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
  </div>
)

export default function SellerPage() {
  const [market, setMarket]   = useState(null)
  const [form, setForm]       = useState({})
  const [errors, setErrors]   = useState({})
  const [saving, setSaving]   = useState(false)
  const [saved, setSaved]     = useState(false)
  const [logoLoading, setLogoLoading]     = useState(false)
  const [bannerLoading, setBannerLoading] = useState(false)
  const logoRef   = useRef()
  const bannerRef = useRef()

  useEffect(() => {
    getSellerProfile().then(r => {
      const m = r.data.data
      setMarket(m)
      setForm({
        market_name:      m.market_name      ?? '',
        description:      m.description      ?? '',
        business_email:   m.business_email   ?? '',
        business_phone:   m.business_phone   ?? '',
        business_address: m.business_address ?? '',
      })
    }).catch(() => {})
  }, [])

  const set = (f) => (e) => setForm(v => ({ ...v, [f]: e.target.value }))

  const handleSave = async (e) => {
    e.preventDefault()
    setErrors({})
    setSaving(true)
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => fd.append(k, v))
      const res = await updateSeller(fd)
      setMarket(res.data.data)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      setErrors(err.response?.data?.errors ?? {})
    } finally { setSaving(false) }
  }

  const handleImageUpload = async (file, field, setLoading) => {
    if (!file) return
    setLoading(true)
    const fd = new FormData()
    fd.append(field, file)
    try {
      const res = await updateSeller(fd)
      setMarket(res.data.data)
    } catch {}
    finally { setLoading(false) }
  }

  if (!market) return (
    <DashboardLayout>
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-400 text-sm">Loading market…</p>
      </div>
    </DashboardLayout>
  )

  return (
    <DashboardLayout>
      <div className="max-w-lg">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{market.market_name}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium
                ${market.is_active ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                {market.is_active ? 'Active' : 'Under review'}
              </span>
              {market.is_verified && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">
                  Verified
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Banner */}
        <div className="mb-6">
          <div className="relative h-28 bg-gray-100 rounded-xl overflow-hidden mb-3">
            {market.banner_url
              ? <img src={market.banner_url} alt="banner" className="w-full h-full object-cover" />
              : <div className="w-full h-full flex items-center justify-center">
                  <span className="text-gray-400 text-sm">No banner</span>
                </div>
            }
          </div>
          <div className="flex gap-3 items-center">
            {/* Logo */}
            <div className="w-14 h-14 rounded-xl bg-gray-100 overflow-hidden flex items-center justify-center flex-shrink-0">
              {market.logo_url
                ? <img src={market.logo_url} alt="logo" className="w-full h-full object-cover" />
                : <span className="text-gray-400 text-xs">Logo</span>
              }
            </div>
            <div className="flex gap-2">
              <button onClick={() => logoRef.current.click()} disabled={logoLoading}
                className="text-xs border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition disabled:opacity-50">
                {logoLoading ? 'Uploading…' : 'Change logo'}
              </button>
              <button onClick={() => bannerRef.current.click()} disabled={bannerLoading}
                className="text-xs border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition disabled:opacity-50">
                {bannerLoading ? 'Uploading…' : 'Change banner'}
              </button>
            </div>
          </div>
          <input ref={logoRef}   type="file" accept="image/*" className="hidden"
            onChange={e => handleImageUpload(e.target.files[0], 'logo', setLogoLoading)} />
          <input ref={bannerRef} type="file" accept="image/*" className="hidden"
            onChange={e => handleImageUpload(e.target.files[0], 'banner_image', setBannerLoading)} />
        </div>

        {/* Form */}
        <form onSubmit={handleSave} className="space-y-4">
          <Field label="Market name" value={form.market_name} onChange={set('market_name')}
            error={errors.market_name?.[0]} placeholder="My Awesome Store" />
          <Field label="Description" value={form.description} onChange={set('description')}
            error={errors.description?.[0]} placeholder="Tell buyers about your market…" textarea />
          <div className="grid grid-cols-2 gap-4">
            <Field label="Business email" value={form.business_email} onChange={set('business_email')}
              error={errors.business_email?.[0]} placeholder="shop@example.com" />
            <Field label="Business phone" value={form.business_phone} onChange={set('business_phone')}
              error={errors.business_phone?.[0]} placeholder="+1 555 000 0000" />
          </div>
          <Field label="Business address" value={form.business_address} onChange={set('business_address')}
            error={errors.business_address?.[0]} placeholder="123 Main St, City" />

          {errors.non_field_errors && (
            <p className="text-sm text-red-600">{errors.non_field_errors[0]}</p>
          )}

          <div className="flex items-center gap-3 pt-2">
            <button type="submit" disabled={saving}
              className="bg-gray-900 text-white text-sm font-medium px-5 py-2 rounded-lg hover:bg-gray-700 transition disabled:opacity-50">
              {saving ? 'Saving…' : 'Save changes'}
            </button>
            {saved && <p className="text-sm text-green-600">Saved successfully.</p>}
          </div>
        </form>
      </div>
    </DashboardLayout>
  )
}