import { get, patch, post } from './index'
import type {
  Post,
  Report,
  PaginatedResponse,
  AdminStats,
  PostStatus,
  Alert,
  ModeratedUser
} from '@/types'

// 获取待审核帖子
export const getPendingPosts = (params?: { page?: number; pageSize?: number }): Promise<PaginatedResponse<Post>> => {
  return get('/admin/posts/', { params: { ...params, status: 'PENDING_REVIEW' } })
}

// 审核帖子
export interface ReviewPostParams {
  status: PostStatus
  rejectReason?: string
}

export const reviewPost = (postId: number, params: ReviewPostParams): Promise<void> => {
  return patch(`/admin/posts/${postId}/status/`, params)
}

// 获取待处理举报
export const getPendingReports = (
  params?: { page?: number; pageSize?: number }
): Promise<PaginatedResponse<Report>> => {
  return get('/admin/reports/', { params: { ...params, status: 'PENDING' } })
}

// 处理举报
export interface HandleReportParams {
  status: 'RESOLVED'
  result?: 'VALID' | 'INVALID'
  handleResult: string
}

export const handleReport = (reportId: number, params: HandleReportParams): Promise<void> => {
  return patch(`/admin/reports/${reportId}/`, params)
}

// 获取管理统计数据
export const getAdminStats = (): Promise<AdminStats> => {
  return get('/admin/stats/')
}

// 告警列表
export const getAlerts = (
  params?: { status?: 'OPEN' | 'RESOLVED' | 'IGNORED'; alertType?: string }
): Promise<PaginatedResponse<Alert>> => {
  // 后端当前返回为简单列表，这里做一层兼容封装
  return get('/admin/alerts/', { params })
}

// 处理告警
export interface HandleAlertParams {
  status: 'OPEN' | 'RESOLVED' | 'IGNORED'
  handleResult?: string
}

export const handleAlert = (alertId: number, params: HandleAlertParams): Promise<void> => {
  return patch(`/admin/alerts/${alertId}/`, params)
}

// 用户治理：获取当前被禁言/封禁用户列表
export const getModeratedUsers = (): Promise<{ items: ModeratedUser[]; total: number }> => {
  return get('/admin/users/moderation/')
}

// 用户治理：直接更新用户状态
export const updateUserStatus = (
  userId: number,
  payload: { status: 'NORMAL' | 'MUTED' | 'BANNED'; reason?: string }
): Promise<void> => {
  return patch(`/admin/users/${userId}/status/`, payload)
}

// 用户治理：禁言（days 默认 7）
export const muteUser = (
  userId: number,
  payload: { days?: number; reason?: string }
): Promise<void> => {
  return post(`/admin/users/${userId}/mute/`, payload)
}

// 用户治理：封禁
export const banUser = (userId: number, payload: { reason?: string }): Promise<void> => {
  return post(`/admin/users/${userId}/ban/`, payload)
}

// 用户治理：解除禁言
export const unmuteUser = (userId: number, payload?: { reason?: string }): Promise<void> => {
  return post(`/admin/users/${userId}/unmute/`, payload || {})
}

// 用户治理：解除封禁
export const unbanUser = (userId: number, payload?: { reason?: string }): Promise<void> => {
  return post(`/admin/users/${userId}/unban/`, payload || {})
}