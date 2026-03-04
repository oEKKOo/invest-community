import { get } from './index'
import type { Post, PaginatedResponse, Portfolio } from '@/types'

// 关注流 / 社交 Feed：我关注的人发布的帖子
export const getFollowingFeed = (params?: {
  page?: number
  pageSize?: number
}): Promise<PaginatedResponse<Post>> => {
  return get('/feed/following/', { params })
}

// 关注用户公开组合更新流
export const getFollowingPortfoliosFeed = (params?: {
  page?: number
  pageSize?: number
}): Promise<PaginatedResponse<Portfolio>> => {
  return get('/feed/following-portfolios/', { params })
}

