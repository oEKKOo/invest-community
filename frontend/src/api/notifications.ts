import { get, post } from './index'
import type { Notification, PaginatedResponse } from '@/types'

export interface GetNotificationsParams {
  unreadOnly?: boolean
  type?: string
  page?: number
  pageSize?: number
}

// 获取通知列表（支持未读过滤和分页）
export const getNotifications = (
  params?: GetNotificationsParams
): Promise<PaginatedResponse<Notification>> => {
  return get('/notifications/', { params })
}

// 标记单条通知为已读
export const markNotificationRead = (id: number): Promise<void> => {
  return post(`/notifications/${id}/read/`)
}

// 一键标记全部通知为已读
export const markAllNotificationsRead = (): Promise<void> => {
  return post('/notifications/read-all/')
}

