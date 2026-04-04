import { onUnmounted, ref } from 'vue'
import { useMarketStore } from '@/stores/market'

// SSE 行情实时推送（用 getter 支持路由复用组件时切换标的）
export function useQuoteStream(getAssetId: () => number) {
  const marketStore = useMarketStore()
  const isConnected = ref(false)
  const hasError = ref(false)

  let es: EventSource | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectDelay = 3000
  const MAX_DELAY = 30000

  const connect = () => {
    if (es) {
      es.close()
    }

    const assetId = getAssetId()
    if (!Number.isFinite(assetId) || assetId <= 0) return

    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
    const token = localStorage.getItem('investhub_token')
    const url = `${baseURL}/assets/${assetId}/quote/stream/${token ? `?token=${token}` : ''}`

    try {
      es = new EventSource(url)
      
      es.onopen = () => {
        isConnected.value = true
        hasError.value = false
        reconnectDelay = 3000 // 重置退避时间
      }

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.assetId) {
            marketStore.updateQuoteFromStream(data)
          }
        } catch (e) {
          console.error('SSE 数据解析失败:', e)
        }
      }

      es.addEventListener('close', () => {
        isConnected.value = false
        es?.close()
        // 服务端主动关闭后不再重连
      })

      es.onerror = (_e) => {
        isConnected.value = false
        hasError.value = true
        es?.close()
        es = null
        // 指数退避重连
        if (reconnectDelay <= MAX_DELAY) {
          reconnectTimer = setTimeout(() => {
            reconnectDelay = Math.min(reconnectDelay * 2, MAX_DELAY)
            connect()
          }, reconnectDelay)
        }
      }
    } catch (e) {
      console.error('SSE 连接失败:', e)
      hasError.value = true
    }
  }

  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (es) {
      es.close()
      es = null
    }
    isConnected.value = false
  }

  // 页面卸载时自动断开
  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    hasError,
    connect,
    disconnect
  }
}
