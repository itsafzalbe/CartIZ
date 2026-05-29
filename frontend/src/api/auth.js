import client from './client'

export const registerEmail        = (email) =>
  client.post('/accounts/register/', { email })

export const checkEmailExists     = (email) =>
  client.get('/accounts/email-exists/', { params: { email } })

export const verifyEmail          = (email, code) =>
  client.post('/accounts/verify-email/', { email, code })

export const resendOTP            = (email) =>
  client.post('/accounts/resend-otp/', { email })

export const completeProfile      = (userId, data) =>
  client.patch(`/accounts/complete-profile/${userId}/`, data)

export const login                = (email, password) =>
  client.post('/accounts/login/', { email, password })

export const logout               = (refresh) =>
  client.post('/accounts/logout/', { refresh })

export const tokenRefresh         = (refresh) =>
  client.post('/accounts/token/refresh/', { refresh })

export const passwordResetRequest = (email) =>
  client.post('/accounts/password/reset/', { email })

export const passwordResetConfirm = (uid, token, new_password, new_password_confirm) =>
  client.post('/accounts/password/reset/confirm/', { uid, token, new_password, new_password_confirm })

export const changePassword       = (data) =>
  client.post('/accounts/password/change/', data)

export const deleteAccount        = (data) =>
  client.delete('/accounts/me/delete/', { data })

export const googleCallback = (code, redirect_uri) =>
  client.post('/accounts/google/callback/', { code, redirect_uri })