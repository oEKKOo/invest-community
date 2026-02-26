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

// 投资组合资产配置（升级版，含强外键关联）
export interface PortfolioAsset {
  // 新接口字段（强关联 Asset 表）
  assetId?: number | null
  market?: string
  assetType?: string
  displayMarket?: string
  // 兼容旧接口/展示用冗余字段
  symbol: string
  name: string
  allocation: number
}

// 个人持仓
export interface UserHolding {
  id: number
  assetId: number
  code: string
  name: string
  market: string
  assetType: string
  displayMarket: string
  quantity: number | string
  costPrice: number | string
  notes: string
  createdAt: string
  updatedAt: string
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

// ============================================================
// 持仓收益相关类型（基于每日快照计算）
// ============================================================

/** 单只持仓的收益明细 */
export interface HoldingPerformanceItem {
  holdingId: number
  assetId: number
  code: string
  name: string
  market: string
  displayMarket: string
  assetType: string
  quantity: string
  costPrice: string        // 成本均价
  todayPrice: string | null    // 今日估值价（日K close）
  yesterdayPrice: string | null  // 昨日估值价
  marketValue: string | null   // 今日市值 = quantity × todayPrice
  costValue: string          // 持仓成本 = quantity × costPrice
  unrealizedPnl: string | null // 持有收益 = marketValue - costValue
  unrealizedReturn: string | null // 持有收益率（如 "0.0556" = 5.56%）
  dailyPnl: string | null      // 当日收益 = quantity × (today - yesterday)
  dailyReturn: string | null   // 当日收益率
  snapshotDate: string | null  // 快照日期 YYYY-MM-DD
  hasData: boolean           // false 表示无K线快照，价格字段均 null
}

/** 持仓收益汇总 */
export interface HoldingPerformance {
  asOf: string | null          // 估值基准日期
  totalMarketValue: string     // 总市值
  totalCostValue: string       // 总持仓成本
  totalUnrealizedPnl: string   // 总持有收益
  totalUnrealizedReturn: string  // 总持有收益率（如 "0.2000" = 20%）
  totalDailyPnl: string        // 总当日收益
  totalDailyReturn: string     // 总当日收益率
  hasAnyData: boolean          // 是否有任意一只有快照数据
  items: HoldingPerformanceItem[]
}