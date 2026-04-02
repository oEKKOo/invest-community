import { get, post } from './index'
import type {
  AssetQuote,
  AssetKlineData,
  IntradayItem,
  BulkQuoteResult,
  MarketRankingItem,
  MarketStatus,
  DataJobStatus
} from '@/types/market'
import type { PaginatedResponse } from '@/types'

const KLINE_CACHE_TTL = 60 * 1000
const INTRADAY_CACHE_TTL = 30 * 1000
const klineCache = new Map<string, { data: AssetKlineData; fetchedAt: number }>()
const klineInflight = new Map<string, Promise<AssetKlineData>>()
const intradayCache = new Map<string, { data: IntradayData; fetchedAt: number }>()
const intradayInflight = new Map<string, Promise<IntradayData>>()

const isValidCache = (fetchedAt: number, ttl: number) => Date.now() - fetchedAt < ttl

// =============================================
// 行情接口
// =============================================

// 获取单资产最新行情
export const getAssetQuote = (assetId: number): Promise<AssetQuote> => {
  return get(`/assets/${assetId}/quote/`)
}

// 获取K线数据
export interface GetKlineParams {
  interval?: '1d' | '60m' | '1h' | '30m' | '15m' | '5m' | '1m' | '1w' | '1mo'
  limit?: number
  from?: string
  to?: string
}

export const getAssetKline = (assetId: number, params?: GetKlineParams): Promise<AssetKlineData> => {
  const cacheKey = `${assetId}:${params?.interval || '1d'}:${params?.limit || ''}:${params?.from || ''}:${params?.to || ''}`
  const cached = klineCache.get(cacheKey)
  if (cached && isValidCache(cached.fetchedAt, KLINE_CACHE_TTL)) {
    return Promise.resolve(cached.data)
  }

  const inflight = klineInflight.get(cacheKey)
  if (inflight) return inflight

  const request = get<AssetKlineData>(`/assets/${assetId}/kline/`, { params })
    .then((data) => {
      klineCache.set(cacheKey, { data, fetchedAt: Date.now() })
      return data
    })
    .finally(() => {
      klineInflight.delete(cacheKey)
    })

  klineInflight.set(cacheKey, request)
  return request
}

// 获取分时数据
export interface GetIntradayParams {
  date?: string
  interval?: '1m' | '5m' | '15m'
}

export interface IntradayData {
  assetId: number
  code: string
  date: string
  interval: string
  items: IntradayItem[]
}

export const getAssetIntraday = (assetId: number, params?: GetIntradayParams): Promise<IntradayData> => {
  const cacheKey = `${assetId}:${params?.date || 'latest'}:${params?.interval || 'default'}`
  const cached = intradayCache.get(cacheKey)
  if (cached && isValidCache(cached.fetchedAt, INTRADAY_CACHE_TTL)) {
    return Promise.resolve(cached.data)
  }

  const inflight = intradayInflight.get(cacheKey)
  if (inflight) return inflight

  const request = get<IntradayData>(`/assets/${assetId}/intraday/`, { params })
    .then((data) => {
      intradayCache.set(cacheKey, { data, fetchedAt: Date.now() })
      return data
    })
    .finally(() => {
      intradayInflight.delete(cacheKey)
    })

  intradayInflight.set(cacheKey, request)
  return request
}

// 批量获取行情
export const getBulkQuotes = (assetIds: number[]): Promise<BulkQuoteResult> => {
  return post('/assets/quotes/', { assetIds })
}

// 资产相关内容聚合
export interface GetAssetContentsParams {
  type?: string
  sort?: 'new' | 'hot'
  page?: number
  pageSize?: number
}

export interface AssetContentsResult {
  assetId: number
  assetCode: string
  assetName: string
  items: any[]
  page: number
  pageSize: number
  total: number
}

export const getAssetContents = (assetId: number, params?: GetAssetContentsParams): Promise<AssetContentsResult> => {
  return get(`/assets/${assetId}/contents/`, { params })
}

// =============================================
// 榜单接口
// =============================================

export interface GetMarketRankingsParams {
  type?: 'gainers' | 'losers' | 'active'
  limit?: number
  market?: 'SH' | 'SZ' | 'HK' | 'US'
}

export interface MarketRankingsResult {
  type: string
  market: string | null
  items: MarketRankingItem[]
}

export const getMarketRankings = (params?: GetMarketRankingsParams): Promise<MarketRankingsResult> => {
  return get('/market/rankings/', { params })
}

// =============================================
// 管理员接口
// =============================================

// 数据状态（管理员）
export const getMarketStatus = (): Promise<MarketStatus> => {
  return get('/market/status/')
}

// 任务日志（管理员）
export interface GetDataJobsParams {
  jobType?: string
  status?: string
  page?: number
  pageSize?: number
}

export interface DataJobsResult {
  items: DataJobStatus[]
  page: number
  pageSize: number
  total: number
}

export const getDataJobs = (params?: GetDataJobsParams): Promise<DataJobsResult> => {
  return get('/market/jobs/', { params })
}

// 手动触发任务（管理员）
export interface TriggerJobParams {
  jobType: 'SYMBOLS_SYNC' | 'KLINE_SYNC' | 'QUOTE_REFRESH' | 'DQ_CHECK' | 'CLEANUP'
  exchange?: string
  market?: string
  assetIds?: number[]
  resolution?: string
  daysBack?: number
  forceRefetch?: boolean
  days?: number
  daysToKeep?: number
}

export const triggerDataJob = (params: TriggerJobParams): Promise<DataJobStatus | { deleted: number }> => {
  return post('/market/jobs/trigger/', params)
}

// =============================================
// 资产搜索（带行情版）
// =============================================

export interface GetAssetsWithQuoteParams {
  q?: string
  type?: string
  market?: string
  withQuote?: number
  page?: number
  pageSize?: number
}

export interface AssetWithQuote {
  id: number
  code: string
  name: string
  asset_type: 'STOCK' | 'FUND' | 'ETF' | 'BOND'
  market?: string
  // withQuote=1 时附加
  price?: number | null
  change?: number | null        // 涨跌额
  changePct?: number | null     // 涨跌幅（%）
  volume?: number | null        // 成交量
  quoteTime?: string | null
  dataUpdatedAt?: string | null
}

export interface AssetsListResult {
  items: AssetWithQuote[]
  page: number
  pageSize: number
  total: number
}

export const getAssetsWithQuote = (params?: GetAssetsWithQuoteParams): Promise<AssetsListResult> => {
  return get('/assets/', { params })
}
