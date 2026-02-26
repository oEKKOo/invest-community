import { get, post, patch, del } from './index'
import type { UserHolding, HoldingPerformance } from '@/types'

export interface HoldingsListResult {
  items: UserHolding[]
  total: number
}

// 获取我的持仓列表
export const getMyHoldings = (): Promise<HoldingsListResult> => {
  return get('/holdings/')
}

// 新增或更新持仓（按 assetId 做 upsert）
export interface UpsertHoldingParams {
  assetId: number
  quantity: number
  costPrice: number
  notes?: string
}

export const upsertHolding = (params: UpsertHoldingParams): Promise<UserHolding> => {
  return post('/holdings/', params)
}

// 更新单条持仓
export const updateHolding = (id: number, params: Partial<UpsertHoldingParams>): Promise<UserHolding> => {
  return patch(`/holdings/${id}/`, params)
}

// 删除持仓
export const deleteHolding = (id: number): Promise<void> => {
  return del(`/holdings/${id}/`)
}

// 获取持仓收益（基于每日快照，模拟基金净值效果）
export const getHoldingPerformance = (): Promise<HoldingPerformance> => {
  return get('/holdings/performance/')
}
