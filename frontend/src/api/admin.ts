import { get, patch } from './index'
import type { Post, Report, PaginatedResponse, AdminStats, PostStatus } from '@/types'

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
export const getPendingReports = (params?: { page?: number; pageSize?: number }): Promise<PaginatedResponse<Report>> => {
  return get('/admin/reports/', { params: { ...params, status: 'PENDING' } })
}

// 处理举报
export interface HandleReportParams {
  status: 'RESOLVED'
  result: 'VALID' | 'INVALID'
  handleResult: string
}

export const handleReport = (reportId: number, params: HandleReportParams): Promise<void> => {
  return patch(`/admin/reports/${reportId}/`, params)
}

// 获取管理统计数据
export const getAdminStats = (): Promise<AdminStats> => {
  return get('/admin/stats/')
}