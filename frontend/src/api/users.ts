import { get, post, del } from './index'
import type { Post, PaginatedResponse, Portfolio, User } from '@/types'

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

// 用户关注关系项
export interface UserFollowItem {
  follower: User
  followee: User
  created_at: string
}

// 获取用户粉丝列表
export const getUserFollowers = (userId: number): Promise<UserFollowItem[]> => {
  return get(`/users/${userId}/followers/`)
}

// 获取用户关注列表
export const getUserFollowing = (userId: number): Promise<UserFollowItem[]> => {
  return get(`/users/${userId}/following/`)
}

// 关注用户
export const followUser = (userId: number): Promise<void> => {
  return post(`/users/${userId}/follow/`)
}

// 取消关注用户
export const unfollowUser = (userId: number): Promise<void> => {
  return del(`/users/${userId}/follow/`)
}
