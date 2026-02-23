// 行情相关类型定义

// 行情快照
export interface AssetQuote {
  assetId: number
  code: string
  name: string
  market: string
  quoteTime: string | null
  price: string | number | null
  change: string | number | null
  changePct: string | number | null
  open: string | number | null
  high: string | number | null
  low: string | number | null
  prevClose: string | number | null
  volume: number | null
  amount: number | null
  dataUpdatedAt: string | null
  isStale: boolean
}

// K线条目
export interface AssetKlineItem {
  time: string
  open: string | number
  high: string | number
  low: string | number
  close: string | number
  volume: number
}

// K线数据容器
export interface AssetKlineData {
  assetId: number
  code: string
  interval: string
  resolution: string
  count: number
  items: AssetKlineItem[]
}

// 分时数据条目
export interface IntradayItem {
  time: string
  price: number
  avgPrice: number
  volume: number
  open?: number
  high?: number
  low?: number
}

// 榜单条目
export interface MarketRankingItem {
  rank: number
  assetId: number
  code: string
  name: string
  market: string
  price: number | null
  changePct: number | null
  change: number | null
  volume: number | null
  quoteTime: string | null
}

// 数据任务状态
export interface DataJobStatus {
  id: number
  jobType: string
  status: 'RUNNING' | 'SUCCESS' | 'FAILED'
  message: string
  affectedRows: number
  startedAt: string
  finishedAt: string | null
  durationSeconds: number | null
}

// 批量行情结果条目
export interface BulkQuoteItem {
  assetId: number
  code?: string
  name?: string
  market?: string
  price: number | null
  changePct: number | null
  change: number | null
  quoteTime: string | null
  dataUpdatedAt: string | null
  error?: string
}

// 批量行情结果
export interface BulkQuoteResult {
  items: BulkQuoteItem[]
  total: number
}

// 市场数据状态（管理员）
export interface MarketStatus {
  finnhubKeyConfigured: boolean
  assetCount: number
  snapshotCount: number
  klineCount: number
  recentJobs: Record<string, {
    status: string
    started_at: string
    affected_rows: number
  }>
}

// 行情缓存条目
export interface QuoteCacheEntry {
  data: AssetQuote
  fetchedAt: number
}

// 扩展已有 Asset 类型的额外字段（在 types/index.ts 中的 Asset 已有基础字段）
export interface AssetExtended {
  id: number
  code: string
  name: string
  asset_type: 'STOCK' | 'FUND' | 'ETF' | 'BOND'
  market?: string
  // 新增扩展字段
  finnhub_symbol?: string
  exchange?: string
  currency?: string
  isin?: string
  industry?: string
  logo_url?: string
  description?: string
  status?: string
  last_sync_at?: string
  // 内嵌行情快照（可选）
  quote?: AssetQuote | null
  // 列表页附带的行情字段
  price?: string | number | null
  changePct?: string | number | null
  quoteTime?: string | null
}
