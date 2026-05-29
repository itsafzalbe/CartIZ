/**
 * extractError(err, fallback?)
 *
 * Parses a backend API error response and returns the most specific
 * human-readable message.
 *
 * Backend envelope shapes handled:
 *   { errors: { non_failed_errors: "msg" | ["msg"] } }
 *   { errors: { non_field_errors: ["msg"] } }
 *   { errors: { email: ["msg"], username: ["msg"], ... } }
 *   { message: "msg" }   (used on 404 etc.)
 *
 * Security notes:
 *   - Login: backend already returns generic "Invalid credentials" — safe to pass through.
 *   - Register / password reset: use extractErrorSafe() to avoid user-enumeration.
 *   - Verify / complete profile: show real errors — user already proved email ownership.
 *
 * Usage:
 *   import { extractError, extractErrorSafe, extractFieldErrors } from '../../utils/errors'
 */

/**
 * Returns a single user-friendly error string from an axios error.
 *
 * @param {import('axios').AxiosError} err
 * @param {string} [fallback]
 * @returns {string}
 */
export function extractError(err, fallback = 'Something went wrong. Please try again.') {
  const data = err?.response?.data

  if (!data) {
    // Network error or no response
    if (err?.code === 'ERR_NETWORK' || err?.message === 'Network Error') {
      return 'Unable to reach the server. Check your internet connection.'
    }
    return fallback
  }

  const errors = data.errors

  if (errors) {
    // Priority 1: non_failed_errors (login lockout, account state messages)
    const nfe = errors.non_failed_errors
    if (nfe) {
      return Array.isArray(nfe) ? nfe[0] : nfe
    }

    // Priority 2: non_field_errors (cross-field validation errors)
    const nonField = errors.non_field_errors
    if (nonField && Array.isArray(nonField) && nonField.length > 0) {
      return nonField[0]
    }

    // Priority 3: First field-level error, in order
    const FIELD_PRIORITY = [
      'email', 'password', 'username', 'code',
      'new_password', 'new_password_confirm', 'refresh', 'token', 'uid',
    ]

    for (const field of FIELD_PRIORITY) {
      if (errors[field]) {
        const val = errors[field]
        return Array.isArray(val) ? val[0] : val
      }
    }

    // Priority 4: any remaining field key
    for (const key of Object.keys(errors)) {
      const val = errors[key]
      if (val) return Array.isArray(val) ? val[0] : val
    }
  }

  // Priority 5: top-level message (e.g. 404 "User not found")
  if (data.message && typeof data.message === 'string') {
    return data.message
  }

  return fallback
}


/**
 * extractErrorSafe — for flows where revealing whether an email exists is a
 * security risk (registration, password reset request).
 *
 * Rules:
 *   - Rate-limit (429) → show actual message so the user knows to slow down.
 *   - Network error    → show connectivity message.
 *   - Any other error  → return the neutral `safeMessage` regardless of backend text.
 *
 * This prevents user-enumeration: an attacker can't tell if an email is
 * registered by reading the error shown in the UI.
 *
 * @param {import('axios').AxiosError} err
 * @param {string} [safeMessage]
 * @returns {string}
 */
export function extractErrorSafe(
  err,
  safeMessage = "If this email isn't registered, we've sent a verification code.",
) {
  // Network / no response
  if (!err?.response) {
    if (err?.code === 'ERR_NETWORK' || err?.message === 'Network Error') {
      return 'Unable to reach the server. Check your internet connection.'
    }
    return safeMessage
  }

  const status = err.response.status

  // Rate limiting — always safe to reveal; doesn't enumerate users
  if (status === 429) {
    return extractError(err, 'Too many requests. Please wait before trying again.')
  }

  // Everything else: return the neutral message to avoid user enumeration
  return safeMessage
}


/**
 * Returns an object mapping field names to their first error string.
 * Useful for per-field inline validation messages.
 *
 * @param {import('axios').AxiosError} err
 * @returns {Record<string, string>}
 */
export function extractFieldErrors(err) {
  const errors = err?.response?.data?.errors ?? {}
  const result = {}

  for (const [key, val] of Object.entries(errors)) {
    if (key === 'non_failed_errors' || key === 'non_field_errors') continue
    result[key] = Array.isArray(val) ? val[0] : String(val)
  }

  return result
}


/**
 * Combines a top-level error and field-level errors in one call.
 *
 * @param {import('axios').AxiosError} err
 * @param {string} [fallback]
 * @returns {{ general: string, fields: Record<string, string> }}
 */
export function extractAllErrors(err, fallback) {
  return {
    general: extractError(err, fallback),
    fields: extractFieldErrors(err),
  }
}