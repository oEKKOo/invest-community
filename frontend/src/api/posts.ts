import { get, post, patch, del } from './index'
import * as likesApi from './likes'
import type { Post, Board, Attachment, Poll, PaginatedResponse, PostStatus, Comment, CommentAttachment } from '@/types'

// 获取帖子列表
export interface GetPostsParams {
  status?: string
  authorId?: number
  tag?: string
  boardId?: number
  boardIds?: number[]
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
  boardIds?: number[]
  contentType?: 'NORMAL' | 'LONGFORM' | 'POLL' | 'LIVE'
  formatType?: 'PLAIN' | 'RICH_TEXT'
  poll?: {
    question: string
    allowMultiple?: boolean
    expiresAt?: string
    options: Array<{ text: string }>
  }
  attachmentIds?: number[]
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

/** 帖子顶级评论分页（默认 page=1、pageSize=20） */
export interface PostCommentsPage {
  items: Comment[]
  page: number
  pageSize: number
  total: number
}

// 获取帖子评论
export const getPostComments = (
  postId: number,
  params?: { page?: number; pageSize?: number }
): Promise<PostCommentsPage> => {
  return get(`/posts/${postId}/comments/`, { params })
}

// 发表评论
export interface CreateCommentParams {
  text: string
  parentId?: number
  replyToUserId?: number
  attachmentIds?: number[]
}

export const createComment = (postId: number, params: CreateCommentParams) => {
  return post(`/posts/${postId}/comments/`, params)
}

// 删除评论
export const deleteComment = (commentId: number): Promise<void> => {
  return del(`/comments/${commentId}/`)
}

// 获取某条评论的子回复（分页）
export const getCommentReplies = (
  commentId: number,
  params?: { page?: number; pageSize?: number }
): Promise<{ items: Comment[]; page: number; pageSize: number; total: number }> => {
  return get(`/comments/${commentId}/replies/`, { params })
}

// 编辑评论
export const updateComment = (commentId: number, params: { text: string }): Promise<Comment> => {
  return patch(`/comments/${commentId}/`, params)
}

// 点赞/取消点赞评论（语义化封装，内部复用 likes 接口）
export const likeComment = (commentId: number): Promise<void> => {
  return likesApi.like({ targetType: 'COMMENT', targetId: commentId })
}

export const unlikeComment = (commentId: number): Promise<void> => {
  return likesApi.unlike({ targetType: 'COMMENT', targetId: commentId })
}

// 获取我的收藏列表
export const getMyFavorites = (params?: { page?: number; pageSize?: number }): Promise<{ items: Post[]; total: number }> => {
  return get('/users/me/favorites/', { params })
}

export interface GetBoardsParams {
  type?: 'MARKET' | 'THEME' | 'COMPANY_RESEARCH' | 'QA'
  parentId?: number
  status?: 'ACTIVE' | 'INACTIVE'
}

export const getBoards = (params?: GetBoardsParams): Promise<{ items: Board[]; total: number }> => {
  return get('/boards/', { params })
}

export const uploadContentAttachment = (file: File): Promise<Attachment> => {
  const form = new FormData()
  form.append('file', file)
  return post('/uploads/content/', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const uploadCommentAttachment = (file: File): Promise<CommentAttachment> => {
  const form = new FormData()
  form.append('file', file)
  return post('/uploads/comment/', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const votePoll = (postId: number, optionIds: number[]): Promise<void> => {
  return post(`/posts/${postId}/poll/vote/`, { optionIds })
}

export const getPollResult = (postId: number): Promise<Poll> => {
  return get(`/posts/${postId}/poll/result/`)
}

export const repostPost = (postId: number, comment?: string): Promise<void> => {
  return post(`/posts/${postId}/repost/`, { comment })
}

export const cancelRepost = (postId: number): Promise<void> => {
  return del(`/posts/${postId}/repost/`)
}

export const downloadContentAttachment = (
  attachmentId: number
): Promise<{ id: number; url: string; name: string; status: string }> => {
  return get(`/attachments/${attachmentId}/download/`)
}