import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Notification, PaginatedResponse } from '@/types'
import * as notificationsApi from '@/api/notifications'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref<Notification[]>([])
  const loading = ref(false)
  const page = ref(1)
  const pageSize = ref(20)
  const total = ref(0)

  const unreadCount = computed(
    () => items.value.filter((n) => !n.is_read).length
  )

  const hasMore = computed(() => page.value * pageSize.value < total.value)

  const fetchNotifications = async (params?: {
    unreadOnly?: boolean
    page?: number
    pageSize?: number
  }) => {
    loading.value = true
    try {
      const res: PaginatedResponse<Notification> =
        await notificationsApi.getNotifications({
          unreadOnly: params?.unreadOnly,
          page: params?.page ?? page.value,
          pageSize: params?.pageSize ?? pageSize.value
        })

      items.value = res.items
      page.value = res.page
      pageSize.value = res.pageSize
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  const refreshUnread = async () => {
    // 复用列表接口，取未读列表的 total 作为未读数量
    const res = await notificationsApi.getNotifications({
      unreadOnly: true,
      page: 1,
      pageSize: 1
    })
    total.value = res.total
  }

  const markRead = async (id: number) => {
    await notificationsApi.markNotificationRead(id)
    const target = items.value.find((n) => n.id === id)
    if (target) {
      target.is_read = true
      target.read_at = new Date().toISOString()
    }
  }

  const markAllRead = async () => {
    await notificationsApi.markAllNotificationsRead()
    items.value = items.value.map((n) => ({
      ...n,
      is_read: true,
      read_at: n.read_at || new Date().toISOString()
    }))
  }

  return {
    items,
    loading,
    page,
    pageSize,
    total,
    unreadCount,
    hasMore,
    fetchNotifications,
    refreshUnread,
    markRead,
    markAllRead
  }
})

