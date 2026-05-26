import client from './client'

export const getProfile      = ()       => client.get('/accounts/me/')
export const getDetailProfile= ()       => client.get('/accounts/me/detail/')
export const updateProfile   = (data)   => client.patch('/accounts/me/update/', data)
export const updateAvatar    = (form)   => client.patch('/accounts/me/avatar/', form, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const deleteAccount   = (data)   => client.delete('/accounts/me/delete/', { data })
export const getStats        = ()       => client.get('/accounts/me/stats/')
export const getActivity     = ()       => client.get('/accounts/me/activity/')

export const getAddresses    = ()       => client.get('/accounts/me/addresses/')
export const createAddress   = (data)   => client.post('/accounts/me/addresses/', data)
export const updateAddress   = (id, data) => client.patch(`/accounts/me/addresses/${id}/`, data)
export const deleteAddress   = (id)     => client.delete(`/accounts/me/addresses/${id}/`)
export const setDefaultAddress = (id)  => client.patch(`/accounts/me/addresses/${id}/set-default/`)

export const becomeSeller    = (data)   => client.post('/accounts/me/become-seller/', data)
export const getSellerProfile= ()       => client.get('/accounts/me/seller/')
export const updateSeller    = (form)   => client.patch('/accounts/me/seller/update/', form, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const getSellerStats  = ()       => client.get('/accounts/me/seller/stats/')
