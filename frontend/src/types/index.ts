// 用户相关类型
export interface User {
  id: number
  username: string
  displayName: string
  avatar: string
  role: 'USER' | 'MODERATOR' | 'ADMIN'
  phoneVerified?: boolean
  emailVerified?: boolean
  identityLevel?: 'UNVERIFIED' | 'BASIC' | 'REAL_NAME' | 'PROFESSIONAL'
  realNameStatus?: 'NONE' | 'PENDING' | 'APPROVED' | 'REJECTED'
  professionalStatus?: 'NONE' | 'PENDING' | 'APPROVED' | 'REJECTED'
  riskAssessmentStatus?: 'NONE' | 'PENDING' | 'APPROVED' | 'REJECTED'
  riskLevel?: 'R1' | 'R2' | 'R3' | 'R4' | 'R5' | null
  vBadge?: boolean
  bio?: string
  investmentExperience?: string
  followers: number
  following: number
  created_at?: string
}

export interface PrivacySettings {
  profileVisibility: 'PUBLIC' | 'FOLLOWERS' | 'PRIVATE'
  showInvestProfile: boolean
  allowSearch: boolean
  showEmail: boolean
  showPhone: boolean
  allowStrangerDm: boolean
}

export interface AchievementBadge {
  code: string
  name: string
  description: string
}

export interface AchievementSummary {
  postCount: number
  featuredPostCount: number
  portfolioCount: number
  favoritesCount: number
  likesCount: number
  followersCount: number
  influenceScore: number
  badges: AchievementBadge[]
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
  /** 列表/卡片接口返回摘要；详情接口为全文 */
  excerpt?: string
  content?: string
  status: PostStatus
  tags: string[]
  likes: number
  comments: number
  /** 冗余收藏数（列表卡片接口返回） */
  favoriteCount?: number
  createdAt: string
  assets?: Asset[]
  boards?: Board[]
  contentType?: 'NORMAL' | 'LONGFORM' | 'POLL' | 'LIVE'
  poll?: Poll | null
  attachments?: Attachment[]
  reposts?: number
  isLiked?: boolean
  isFavorited?: boolean
  /** 首图缩略图 URL（列表卡片接口），省流 */
  thumbUrl?: string | null
}

export interface Attachment {
  id: number
  original_name?: string
  mime_type?: string
  file_size?: number
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  reject_reason?: string
  fileUrl?: string
  /** 图片小图 URL，列表/缩略用；详情仍可打开 fileUrl */
  thumbUrl?: string
  created_at?: string
}

export interface CommentAttachment {
  id: number
  original_name?: string
  mime_type?: string
  file_size?: number
  fileUrl?: string
  thumbUrl?: string
  created_at?: string
}

export interface PollOption {
  id: number
  text: string
  sort_order?: number
  vote_count: number
}

export interface Poll {
  id: number
  question: string
  allow_multiple: boolean
  expires_at?: string | null
  is_closed: boolean
  options: PollOption[]
  totalVotes: number
}

export interface Board {
  id: number
  name: string
  slug: string
  board_type: 'MARKET' | 'THEME' | 'COMPANY_RESEARCH' | 'QA'
  parentId?: number | null
  description?: string
  icon?: string
  sort_order: number
  status: 'ACTIVE' | 'INACTIVE'
  is_builtin: boolean
  market?: 'A_SHARE' | 'HK_STOCK' | 'US_STOCK' | 'FUTURES' | ''
  industry_code?: string
  stock_code?: string
  children?: Board[]
}

