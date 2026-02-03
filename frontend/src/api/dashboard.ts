import { get } from './index'
import type { DashboardData } from '@/types'

// 获取Dashboard概览数据
export const getDashboardOverview = (): Promise<DashboardData> => {
  return get('/dashboard/overview/')
}