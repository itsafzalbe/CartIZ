import axios from 'axios'
import { getAccess, getRefresh, setTokens, clearTokens } from '../utils/token'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '',
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use(config => {
  const token = getAccess()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing = false
let queue = []

const processQueue = (error, token = null) => {
  queue.forEach(p => error ? p.reject(error) : p.resolve(token))
  queue = []
}

client.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config
    if (err.response?.status !== 401 || original._retry) {
      return Promise.reject(err)
    }
    if (refreshing) {
      return new Promise((resolve, reject) => {
        queue.push({ resolve, reject })
      }).then(token => {
        original.headers.Authorization = `Bearer ${token}`
        return client(original)
      })
    }
    original._retry = true
    refreshing = true
    try {
      const { data } = await axios.post('/accounts/token/refresh/', { refresh: getRefresh() })
      const { access, refresh } = data.data
      setTokens({ access, refresh })
      processQueue(null, access)
      original.headers.Authorization = `Bearer ${access}`
      return client(original)
    } catch (e) {
      processQueue(e, null)
      clearTokens()
      window.location.href = '/login'
      return Promise.reject(e)
    } finally {
      refreshing = false
    }
  }
)

export default client
