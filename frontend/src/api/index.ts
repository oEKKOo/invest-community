import axios from 'axios'
import type { ApiResponse } from '../types'
// Note: Import useAuthStore inside interceptors to avoid circular dependency
// import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'investhub_token'
const REFRESH_TOKEN_KEY = 'investhub_refresh_token'
const USER_KEY = 'investhub_user'

const clearAuthStorage = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    // 从localStorage获取token，避免循环依赖
    const token = localStorage.getItem('investhub_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 统一处理错误
api.interceptors.response.use(
  (response) => {
    const { data } = response
    
    // API返回code !== 0表示业务错误
    if (data.code !== 0) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    
    return response
  },
  async (error) => {
    const { response } = error
    
    if (response?.status === 401) {
      // token过期，尝试刷新
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      if (refreshToken) {
        try {
          // 动态导入避免循环依赖
          const { useAuthStore } = await import('../stores/auth')
          const authStore = useAuthStore()
          await authStore.refreshTokens()
          // 重新发送原请求
          return api.request(error.config)
        } catch (refreshError) {
          // 刷新失败，清除token并跳转登录
          clearAuthStorage()
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      } else {
        clearAuthStorage()
        window.location.href = '/login'
      }
    } else if (response?.status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    } else if (response?.data?.message) {
      ElMessage.error(response.data.message)
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

// 通用请求方法
export const request = <T = any>(config: any): Promise<T> => {
  return api.request(config).then((response) => response.data.data)
}

// GET请求
export const get = <T = any>(url: string, config?: any): Promise<T> => {
  return request({ ...config, method: 'GET', url })
}

// POST请求
export const post = <T = any>(url: string, data?: any, config?: any): Promise<T> => {
  return request({ ...config, method: 'POST', url, data })
}

// PUT请求
export const put = <T = any>(url: string, data?: any, config?: any): Promise<T> => {
  return request({ ...config, method: 'PUT', url, data })
}

// PATCH请求
export const patch = <T = any>(url: string, data?: any, config?: any): Promise<T> => {
  return request({ ...config, method: 'PATCH', url, data })
}

// DELETE请求
export const del = <T = any>(url: string, config?: any): Promise<T> => {
  return request({ ...config, method: 'DELETE', url })
}

export default api