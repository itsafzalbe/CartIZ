import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { changePassword } from '../../api/auth'
import { deleteAccount } from '../../api/account'
import { useAuth } from '../../hooks/useAuth'
import DashboardLayout from '../../components/DashboardLayout'

export default function SecurityPage() {
  const { logout } = useAuth()
  const navigate   = useNavigate()

  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '', new_password_confirm: '' })
  const [pwErrors, setPwErrors]   = useState({})
  const [pwSaving, setPwSaving]   = useState(false)
  const [pwSaved, setPwSaved]     = useState(false)

  const [deletePassword, setDeletePassword] = useState('')
  const [deleteError, setDeleteError]       = useState('')
  const [deleting, setDeleting]             = useState(false)
  const [confirmDelete, setConfirmDelete]   = useState(false)

  const setPw = (f) => (e) => setPwForm(v => ({ ...v, [f]: e.target.value }))

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    setPwErrors({})
    setPwSaving(true)
    try {
      await changePassword(pwForm)
      setPwSaved(true)
      setPwForm({ old_password: '', new_password: '', new_password_confirm: '' })
      setTimeout(() => setPwSaved(false), 3000)
    } catch (err) {
      setPwErrors(err.response?.data?.errors ?? {})
    } finally { setPwSaving(false) }
  }

  const handleDelete = async () => {
    setDeleteError('')
    setDeleting(true)
    try {
      await deleteAccount({ password: deletePassword, hard_delete: false })
      logout()
      navigate('/login', { replace: true })
    } catch (err) {
      const errors = err.response?.data?.errors
      setDeleteError(errors?.password?.[0] || 'Could not delete account.')
    } finally { setDeleting(false) }
  }

  return (
    <DashboardLayout>
      <div className="max-w-lg space-y-8">
        <h2 className="text-xl font-semibold text-gray-900">Security</h2>

        {/* Change password */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Change password</h3>
          <form onSubmit={handlePasswordChange} className="space-y-4">
            {[
              { label: 'Current password', field: 'old_password'         },
              { label: 'New password',     field: 'new_password'         },
              { label: 'Confirm password', field: 'new_password_confirm' },
            ].map(({ label, field }) => (
              <div key={field}>
                <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
                <input type="password" value={pwForm[field]} onChange={setPw(field)}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent" />
                {pwErrors[field] && <p className="text-xs text-red-600 mt-1">{pwErrors[field][0]}</p>}
              </div>
            ))}
            {pwErrors.non_field_errors && <p className="text-sm text-red-600">{pwErrors.non_field_errors[0]}</p>}
            <div className="flex items-center gap-3">
              <button type="submit" disabled={pwSaving}
                className="bg-gray-900 text-white text-sm font-medium px-5 py-2 rounded-lg hover:bg-gray-700 transition disabled:opacity-50">
                {pwSaving ? 'Saving…' : 'Update password'}
              </button>
              {pwSaved && <p className="text-sm text-green-600">Password updated.</p>}
            </div>
          </form>
        </div>

        {/* Delete account */}
        <div className="bg-white border border-red-200 rounded-xl p-6">
          <h3 className="text-sm font-semibold text-red-600 mb-1">Delete account</h3>
          <p className="text-sm text-gray-500 mb-4">
            This will deactivate your account. Enter your password to confirm.
          </p>
          {!confirmDelete ? (
            <button onClick={() => setConfirmDelete(true)}
              className="text-sm text-red-500 border border-red-200 px-4 py-2 rounded-lg hover:bg-red-50 transition">
              Delete my account
            </button>
          ) : (
            <div className="space-y-3">
              <input type="password" placeholder="Enter your password" value={deletePassword}
                onChange={e => setDeletePassword(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-transparent" />
              {deleteError && <p className="text-sm text-red-600">{deleteError}</p>}
              <div className="flex gap-2">
                <button onClick={handleDelete} disabled={deleting || !deletePassword}
                  className="bg-red-500 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-red-600 transition disabled:opacity-50">
                  {deleting ? 'Deleting…' : 'Confirm delete'}
                </button>
                <button onClick={() => { setConfirmDelete(false); setDeletePassword('') }}
                  className="text-sm text-gray-500 px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-100 transition">
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}