// 评论类型
export interface Comment {
  id: number
  authorId: number
  authorName: string
  authorAvatar?: string
  parentId?: number | null
  replyToUserId?: number | null
  replyToUsername?: string | null
  body: string
  likeCount: number
  createdAt: string
  isLiked?: boolean
  replies: Comment[]
  attachments?: CommentAttachment[]
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

export interface PortfolioHoldingDetail {
  assetId: number | null
  code: string
  name: string
  market: string
  weight: number
  price: number | null
  marketValue: number | null
  returnRate: number | null
}

export interface PortfolioReturnPoint {
  date: string
  totalValue: string
  returnRate: string
  coverage: number
}

export interface PortfolioReturnsHistory {
  range: '7d' | '30d' | 'all' | string
  portfolioId: number
  items: PortfolioReturnPoint[]
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
  totalReturn?: number | null
  dailyReturn?: number | null
  sevenDayReturn?: number | null
  isPublic: boolean
  visibility?: 'PUBLIC' | 'PRIVATE' | 'FOLLOWERS' | string
  likes: number
  favorites?: number
  subscriptionCount?: number
  assets: PortfolioAsset[]
  assetCount?: number
  isLiked?: boolean
  isFavorited?: boolean
  createdAt: string
  updatedAt?: string
  lastRebalanceAt?: string
  strategyNote?: string
  holdingDetails?: PortfolioHoldingDetail[]
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
  targetType: 'POST' | 'COMMENT' | 'USER' | 'PORTFOLIO'
  targetId: number
  reason: string
  status: 'PENDING' | 'RESOLVED'
  createdAt: string
  reportTypeDetail?: string
  priority?: number
  handledByName?: string
  handleResult?: string
  result?: string
  handleTime?: string
}

// 告警类型（Admin 告警中心）
export interface Alert {
  id: number
  alert_type: 'CONTENT_RISK' | 'USER_BEHAVIOR' | 'SYSTEM' | string
  title: string
  description: string
  related_object_type?: string
  related_object_id?: number
  severity: string
  status: 'OPEN' | 'RESOLVED' | 'IGNORED'
  handled_by_name?: string
  handle_result?: string
  created_at: string
  handle_time?: string
}

// 用户治理列表条目（管理员查看被禁言/封禁用户）
export interface ModeratedUser {
  id: number
  username: string
  displayName: string
  status: 'NORMAL' | 'MUTED' | 'BANNED'
  muteUntil?: string | null
  lastAction?: string | null
  lastReason?: string
  lastOperator?: string | null
  lastCreatedAt?: string | null
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
  /** 当 overview 请求带 include=rankings,gainers 等时由后端填充 */
  rankingsGainers?: { type: string; market: string | null; items: unknown[] }
  hotAssets?: { type: string; market: string | null; items: unknown[] }
  notificationsUnread?: number
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

// 群组相关
export interface Group {
  id: number
  name: string
  slug: string
  description: string
  avatar?: string
  tags: string[]
  topicDirection?: string
  visibility: 'PUBLIC' | 'PRIVATE' | 'APPROVAL'
  status: 'ACTIVE' | 'DISSOLVED'
  ownerId: number
  ownerName: string
  memberCount: number
  postCount: number
  fileCount: number
  createdAt: string
}

export interface GroupMember {
  id: number
  userId: number
  username: string
  displayName: string
  avatar?: string
  role: 'OWNER' | 'ADMIN' | 'MEMBER'
  status: 'ACTIVE' | 'LEFT' | 'REMOVED'
  joinedAt: string
}

export interface GroupPost {
  id: number
  groupId: number
  authorId: number
  authorName: string
  title: string
  body: string
  content_type: 'NORMAL' | 'LONGFORM' | 'POLL'
  status: 'PUBLISHED' | 'DELETED'
  like_count: number
  comment_count: number
  createdAt: string
}

export interface GroupFile {
  id: number
  groupId: number
  uploadedBy: number
  uploadedByName: string
  original_name: string
  mime_type?: string
  file_size: number
  visibility: 'GROUP_ONLY'
  status: 'ACTIVE' | 'DELETED'
  createdAt: string
  fileUrl: string
}

export interface GroupJoinRequest {
  id: number
  group_id: number
  userId: number
  userName: string
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED'
  message: string
  reviewedBy?: number
  reviewNote?: string
  createdAt: string
  reviewedAt?: string
}

export interface GroupReviewer {
  id: number
  group_id: number
  userId: number
  userName: string
  username: string
  createdAt: string
}

export interface GroupInvite {
  id: number
  groupId: number
  groupName: string
  groupVisibility: 'PUBLIC' | 'PRIVATE' | 'APPROVAL'
  inviterId: number
  inviterName: string
  inviteeId: number
  inviteeName: string
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED'
  message: string
  respondedAt?: string
  createdAt: string
}