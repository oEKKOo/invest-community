import { del, get, patch, post } from './index'
import type { AchievementSummary, PaginatedResponse, Portfolio, Post, PrivacySettings, User } from '@/types'

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

// 关注推荐：你可能感兴趣的用户 / 组合
export interface FollowingRecommendations {
  users: User[]
  portfolios: Portfolio[]
}

export const getFollowingRecommendations = (): Promise<FollowingRecommendations> => {
  return get('/feed/following/recommendations/')
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

export const getPrivacySettings = (): Promise<PrivacySettings> => {
  return get('/users/me/privacy-settings/')
}

export const updatePrivacySettings = (params: Partial<PrivacySettings>): Promise<PrivacySettings> => {
  return patch('/users/me/privacy-settings/', params)
}

export const getMyAchievements = (): Promise<AchievementSummary> => {
  return get('/users/me/achievements/')
}
