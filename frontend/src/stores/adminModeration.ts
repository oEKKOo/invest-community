// TODO(cleanup): 当前审核队列页面尚未消费该 store，暂作为状态统一改造的预留实现。
// 若后续继续保持页面直调 API，可在确认无引用后清理该文件。
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as adminApi from '@/api/admin'

export const useAdminModerationStore = defineStore('adminModeration', () => {
  const queueItems = ref<adminApi.ModerationQueueItem[]>([])
  const rules = ref<adminApi.ModerationRule[]>([])
  const loading = ref(false)

  const fetchQueue = async (params?: Parameters<typeof adminApi.getModerationQueue>[0]) => {
    loading.value = true
    try {
      const res = await adminApi.getModerationQueue(params)
      queueItems.value = res.items
      return res
    } finally {
      loading.value = false
    }
  }

  const fetchRules = async () => {
    const res = await adminApi.getModerationRules()
    rules.value = res.items
    return res
  }

  return {
    queueItems,
    rules,
    loading,
    fetchQueue,
    fetchRules
  }
})
