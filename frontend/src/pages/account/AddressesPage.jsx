import { useEffect, useState } from 'react'
import { getAddresses, createAddress, updateAddress, deleteAddress, setDefaultAddress } from '../../api/account'
import DashboardLayout from '../../components/DashboardLayout'

const EMPTY = {
  address_type: 'shipping', full_name: '', phone_number: '',
  address_line_1: '', address_line_2: '', city: '',
  state_province: '', postal_code: '', country: '', is_default: false,
}

function AddressForm({ initial = EMPTY, onSave, onCancel, loading }) {
  const [form, setForm] = useState(initial)
  const set = (f) => (e) => setForm(v => ({ ...v, [f]: e.target.value }))

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-5 space-y-3">
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: 'Full name',    field: 'full_name'    },
          { label: 'Phone',        field: 'phone_number' },
          { label: 'Address line 1', field: 'address_line_1' },
          { label: 'Address line 2', field: 'address_line_2' },
          { label: 'City',         field: 'city'         },
          { label: 'State',        field: 'state_province'},
          { label: 'Postal code',  field: 'postal_code'  },
          { label: 'Country',      field: 'country'      },
        ].map(({ label, field }) => (
          <div key={field}>
            <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
            <input value={form[field]} onChange={set(field)}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent" />
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <input type="checkbox" id="is_default" checked={form.is_default}
          onChange={e => setForm(v => ({ ...v, is_default: e.target.checked }))}
          className="rounded" />
        <label htmlFor="is_default" className="text-sm text-gray-600">Set as default address</label>
      </div>
      <div className="flex gap-2 pt-1">
        <button onClick={() => onSave(form)} disabled={loading}
          className="bg-gray-900 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-gray-700 transition disabled:opacity-50">
          {loading ? 'Saving…' : 'Save address'}
        </button>
        <button onClick={onCancel}
          className="text-sm text-gray-500 px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-100 transition">
          Cancel
        </button>
      </div>
    </div>
  )
}

export default function AddressesPage() {
  const [addresses, setAddresses] = useState([])
  const [showForm, setShowForm]   = useState(false)
  const [editing, setEditing]     = useState(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState('')

  const load = () => getAddresses().then(r => setAddresses(r.data.data.addresses)).catch(() => {})
  useEffect(() => { load() }, [])

  const handleCreate = async (form) => {
    setLoading(true)
    setError('')
    try {
      await createAddress(form)
      await load()
      setShowForm(false)
    } catch (err) {
      setError('Could not save address.')
    } finally { setLoading(false) }
  }

  const handleUpdate = async (form) => {
    setLoading(true)
    setError('')
    try {
      await updateAddress(editing.id, form)
      await load()
      setEditing(null)
    } catch { setError('Could not update address.') }
    finally { setLoading(false) }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this address?')) return
    try {
      await deleteAddress(id)
      await load()
    } catch { setError('Could not delete address.') }
  }

  const handleSetDefault = async (id) => {
    try {
      await setDefaultAddress(id)
      await load()
    } catch { setError('Could not set default.') }
  }

  return (
    <DashboardLayout>
      <div className="max-w-2xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Addresses</h2>
          {!showForm && !editing && (
            <button onClick={() => setShowForm(true)}
              className="text-sm font-medium bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition">
              Add address
            </button>
          )}
        </div>

        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        {showForm && (
          <div className="mb-4">
            <AddressForm onSave={handleCreate} onCancel={() => setShowForm(false)} loading={loading} />
          </div>
        )}

        <div className="space-y-3">
          {addresses.length === 0 && !showForm && (
            <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
              <p className="text-gray-400 text-sm">No addresses yet.</p>
            </div>
          )}

          {addresses.map(addr => (
            <div key={addr.id}>
              {editing?.id === addr.id ? (
                <AddressForm initial={addr} onSave={handleUpdate} onCancel={() => setEditing(null)} loading={loading} />
              ) : (
                <div className="bg-white border border-gray-200 rounded-xl p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm font-medium text-gray-900">{addr.full_name}</p>
                        {addr.is_default && (
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">Default</span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500">{addr.address_line_1}, {addr.city}</p>
                      <p className="text-sm text-gray-500">{addr.country} {addr.postal_code}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {!addr.is_default && (
                        <button onClick={() => handleSetDefault(addr.id)}
                          className="text-xs text-gray-500 hover:text-gray-900 border border-gray-200 px-2 py-1 rounded-lg transition">
                          Set default
                        </button>
                      )}
                      <button onClick={() => setEditing(addr)}
                        className="text-xs text-gray-500 hover:text-gray-900 border border-gray-200 px-2 py-1 rounded-lg transition">
                        Edit
                      </button>
                      <button onClick={() => handleDelete(addr.id)}
                        className="text-xs text-red-400 hover:text-red-600 border border-gray-200 px-2 py-1 rounded-lg transition">
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  )
}