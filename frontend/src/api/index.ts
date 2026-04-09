import axios from 'axios'
import type { ApiResponse } from '../types'
import { notifyError } from '../utils/notify'
import { getAccessToken, refreshAccessToken, clearAuthStorage } from './auth-token'

let refreshingPromise: Promise<string> | null = null

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
    const token = getAccessToken()
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
      void notifyError(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    
    return response
  },
  async (error) => {
    const { response } = error
    
    if (response?.status === 401) {
      try {
        if (!refreshingPromise) {
          refreshingPromise = refreshAccessToken().finally(() => {
            refreshingPromise = null
          })
        }
        await refreshingPromise
        return api.request(error.config)
      } catch (refreshError) {
        clearAuthStorage()
        window.location.href = `${import.meta.env.BASE_URL}login`
        return Promise.reject(refreshError)
      }
    } else if (response?.status >= 500) {
      void notifyError('服务器错误，请稍后重试')
    } else if (response?.data?.message) {
      void notifyError(response.data.message)
    } else {
      void notifyError('网络错误，请检查网络连接')
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