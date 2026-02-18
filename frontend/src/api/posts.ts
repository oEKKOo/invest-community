import { get, post, patch, del } from './index'
import * as likesApi from './likes'
import type { Post, PaginatedResponse, PostStatus } from '@/types'

// 获取帖子列表
export interface GetPostsParams {
  status?: string
  authorId?: number
  tag?: string
  q?: string
  sort?: 'new' | 'hot'
  page?: number
  pageSize?: number
}

export const getPosts = (params?: GetPostsParams): Promise<PaginatedResponse<Post>> => {
  return get('/posts/', { params })
}

// 获取帖子详情
export const getPost = (id: number): Promise<Post> => {
  return get(`/posts/${id}/`)
}

// 创建帖子
export interface CreatePostParams {
  title: string
  content: string
  tags?: string[]
  status?: PostStatus
  assetIds?: number[]
}

export const createPost = (params: CreatePostParams): Promise<Post> => {
  return post('/posts/', params)
}

// 更新帖子
export const updatePost = (id: number, params: Partial<CreatePostParams>): Promise<Post> => {
  return patch(`/posts/${id}/`, params)
}

// 删除帖子
export const deletePost = (id: number): Promise<void> => {
  return del(`/posts/${id}/`)
}

// 收藏/取消收藏帖子
export const favoritePost = (id: number): Promise<void> => {
  return post(`/posts/${id}/favorite/`)
}

export const unfavoritePost = (id: number): Promise<void> => {
  return del(`/posts/${id}/favorite/`)
}

// 获取帖子评论
export const getPostComments = (postId: number, params?: { page?: number; pageSize?: number }) => {
  return get(`/posts/${postId}/comments/`, { params })
}

// 发表评论
export interface CreateCommentParams {
  text: string
  parentId?: number
  replyToUserId?: number
}

export const createComment = (postId: number, params: CreateCommentParams) => {
  return post(`/posts/${postId}/comments/`, params)
}

// 删除评论
export const deleteComment = (commentId: number): Promise<void> => {
  return del(`/comments/${commentId}/`)
}

// 获取我的收藏列表
export const getMyFavorites = (params?: { page?: number; pageSize?: number }): Promise<{ items: Post[]; total: number }> => {
  return get('/users/me/favorites/', { params })
}