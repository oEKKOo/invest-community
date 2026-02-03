import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginResponse } from '../types'
import * as authApi from '../api/auth'

const TOKEN_KEY = 'investhub_token'
const REFRESH_TOKEN_KEY = 'investhub_refresh_token'
const USER_KEY = 'investhub_user'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const refreshToken = ref<string>(localStorage.getItem(REFRESH_TOKEN_KEY) || '')
  const user = ref<User | null>(
    localStorage.getItem(USER_KEY) 
      ? JSON.parse(localStorage.getItem(USER_KEY)!) 
      : null
  )

  // Getters
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN' || user.value?.role === 'MODERATOR')

  // Actions
  const setAuth = (authData: LoginResponse) => {
    token.value = authData.access
    refreshToken.value = authData.refresh
    user.value = authData.user
    
    // 持久化到localStorage
    localStorage.setItem(TOKEN_KEY, authData.access)
    localStorage.setItem(REFRESH_TOKEN_KEY, authData.refresh)
    localStorage.setItem(USER_KEY, JSON.stringify(authData.user))
  }

  const clearAuth = () => {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    
    // 清除localStorage
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  const login = async (params: authApi.LoginParams) => {
    try {
      const response = await authApi.login(params)
      setAuth(response)
      return response
    } catch (error) {
      throw error
    }
  }

  const register = async (params: authApi.RegisterParams) => {
    try {
      const response = await authApi.register(params)
      setAuth(response)
      return response
    } catch (error) {
      throw error
    }
  }

  const logout = async () => {
    try {
      // 调用API登出（可选）
      if (token.value) {
        await authApi.logout()
      }
    } catch (error) {
      // 即使API调用失败也要清除本地数据
      console.error('Logout API error:', error)
    } finally {
      clearAuth()
    }
  }

  const refreshTokens = async () => {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }
    
    try {
      const response = await authApi.refreshToken(refreshToken.value)
      token.value = response.access
      localStorage.setItem(TOKEN_KEY, response.access)
      return response
    } catch (error) {
      // 刷新失败，清除所有认证信息
      clearAuth()
      throw error
    }
  }

  const fetchCurrentUser = async () => {
    if (!token.value) {
      throw new Error('Not authenticated')
    }
    
    try {
      const userData = await authApi.getCurrentUser()
      user.value = userData
      localStorage.setItem(USER_KEY, JSON.stringify(userData))
      return userData
    } catch (error) {
      // 获取用户信息失败，可能token无效
      clearAuth()
      throw error
    }
  }

  return {
    // State
    token,
    refreshToken,
    user,
    
    // Getters
    isLoggedIn,
    isAdmin,
    
    // Actions
    login,
    register,
    logout,
    refreshTokens,
    fetchCurrentUser,
    setAuth,
    clearAuth
  }
})