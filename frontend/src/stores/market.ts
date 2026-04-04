import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AssetQuote, MarketRankingItem, QuoteCacheEntry, BulkQuoteItem } from '@/types/market'
import { getAssetQuote, getBulkQuotes, getMarketRankings } from '@/api/market'

const CACHE_TTL = 60 * 1000 // 60秒缓存
type RankingsCacheEntry = {
  items: MarketRankingItem[]
  fetchedAt: number
}

export const useMarketStore = defineStore('market', () => {
  // 行情缓存 Map<assetId, { data, fetchedAt }>
  const quoteCache = ref(new Map<number, QuoteCacheEntry>())
  const quoteRequests = new Map<number, Promise<AssetQuote | null>>()
  
  // 榜单缓存（key 含 limit，与接口参数一致）
  const rankingList = ref<MarketRankingItem[]>([])
  const rankingFetchedAt = ref<number>(0)
  const rankingType = ref<string>('gainers')
  const rankingsCache = ref(new Map<string, RankingsCacheEntry>())
  const rankingRequests = new Map<string, Promise<MarketRankingItem[]>>()

  const rankingsCacheKey = (type: string, market: string | undefined, limit: number) =>
    `${type}:${market || 'ALL'}:${limit}`

  // =============================================
  // 辅助方法
  // =============================================
  
  // 判断缓存是否有效
  const isCacheValid = (fetchedAt: number): boolean => {
    return Date.now() - fetchedAt < CACHE_TTL
  }

  // 从缓存获取行情
  const getCachedQuote = (assetId: number): AssetQuote | null => {
    const entry = quoteCache.value.get(assetId)
    if (entry && isCacheValid(entry.fetchedAt)) {
      return entry.data
    }
    return null
  }

  // 设置行情缓存
  const setQuoteCache = (assetId: number, data: AssetQuote) => {
    quoteCache.value.set(assetId, { data, fetchedAt: Date.now() })
  }

  // =============================================
  // Actions
  // =============================================

  // 获取单资产行情（带缓存）
  const fetchQuote = async (assetId: number, forceRefresh = false): Promise<AssetQuote | null> => {
    if (!forceRefresh) {
      const cached = getCachedQuote(assetId)
      if (cached) return cached
    }

    const inflight = quoteRequests.get(assetId)
    if (inflight) {
      return inflight
    }
    
    const request = getAssetQuote(assetId)
      .then((data) => {
        setQuoteCache(assetId, data)
        return data
      })
      .catch((error) => {
        console.error(`获取资产 ${assetId} 行情失败:`, error)
        return null
      })
      .finally(() => {
        quoteRequests.delete(assetId)
      })

    quoteRequests.set(assetId, request)
    return request
  }

  // 批量获取行情（带缓存）
  const fetchBulkQuotes = async (assetIds: number[]): Promise<Map<number, BulkQuoteItem>> => {
    const result = new Map<number, BulkQuoteItem>()
    const toFetch: number[] = []

    // 先从缓存中取
    for (const id of assetIds) {
      const cached = getCachedQuote(id)
      if (cached) {
        result.set(id, {
          assetId: id,
          code: cached.code,
          name: cached.name,
          market: cached.market,
          price: cached.price !== null ? Number(cached.price) : null,
          changePct: cached.changePct !== null ? Number(cached.changePct) : null,
          change: cached.change !== null ? Number(cached.change) : null,
          quoteTime: cached.quoteTime,
          dataUpdatedAt: cached.dataUpdatedAt
        })
      } else {
        toFetch.push(id)
      }
    }

    // 批量请求未缓存的
    if (toFetch.length > 0) {
      try {
        const res = await getBulkQuotes(toFetch)
        for (const item of res.items) {
          result.set(item.assetId, item)
          // 写入缓存（有价格数据才缓存）
          if (item.price !== null && !item.error) {
            const quote: AssetQuote = {
              assetId: item.assetId,
              code: item.code || '',
              name: item.name || '',
              market: item.market || '',
              quoteTime: item.quoteTime,
              price: item.price,
              change: item.change,
              changePct: item.changePct,
              open: null,
              high: null,
              low: null,
              prevClose: null,
              volume: null,
              amount: null,
              dataUpdatedAt: item.dataUpdatedAt,
              isStale: false
            }
            setQuoteCache(item.assetId, quote)
          }
        }
      } catch (error) {
        console.error('批量获取行情失败:', error)
      }
    }

    return result
  }

  /** 过期缓存也返回，供首页 stale-while-revalidate 先渲染卡片 */
  const peekStaleRankings = (
    type: string = 'gainers',
    market?: string,
    limit: number = 50
  ): MarketRankingItem[] | null => {
    const cacheKey = rankingsCacheKey(type, market, limit)
    const cached = rankingsCache.value.get(cacheKey)
    if (cached?.items?.length) return cached.items
    return null
  }

  // 获取榜单（带缓存）
  const fetchRankings = async (
    type: string = 'gainers',
    market?: string,
    limit: number = 50
  ): Promise<MarketRankingItem[]> => {
    const cacheKey = rankingsCacheKey(type, market, limit)
    const cached = rankingsCache.value.get(cacheKey)
    if (cached && isCacheValid(cached.fetchedAt)) {
      rankingList.value = cached.items
      rankingFetchedAt.value = cached.fetchedAt
      rankingType.value = type
      return cached.items
    }

    const inflight = rankingRequests.get(cacheKey)
    if (inflight) {
      return inflight
    }

    const request = getMarketRankings({ type: type as any, market: market as any, limit })
      .then((res) => {
        rankingsCache.value.set(cacheKey, {
          items: res.items,
          fetchedAt: Date.now()
        })
        rankingList.value = res.items
        rankingFetchedAt.value = Date.now()
        rankingType.value = type
        return res.items
      })
      .catch((error) => {
        console.error('获取榜单失败:', error)
        return []
      })
      .finally(() => {
        rankingRequests.delete(cacheKey)
      })

    rankingRequests.set(cacheKey, request)

    try {
      return await request
    } catch (error) {
      console.error('获取榜单失败:', error)
      return []
    }
  }

  // 更新行情缓存（用于SSE推送更新）
  const updateQuoteFromStream = (data: Partial<AssetQuote> & { assetId: number }) => {
    const existing = quoteCache.value.get(data.assetId)
    if (existing) {
      quoteCache.value.set(data.assetId, {
        data: { ...existing.data, ...data },
        fetchedAt: Date.now()
      })
    } else if (data.price !== undefined) {
      quoteCache.value.set(data.assetId, {
        data: data as AssetQuote,
        fetchedAt: Date.now()
      })
    }
  }

  // 清理过期缓存
  const cleanExpiredCache = () => {
    for (const [id, entry] of quoteCache.value.entries()) {
      if (!isCacheValid(entry.fetchedAt)) {
        quoteCache.value.delete(id)
      }
    }
  }

  return {
    quoteCache,
    rankingList,
    rankingType,
    getCachedQuote,
    fetchQuote,
    fetchBulkQuotes,
    fetchRankings,
    peekStaleRankings,
    updateQuoteFromStream,
    cleanExpiredCache
  }
})
