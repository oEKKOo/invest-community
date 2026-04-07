import axios from 'axios'

const TOKEN_KEY = 'investhub_token'
const REFRESH_TOKEN_KEY = 'investhub_refresh_token'
const USER_KEY = 'investhub_user'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

export const getAccessToken = () => localStorage.getItem(TOKEN_KEY)
export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY)
export const getStoredUser = () => localStorage.getItem(USER_KEY)

export const setAccessToken = (token: string) => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const setRefreshToken = (token: string) => {
  localStorage.setItem(REFRESH_TOKEN_KEY, token)
}

export const setStoredUser = (user: string) => {
  localStorage.setItem(USER_KEY, user)
}

export const setAuthStorage = (payload: { access?: string; refresh?: string; user?: string | null }) => {
  if (payload.access !== undefined) {
    setAccessToken(payload.access)
  }
  if (payload.refresh !== undefined) {
    setRefreshToken(payload.refresh)
  }
  if (payload.user !== undefined) {
    if (payload.user === null) {
      localStorage.removeItem(USER_KEY)
    } else {
      setStoredUser(payload.user)
    }
  }
}

export const clearAuthStorage = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export const refreshAccessToken = async () => {
  const refresh = getRefreshToken()
  if (!refresh) throw new Error('No refresh token available')

  const response = await axios.post(
    `${baseURL}/auth/refresh/`,
    { refresh },
    { headers: { 'Content-Type': 'application/json' }, timeout: 10000 }
  )

  const payload = response.data
  const access = payload?.data?.access ?? payload?.access
  if (!access) throw new Error('Refresh token response is invalid')

  setAccessToken(access)
  return access as string
}
