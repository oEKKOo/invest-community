import axios from 'axios'

const TOKEN_KEY = 'investhub_token'
const REFRESH_TOKEN_KEY = 'investhub_refresh_token'
const USER_KEY = 'investhub_user'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

export const getAccessToken = () => localStorage.getItem(TOKEN_KEY)
export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY)

export const setAccessToken = (token: string) => {
  localStorage.setItem(TOKEN_KEY, token)
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
