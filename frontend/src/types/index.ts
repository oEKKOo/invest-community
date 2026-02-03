// 用户相关类型
export interface User {
  id: number
  username: string
  displayName: string
  avatar: string
  role: 'USER' | 'MODERATOR' | 'ADMIN'
  bio?: string
  followers: number
  following: number
  created_at?: string
}

// 帖子状态枚举
export enum PostStatus {
  DRAFT = 'DRAFT',
  PENDING_REVIEW = 'PENDING_REVIEW',
  PUBLISHED = 'PUBLISHED',
  REJECTED = 'REJECTED',
  TAKEN_DOWN = 'TAKEN_DOWN'
}

// 帖子类型
export interface Post {
  id: number
  authorId: number
  authorName: string
  authorAvatar?: string
  title: string
  content: string
  status: PostStatus
  tags: string[]
  likes: number
  comments: number
  createdAt: string
  assets?: Asset[]
  isLiked?: boolean
  isFavorited?: boolean
}

// 评论类型
export interface Comment {
  id: number
  authorId: number
  authorName: string
  authorAvatar?: string
  parentId?: number
  replyToUserId?: number
  replyToUsername?: string
  body: string
  likeCount: number
  createdAt: string
  isLiked?: boolean
  replies: Comment[]
}

// 资产类型
export interface Asset {
  id: number
  code: string
  name: string
  asset_type: 'STOCK' | 'FUND' | 'ETF' | 'BOND'
  market?: string
}

// 投资组合资产配置
export interface PortfolioAsset {
  symbol: string
  name: string
  allocation: number
}

// 投资组合类型
export interface Portfolio {
  id: number
  userId: number
  userName: string
  title: string
  description: string
  riskLevel: 'Low' | 'Medium' | 'High'
  returnsYTD: number
  isPublic: boolean
  likes: number
  assets: PortfolioAsset[]
  isLiked?: boolean
  createdAt: string
}

// 通知类型
export interface Notification {
  id: number
  notification_type: string
  title: string
  content: string
  related_object_type?: string
  related_object_id?: number
  is_read: boolean
  created_at: string
  read_at?: string
}

// API 响应基础类型
export interface ApiResponse<T = any> {
  code: number
  data?: T
  message?: string
  errors?: Record<string, string[]>
}

// 分页响应类型
export interface PaginatedResponse<T> {
  items: T[]
  page: number
  pageSize: number
  total: number
}

// 登录响应类型
export interface LoginResponse {
  access: string
  refresh: string
  user: User
}

// 举报类型
export interface Report {
  id: number
  reporterName?: string
  targetType: 'POST' | 'COMMENT' | 'USER'
  targetId: number
  reason: string
  status: 'PENDING' | 'RESOLVED'
  createdAt: string
}

// Dashboard 数据类型
export interface DashboardData {
  marketSeries: Array<{ name: string; value: number }>
  trendingPosts: Post[]
  topPortfolios: Portfolio[]
  communityStats: {
    activeInvestorsCount: number
    strategiesSharedCount: number
  }
}

// 管理员统计数据
export interface AdminStats {
  pendingPostsCount: number
  openReportsCount: number
  newUsers24h: number
}