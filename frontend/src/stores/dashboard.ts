import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DashboardData } from '@/types'
import * as dashboardApi from '@/api/dashboard'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const dashboardData = ref<DashboardData | null>(null)
  const loading = ref(false)

  // Actions
  const fetchDashboardData = async () => {
    loading.value = true
    try {
      const data = await dashboardApi.getDashboardOverview()
      dashboardData.value = data
      return data
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    dashboardData,
    loading,
    
    // Actions
    fetchDashboardData
  }
})