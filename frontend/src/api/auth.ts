import { get, post, patch } from './index'
import type { User, LoginResponse } from '../types'

// 用户注册
export interface RegisterParams {
  username: string
  email: string
  password: string
  password_confirm: string
  phone?: string
}

// 注册接口返回的原始格式（扁平化）
export interface RegisterResponse {
  id: number
  username: string
  displayName: string
  role: 'USER' | 'MODERATOR' | 'ADMIN'
  access: string
  refresh: string
}

export const register = (params: RegisterParams): Promise<RegisterResponse> => {
  return post('/auth/register/', params)
}

// 用户登录
export interface LoginParams {
  username: string
  password: string
}

export const login = (params: LoginParams): Promise<LoginResponse> => {
  return post('/auth/login/', params)
}

// 刷新token
export const refreshToken = (refresh: string): Promise<{ access: string }> => {
  return post('/auth/refresh/', { refresh })
}

// 用户登出
export const logout = (): Promise<void> => {
  return post('/auth/logout/')
}

// 获取当前用户信息
export const getCurrentUser = (): Promise<User> => {
  return get('/users/me/')
}

// 更新当前用户信息
export interface UpdateUserParams {
  displayName?: string
  bio?: string
  avatar?: string
  phone?: string
}

export const updateCurrentUser = (params: UpdateUserParams): Promise<User> => {
  return patch('/users/me/', params)
}