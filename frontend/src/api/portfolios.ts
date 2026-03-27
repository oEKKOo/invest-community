import { get, post, patch, del } from './index'
import type {
  Portfolio,
  PaginatedResponse,
  PortfolioAsset,
  PortfolioReturnsHistory
} from '@/types'

// 获取投资组合列表
export interface GetPortfoliosParams {
  userId?: number
  isPublic?: boolean
  sortBy?: 'returnsYTD' | 'new' | 'likes'
  page?: number
  pageSize?: number
}

export const getPortfolios = (params?: GetPortfoliosParams): Promise<PaginatedResponse<Portfolio>> => {
  return get('/portfolios/', { params })
}

// 获取热门组合
export const getTopPortfolios = (limit?: number): Promise<{ items: Portfolio[] }> => {
  return get('/portfolios/top/', { params: { limit } })
}

// 获取投资组合详情
export const getPortfolio = (id: number): Promise<Portfolio> => {
  return get(`/portfolios/${id}/`)
}

// 创建投资组合
export interface CreatePortfolioParams {
  title: string
  description?: string
  strategyNote?: string
  riskLevel: 'Low' | 'Medium' | 'High'
  isPublic?: boolean
  assets: PortfolioAsset[]
}

export const createPortfolio = (params: CreatePortfolioParams): Promise<Portfolio> => {
  return post('/portfolios/', params)
}

// 更新投资组合
export const updatePortfolio = (id: number, params: Partial<CreatePortfolioParams>): Promise<Portfolio> => {
  return patch(`/portfolios/${id}/`, params)
}

// 删除投资组合
export const deletePortfolio = (id: number): Promise<void> => {
  return del(`/portfolios/${id}/`)
}

// 组合评论
export const getPortfolioComments = (
  id: number
): Promise<{ items: any[] }> => {
  return get(`/portfolios/${id}/comments/`)
}

export const createPortfolioComment = (
  id: number,
  payload: { body: string; parentId?: number | null; replyToUserId?: number | null }
): Promise<any> => {
  return post(`/portfolios/${id}/comments/`, payload)
}

// 组合订阅（开关）
export const togglePortfolioSubscribe = (id: number): Promise<{ message: string }> => {
  return post(`/portfolios/${id}/subscribe/`)
}

// 组合收藏（开关）
export const togglePortfolioFavorite = (id: number): Promise<{ message: string }> => {
  return post(`/portfolios/${id}/favorite/`)
}

// 组合更新日志
export const getPortfolioUpdates = (id: number): Promise<{ items: any[] }> => {
  return get(`/portfolios/${id}/updates/`)
}

// 组合收益趋势曲线
export const getPortfolioReturnsHistory = (
  id: number,
  range: '7d' | '30d' | 'all' = '30d'
): Promise<PortfolioReturnsHistory> => {
  return get(`/portfolios/${id}/returns-history/`, { params: { range } })
}