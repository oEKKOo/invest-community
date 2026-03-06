import { post, get } from './index'
import type { PaginatedResponse, Report } from '@/types'

// 创建举报
export interface CreateReportParams {
  targetType: 'POST' | 'COMMENT' | 'USER' | 'PORTFOLIO'
  targetId: number
  reason: string
  reportTypeDetail?: string
  evidence?: any
}

export const createReport = (params: CreateReportParams): Promise<{ id: number }> => {
  return post('/reports/', params)
}

// 获取当前用户的举报列表
export const getMyReports = (params?: { page?: number; pageSize?: number }): Promise<PaginatedResponse<Report>> => {
  return get('/users/me/reports/', { params })
}

