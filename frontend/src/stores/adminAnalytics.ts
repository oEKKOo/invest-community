import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as adminApi from '@/api/admin'

export const useAdminAnalyticsStore = defineStore('adminAnalytics', () => {
  const overview = ref<any>(null)
  const activity = ref<any[]>([])
  const topics = ref<any[]>([])
  const engagements = ref<any[]>([])
  const loading = ref(false)

  const fetchOverview = async () => {
    overview.value = await adminApi.getAnalyticsOverview()
    return overview.value
  }

  const fetchActivity = async (params?: Parameters<typeof adminApi.getAnalyticsActivity>[0]) => {
    const res = await adminApi.getAnalyticsActivity(params)
    activity.value = res.items || []
    return res
  }

  const fetchTopics = async (params?: Parameters<typeof adminApi.getAnalyticsTopicsHot>[0]) => {
    const res = await adminApi.getAnalyticsTopicsHot(params)
    topics.value = res.items || []
    return res
  }

  const fetchEngagements = async (params?: Parameters<typeof adminApi.getAnalyticsUsersEngagement>[0]) => {
    const res = await adminApi.getAnalyticsUsersEngagement(params)
    engagements.value = res.items || []
    return res
  }

  const fetchAll = async () => {
    loading.value = true
    try {
      await Promise.all([fetchOverview(), fetchActivity(), fetchTopics(), fetchEngagements()])
    } finally {
      loading.value = false
    }
  }

  return {
    overview,
    activity,
    topics,
    engagements,
    loading,
    fetchOverview,
    fetchActivity,
    fetchTopics,
    fetchEngagements,
    fetchAll
  }
})
