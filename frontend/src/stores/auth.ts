import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginResponse } from '../types'
import * as authApi from '../api/auth'
import type { RegisterResponse } from '../api/auth'

const TOKEN_KEY = 'investhub_token'
const REFRESH_TOKEN_KEY = 'investhub_refresh_token'
const USER_KEY = 'investhub_user'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const refreshToken = ref<string>(localStorage.getItem(REFRESH_TOKEN_KEY) || '')
  
  // 安全地从 localStorage 读取用户信息
  let initialUser: User | null = null
  try {
    const userStr = localStorage.getItem(USER_KEY)
    if (userStr && userStr !== 'undefined' && userStr !== 'null') {
      initialUser = JSON.parse(userStr)
    }
  } catch (error) {
    console.warn('Failed to parse user from localStorage:', error)
    // 清除无效数据
    localStorage.removeItem(USER_KEY)
  }
  
  const user = ref<User | null>(initialUser)

  // Getters
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN' || user.value?.role === 'MODERATOR')
  const authCapabilities = computed(() => ({
    basicVerified: !!(user.value?.phoneVerified || user.value?.emailVerified),
    realNameVerified: user.value?.realNameStatus === 'APPROVED',
    professionalVerified: user.value?.professionalStatus === 'APPROVED',
    riskAssessed: user.value?.riskAssessmentStatus === 'APPROVED',
    canUseProFeatures: user.value?.professionalStatus === 'APPROVED' && user.value?.riskAssessmentStatus === 'APPROVED',
    vBadge: !!user.value?.vBadge
  }))

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

  const loginWithPassword = async (params: authApi.PasswordLoginParams) => {
    const response = await authApi.loginWithPassword(params)
    setAuth(response)
    return response
  }

  const loginWithSms = async (params: authApi.SmsLoginParams) => {
    const response = await authApi.loginWithSms(params)
    setAuth(response)
    return response
  }

  const register = async (params: authApi.RegisterParams) => {
    try {
      const response = await authApi.register(params) as RegisterResponse
      // 注册接口返回的数据格式与登录不同，需要转换
      // 注册返回: { id, username, displayName, role, access, refresh }
      // 需要转换为: { access, refresh, user: { id, username, displayName, role, ... } }
      if (response && response.access && response.refresh && response.id) {
        const loginResponse: LoginResponse = {
          access: response.access,
          refresh: response.refresh,
          user: {
            id: response.id,
            username: response.username,
            displayName: response.displayName || response.username,
            avatar: '',
            role: response.role || 'USER',
            bio: '',
            followers: 0,
            following: 0
          }
        }
        setAuth(loginResponse)
        return loginResponse
      }
      throw new Error('注册响应数据格式错误')
    } catch (error) {
      throw error
    }
  }

  const registerByEmail = async (params: authApi.EmailRegisterParams) => {
    const response = await authApi.registerEmail(params)
    setAuth(response)
    return response
  }

  const registerByPhone = async (params: authApi.PhoneRegisterParams) => {
    const response = await authApi.registerPhone(params)
    setAuth(response)
    return response
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
    authCapabilities,
    
    // Actions
    login,
    loginWithPassword,
    loginWithSms,
    register,
    registerByEmail,
    registerByPhone,
    logout,
    refreshTokens,
    fetchCurrentUser,
    setAuth,
    clearAuth
  }
})