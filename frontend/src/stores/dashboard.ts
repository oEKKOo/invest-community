import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DashboardData } from '@/types'
import * as dashboardApi from '@/api/dashboard'

const DASHBOARD_CACHE_TTL = 60 * 1000

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const dashboardData = ref<DashboardData | null>(null)
  const loading = ref(false)
  const fetchedAt = ref(0)
  let inflightRequest: Promise<DashboardData> | null = null

  // Actions
  const fetchDashboardData = async (forceRefresh = false) => {
    if (!forceRefresh && dashboardData.value && Date.now() - fetchedAt.value < DASHBOARD_CACHE_TTL) {
      return dashboardData.value
    }

    if (inflightRequest) {
      return inflightRequest
    }

    loading.value = true
    inflightRequest = dashboardApi
      .getDashboardOverview()
      .then((data) => {
        dashboardData.value = data
        fetchedAt.value = Date.now()
        return data
      })
      .catch((error) => {
        console.error('Failed to fetch dashboard data:', error)
        throw error
      })
      .finally(() => {
        loading.value = false
        inflightRequest = null
      })

    return inflightRequest
  }

  return {
    // State
    dashboardData,
    loading,
    
    // Actions
    fetchDashboardData
  }
})
