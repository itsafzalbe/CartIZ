import { useState, useRef } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { updateProfile, updateAvatar } from '../../api/account'
import DashboardLayout from '../../components/DashboardLayout'

export default function ProfilePage() {
  const { user, setUser } = useAuth()

  const [form, setForm] = useState({
    first_name:  user?.first_name  ?? '',
    last_name:   user?.last_name   ?? '',
    username:    user?.username    ?? '',
    phone_number: user?.phone_number ?? '',
  })
  const [errors, setErrors]     = useState({})
  const [saving, setSaving]     = useState(false)
  const [saved, setSaved]       = useState(false)
  const [avatarLoading, setAvatarLoading] = useState(false)
  const fileRef = useRef()

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }))

  const handleSave = async (e) => {
    e.preventDefault()
    setErrors({})
    setSaving(true)
    try {
      const res = await updateProfile(form)
      setUser(u => ({ ...u, ...res.data.data }))
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      setErrors(err.response?.data?.errors ?? {})
    } finally {
      setSaving(false)
    }
  }

  const handleAvatar = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setAvatarLoading(true)
    const formData = new FormData()
    formData.append('avatar', file)
    try {
      const res = await updateAvatar(formData)
      setUser(u => ({ ...u, avatar_url: res.data.data.avatar_url }))
    } catch {}
    finally { setAvatarLoading(false) }
  }

  return (
    <DashboardLayout>
      <div className="max-w-lg">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Profile</h2>

        {/* Avatar */}
        <div className="flex items-center gap-4 mb-8">
          <div className="w-16 h-16 rounded-full bg-gray-200 overflow-hidden flex items-center justify-center">
            {user?.avatar_url
              ? <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" />
              : <span className="text-xl font-medium text-gray-500">
                  {user?.first_name?.[0]}{user?.last_name?.[0]}
                </span>
            }
          </div>
          <div>
            <button onClick={() => fileRef.current.click()}
              disabled={avatarLoading}
              className="text-sm font-medium text-gray-900 border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition disabled:opacity-50">
              {avatarLoading ? 'Uploading…' : 'Change photo'}
            </button>
            <p className="text-xs text-gray-400 mt-1">JPG or PNG, max 5MB</p>
          </div>
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleAvatar} />
        </div>

        {/* Form */}
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'First name', field: 'first_name' },
              { label: 'Last name',  field: 'last_name'  },
            ].map(({ label, field }) => (
              <div key={field}>
                <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
                <input value={form[field]} onChange={set(field)}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent" />
                {errors[field] && <p className="text-xs text-red-600 mt-1">{errors[field][0]}</p>}
              </div>
            ))}
          </div>

          {[
            { label: 'Username',     field: 'username',     placeholder: 'alex_smith'        },
            { label: 'Phone number', field: 'phone_number', placeholder: '+1 555 000 0000'   },
          ].map(({ label, field, placeholder }) => (
            <div key={field}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
              <input value={form[field]} onChange={set(field)} placeholder={placeholder}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent" />
              {errors[field] && <p className="text-xs text-red-600 mt-1">{errors[field][0]}</p>}
            </div>
          ))}

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