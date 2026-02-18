import { get, post, del } from './index'
import type { PaginatedResponse } from '@/types'

// 点赞
export interface LikeParams {
  targetType: 'POST' | 'COMMENT' | 'PORTFOLIO'
  targetId: number
}

export const like = (params: LikeParams): Promise<void> => {
  return post('/likes/', params)
}

// 取消点赞
export const unlike = (params: LikeParams): Promise<void> => {
  return del('/likes/', { data: params })
}

// 点赞记录中的目标摘要
export interface LikeTargetSummary {
  id: number
  title?: string
  body?: string
  authorName?: string
  ownerName?: string
  postId?: number
  postTitle?: string
}

// 点赞记录条目
export interface LikeRecord {
  id: number
  targetType: 'POST' | 'COMMENT' | 'PORTFOLIO'
  targetId: number
  createdAt: string
  target: LikeTargetSummary | null
}

// 获取我的点赞记录
export const getMyLikes = (params?: { page?: number; pageSize?: number }): Promise<PaginatedResponse<LikeRecord>> => {
  return get('/users/me/likes/', { params })
}
