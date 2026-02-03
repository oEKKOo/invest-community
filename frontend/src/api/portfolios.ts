import { get, post, patch, del } from './index'
import type { Portfolio, PaginatedResponse, PortfolioAsset } from '@/types'

// 获取投资组合列表
export interface GetPortfoliosParams {
  userId?: number
  isPublic?: boolean
  sortBy?: 'returnsYTD' | 'new'
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