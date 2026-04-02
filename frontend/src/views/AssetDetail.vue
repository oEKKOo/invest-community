<template>
  <div class="asset-detail">
    <!-- 面包屑导航-->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/market' }">行情列表</el-breadcrumb-item>
        <el-breadcrumb-item>{{ asset?.name || assetId }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <template v-if="asset">
      <!-- 区块 1: Asset Hero 卡片 -->
      <div class="quote-header-card card hero-card">
        <div class="asset-title">
          <div class="asset-code-name">
            <span class="asset-code">{{ asset.code }}</span>
            <span class="asset-name">{{ asset.name }}</span>
            <el-tag size="small" :type="marketTagType" class="market-tag">
              {{ marketLabel }}
            </el-tag>
            <el-tag size="small" type="info" class="type-tag">
              {{ asset.asset_type }}
            </el-tag>
          </div>
        </div>

        <!-- 行情数据 -->
        <div v-if="quoteLoading" class="quote-skeleton">
          <el-skeleton :rows="2" animated />
        </div>
        <div v-else-if="quote" class="quote-body">
          <!-- 主价格-->
          <div class="main-price-row">
            <span class="main-price" :class="priceColor">
              {{ formatPrice(quote.price) }}
            </span>
            <div class="change-info" :class="priceColor">
              <span class="change-amount">{{ formatChange(quote.change) }}</span>
              <span class="change-pct">{{ formatChangePct(quote.changePct) }}</span>
            </div>
          </div>

          <!-- 警告：数据陈旧-->
          <el-alert
            v-if="quote.isStale"
            type="warning"
            show-icon
            :closable="false"
            class="stale-alert"
          >
            <template #title>行情数据已超过60秒，可能不是最新</template>
          </el-alert>

          <!-- 开高低昨收成交量-->
          <div class="quote-metrics">
            <div class="metric-item">
              <span class="metric-label">开盘价</span>
              <span class="metric-value">{{ formatPrice(quote.open) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">最高价</span>
              <span class="metric-value up">{{ formatPrice(quote.high) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">最低价</span>
              <span class="metric-value down">{{ formatPrice(quote.low) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">昨收</span>
              <span class="metric-value">{{ formatPrice(quote.prevClose) }}</span>
            </div>
            <div class="metric-item" v-if="quote.volume !== null">
              <span class="metric-label">成交量</span>
              <span class="metric-value">{{ formatVolume(quote.volume) }}</span>
            </div>
          </div>

          <!-- 数据来源和时间-->
          <div class="quote-footer">
            <span class="data-source">数据来源：Finnhub | 更新时间：{{ formatQuoteTime(quote.quoteTime) }}</span>
          </div>
        </div>

        <!-- 行情获取失败 -->
        <div v-else-if="quoteError" class="quote-error">
          <el-empty description="暂无行情数据" :image-size="40" />
        </div>
      </div>

      <!-- 区块 2 & 3: K线图 + 分时图-->
      <div ref="chartSectionRef" class="chart-card card">
        <div class="card-header">
          <h3 class="card-title">走势图</h3>
          <div class="chart-type-tabs">
            <button
              class="chart-type-btn"
              :class="{ active: chartType === 'kline' }"
              @click="chartType = 'kline'"
            >K线图</button>
            <button
              class="chart-type-btn"
              :class="{ active: chartType === 'intraday' }"
              @click="chartType = 'intraday'"
            >分时图</button>
          </div>
        </div>

        <div v-if="!shouldRenderCharts" class="chart-lazy-skeleton">
          <el-skeleton :rows="6" animated />
        </div>
        <KlineChart
          v-else-if="chartType === 'kline'"
          :assetId="Number(assetId)"
          :limit="150"
        />
        <IntradayChart
          v-else
          :assetId="Number(assetId)"
        />
      </div>

      <!-- 区块 4: 公司简介（如果有） -->
      <div class="info-card card" v-if="asset.description || asset.industry">
        <div class="card-header">
          <h3 class="card-title">公司信息</h3>
        </div>
        <div class="company-info">
          <div class="info-row" v-if="asset.industry">
            <span class="info-label">行业</span>
            <span class="info-value">{{ asset.industry }}</span>
          </div>
          <div class="info-row" v-if="asset.exchange">
            <span class="info-label">交易所</span>
            <span class="info-value">{{ asset.exchange }}</span>
          </div>
          <div class="info-row" v-if="asset.currency">
            <span class="info-label">币种</span>
            <span class="info-value">{{ asset.currency }}</span>
          </div>
        </div>
        <el-collapse class="desc-collapse" v-if="asset.description">
          <el-collapse-item title="公司简介" name="desc">
            <p class="company-desc">{{ asset.description }}</p>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 区块 5: 相关内容聚合 -->
      <div class="contents-card card">
        <div class="card-header">
          <h3 class="card-title">相关讨论</h3>
          <div class="sort-tabs">
            <button
              class="sort-btn"
              :class="{ active: contentSort === 'new' }"
              @click="changeContentSort('new')"
            >最新</button>
            <button
              class="sort-btn"
              :class="{ active: contentSort === 'hot' }"
              @click="changeContentSort('hot')"
            >热门</button>
          </div>
        </div>

        <div v-if="contentsLoading" class="content-loading">
          <el-skeleton :rows="3" animated v-for="i in 3" :key="i" style="margin-bottom:16px" />
        </div>

        <div v-else-if="relatedContents.length === 0" class="content-empty">
          <el-empty description="暂无相关讨论" :image-size="60" />
        </div>

        <div v-else class="content-list">
          <div
            v-for="item in relatedContents"
            :key="item.id"
            class="content-item"
            @click="$router.push(`/posts/${item.id}`)"
          >
            <div class="content-item-main">
              <h4 class="content-title">{{ item.title }}</h4>
              <p class="content-excerpt" v-if="item.content">{{ item.content }}</p>
            </div>
            <div class="content-item-meta">
              <span
                class="author author-clickable"
                @click.stop="$router.push({ name: 'UserProfile', params: { userId: item.authorId } })"
              >
                {{ item.authorName }}
              </span>
              <span class="dot">·</span>
              <span class="like-count">
                <el-icon><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg></el-icon>
                {{ item.likes }}
              </span>
              <span class="dot">·</span>
              <span class="time">{{ formatDate(item.createdAt) }}</span>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div class="content-pagination" v-if="contentTotal > contentPageSize">
          <el-pagination
            v-model="contentPage"
            :page-size="contentPageSize"
            :total="contentTotal"
            layout="prev, pager, next"
            @current-change="loadContents"
          />
        </div>

        <!-- 查看更多 -->
        <div class="view-more" v-if="contentTotal > 0 && contentTotal <= contentPageSize">
          <router-link :to="`/community?assetId=${assetId}`" class="view-more-link">
            查看全部相关讨论
          </router-link>
        </div>
      </div>

      <!-- 区块 6: 快速发帖（登录用户）-->
      <div class="quick-post-card card" v-if="authStore.isLoggedIn">
        <div class="card-header">
          <h3 class="card-title">分享你的市场观察</h3>
        </div>
        <div class="quick-post-form">
          <el-input
            v-model="quickPostTitle"
            placeholder="输入帖子标题..."
            class="quick-title-input"
          />
          <el-input
            v-model="quickPostContent"
            type="textarea"
            :rows="4"
            placeholder="你怎么看这只股票？可以分享逻辑、风险点或操作思路。"
            class="quick-content-input"
          />
          <div class="quick-post-actions">
            <el-tag size="small" type="success">
              已关联：{{ asset.code }} {{ asset.name }}
            </el-tag>
            <el-button
              type="primary"
              size="small"
              :loading="quickPosting"
              @click="submitQuickPost"
              :disabled="!quickPostTitle || !quickPostContent"
            >
              发布讨论
            </el-button>
          </div>
        </div>
      </div>

      <!-- 免责声明 -->
      <div class="disclaimer">
        <el-icon><InfoFilled /></el-icon>
        行情数据来源：Finnhub Finance，仅供学习参考，不构成投资建议。请自行承担投资决策风险。
      </div>
    </template>
    <div v-else-if="assetLoading" class="hero-loading card">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 资产不存在-->
    <div v-else-if="!assetLoading" class="not-found">
      <el-empty description="资产不存在" :image-size="80">
        <el-button @click="$router.push('/market')">返回行情列表</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted, onUnmounted, watch, defineAsyncComponent, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { get } from '@/api/index'
import { getAssetContents } from '@/api/market'
import { createPost } from '@/api/posts'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { useQuoteStream } from '@/composables/useQuoteStream'
import type { AssetQuote } from '@/types/market'
import type { Asset } from '@/types'

const KlineChart = defineAsyncComponent(() => import('@/components/market/KlineChart.vue'))
const IntradayChart = defineAsyncComponent(() => import('@/components/market/IntradayChart.vue'))

// 扩展 Asset 类型以包含行情字段
type AssetDetail = Asset & {
  quote?: AssetQuote
  description?: string
  industry?: string
  exchange?: string
  currency?: string
  logo_url?: string
  finnhub_symbol?: string
}

const ASSET_DETAIL_CACHE_TTL = 5 * 60 * 1000
const assetDetailCache = new Map<string, { data: AssetDetail; fetchedAt: number }>()
const assetDetailRequests = new Map<string, Promise<AssetDetail>>()

const props = defineProps<{ assetId: string }>()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const marketStore = useMarketStore()

const assetId = computed(() => props.assetId || route.params.assetId as string)

// 资产基础信息
const asset = ref<AssetDetail | null>(null)
const assetLoading = ref(false)

// 行情数据
const quote = ref<AssetQuote | null>(null)
const quoteLoading = ref(false)
const quoteError = ref(false)

// 图表类型
const chartType = ref<'kline' | 'intraday'>('kline')
const chartSectionRef = ref<HTMLElement | null>(null)
const shouldRenderCharts = ref(false)
let chartObserver: IntersectionObserver | null = null

// 相关内容
const relatedContents = ref<any[]>([])
const contentsLoading = ref(false)
const contentSort = ref<'new' | 'hot'>('new')
const contentPage = ref(1)
const contentPageSize = ref(10)
const contentTotal = ref(0)

// 快速发帖
const quickPostTitle = ref('')
const quickPostContent = ref('')
const quickPosting = ref(false)

// SSE（lazy connect, 在行情加载完后手动connect）
const quoteStream = useQuoteStream(Number(assetId.value))
const connectSSE = quoteStream.connect
const disconnectSSE = quoteStream.disconnect
let quoteStreamConnectTimer: ReturnType<typeof setTimeout> | null = null
let quoteStreamConnectScheduled = false

// 计算属性
const marketLabel = computed(() => {
  const map: Record<string, string> = {
    SH: 'A股沪市', SZ: 'A股深市', HK: '港股', US: '美股'
  }
  return asset.value?.market ? (map[asset.value.market] || asset.value.market) : '未知'
})

const marketTagType = computed(() => {
  const m = asset.value?.market?.toUpperCase()
  if (m === 'SH' || m === 'SZ') return 'danger'
  if (m === 'HK') return 'warning'
  if (m === 'US') return 'primary'
  return 'info'
})

const changePctNum = computed(() => {
  if (!quote.value?.changePct) return 0
  return parseFloat(String(quote.value.changePct))
})

const priceColor = computed(() => {
  if (changePctNum.value > 0) return 'up'
  if (changePctNum.value < 0) return 'down'
  return 'flat'
})

// 格式化方法
const formatPrice = (val: any) => {
  if (val === null || val === undefined) return '--'
  return parseFloat(String(val)).toFixed(2)
}

const formatChange = (val: any) => {
  if (val === null || val === undefined) return ''
  const num = parseFloat(String(val))
  const sign = num > 0 ? '+' : ''
  return `${sign}${num.toFixed(2)}`
}

const formatChangePct = (val: any) => {
  if (val === null || val === undefined) return ''
  const num = parseFloat(String(val))
  const sign = num > 0 ? '+' : ''
  return `${sign}${num.toFixed(2)}%`
}

const formatVolume = (val: number | null) => {
  if (val === null || val === undefined) return '--'
  if (val >= 1e8) return `${(val / 1e8).toFixed(2)}亿`
  if (val >= 1e4) return `${(val / 1e4).toFixed(2)}万`
  return String(val)
}

const formatQuoteTime = (timeStr: string | null) => {
  if (!timeStr) return '--'
  const d = new Date(timeStr)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${min}`
}

const formatDate = (str: string) => {
  if (!str) return ''
  return str.substring(0, 10)
}

const getCachedAssetDetail = (id: string) => {
  const cached = assetDetailCache.get(id)
  if (!cached) return null
  if (Date.now() - cached.fetchedAt >= ASSET_DETAIL_CACHE_TTL) return null
  return cached.data
}

const fetchAssetDetail = async (id: string, forceRefresh = false) => {
  if (!forceRefresh) {
    const cached = getCachedAssetDetail(id)
    if (cached) return cached
  }

  const inflight = assetDetailRequests.get(id)
  if (inflight) return inflight

  const request = get<AssetDetail>(`/assets/${id}/`)
    .then((data) => {
      assetDetailCache.set(id, { data, fetchedAt: Date.now() })
      return data
    })
    .finally(() => {
      assetDetailRequests.delete(id)
    })

  assetDetailRequests.set(id, request)
  return request
}

const applyAssetData = (data: AssetDetail) => {
  asset.value = data
  document.title = `${data.code} - ${data.name} - 投研社区`

  if (data.quote && !quote.value) {
    quote.value = data.quote
    marketStore.updateQuoteFromStream({ assetId: Number(assetId.value), ...data.quote })
  }
}

const scheduleQuoteStreamConnect = () => {
  if (quoteStreamConnectScheduled) return
  quoteStreamConnectScheduled = true

  const connect = () => {
    quoteStreamConnectTimer = null
    quoteStreamConnectScheduled = false
    connectSSE()
  }

  if ('requestIdleCallback' in window) {
    ;(window as any).requestIdleCallback(connect, { timeout: 1200 })
    return
  }

  quoteStreamConnectTimer = window.setTimeout(connect, 150)
}

// 首屏并发加载：资产详情 + 行情
const loadInitialData = async () => {
  const currentAssetId = String(assetId.value)
  const numericAssetId = Number(currentAssetId)
  const cachedAsset = getCachedAssetDetail(currentAssetId)
  const cachedQuote = marketStore.getCachedQuote(numericAssetId)

  assetLoading.value = true
  quoteLoading.value = !cachedQuote
  quoteError.value = false

  if (cachedAsset) {
    applyAssetData(cachedAsset)
    assetLoading.value = false
  }

  if (cachedQuote) {
    quote.value = cachedQuote
  }

  try {
    const [assetRes, quoteRes] = await Promise.allSettled([
      fetchAssetDetail(currentAssetId),
      marketStore.fetchQuote(numericAssetId)
    ])

    if (assetRes.status === 'fulfilled') {
      applyAssetData(assetRes.value)
    } else if (!cachedAsset) {
      asset.value = null
    }

    // 行情接口结果优先（通常更实时）
    if (quoteRes.status === 'fulfilled' && quoteRes.value) {
      quote.value = quoteRes.value
      quoteError.value = false
      marketStore.updateQuoteFromStream(quoteRes.value)
    } else if (!quote.value) {
      quoteError.value = true
    }

    if (quote.value) {
      scheduleQuoteStreamConnect()
    }
  } catch (e) {
    if (!cachedAsset) {
      asset.value = null
    }
    if (!quote.value) {
      quoteError.value = true
    }
  } finally {
    assetLoading.value = false
    quoteLoading.value = false
  }
}

// 加载行情
const loadQuote = async () => {
  quoteLoading.value = true
  quoteError.value = false
  try {
    const data = await marketStore.fetchQuote(Number(assetId.value), true)
    quote.value = data
    if (data) {
      marketStore.updateQuoteFromStream(data)
      scheduleQuoteStreamConnect()
    } else {
      quoteError.value = true
    }
  } catch (e) {
    quoteError.value = true
    quote.value = null
  } finally {
    quoteLoading.value = false
  }
}

// 加载相关内容
const loadContents = async () => {
  contentsLoading.value = true
  try {
    const res = await getAssetContents(Number(assetId.value), {
      sort: contentSort.value,
      page: contentPage.value,
      pageSize: contentPageSize.value
    })
    relatedContents.value = res.items
    contentTotal.value = res.total
  } catch (e) {
    relatedContents.value = []
  } finally {
    contentsLoading.value = false
  }
}

const changeContentSort = (sort: 'new' | 'hot') => {
  contentSort.value = sort
  contentPage.value = 1
  loadContents()
}

const scheduleLoadContents = () => {
  const loader = () => loadContents()
  if ('requestIdleCallback' in window) {
    ;(window as any).requestIdleCallback(loader, { timeout: 1500 })
  } else {
    window.setTimeout(loader, 250)
  }
}

const initChartObserver = () => {
  if (!chartSectionRef.value || shouldRenderCharts.value) return
  if (typeof IntersectionObserver === 'undefined') {
    shouldRenderCharts.value = true
    return
  }

  chartObserver?.disconnect()
  chartObserver = null

  const rect = chartSectionRef.value.getBoundingClientRect()
  if (rect.top <= window.innerHeight + 60) {
    shouldRenderCharts.value = true
    return
  }

  chartObserver = new IntersectionObserver(
    (entries) => {
      if (entries.some(entry => entry.isIntersecting)) {
        shouldRenderCharts.value = true
        chartObserver?.disconnect()
        chartObserver = null
      }
    },
    { rootMargin: '60px 0px' }
  )
  chartObserver.observe(chartSectionRef.value)
}

// 快速发帖
const submitQuickPost = async () => {
  if (!quickPostTitle.value || !quickPostContent.value || !asset.value) return
  quickPosting.value = true
  try {
    await createPost({
      title: quickPostTitle.value,
      content: quickPostContent.value,
      status: 'PENDING_REVIEW' as any,
      assetIds: [asset.value.id]
    } as any)
    ElMessage.success('发布成功，等待审核')
    quickPostTitle.value = ''
    quickPostContent.value = ''
    loadContents()
  } catch (e) {
    ElMessage.error('发布失败')
  } finally {
    quickPosting.value = false
  }
}

// 监听来自 SSE/store 的行情更新
watch(
  () => marketStore.getCachedQuote(Number(assetId.value)),
  (newQuote) => {
    if (newQuote) {
      quote.value = newQuote
    }
  }
)

watch(
  () => [asset.value?.id, assetLoading.value],
  async ([id, loading]) => {
    if (!id || loading || shouldRenderCharts.value) return
    await nextTick()
    initChartObserver()
  }
)

onMounted(() => {
  loadInitialData()
  scheduleLoadContents()
  nextTick(() => {
    initChartObserver()
  })
})

onUnmounted(() => {
  chartObserver?.disconnect()
  chartObserver = null
  if (quoteStreamConnectTimer) {
    clearTimeout(quoteStreamConnectTimer)
    quoteStreamConnectTimer = null
  }
  quoteStreamConnectScheduled = false
  disconnectSSE()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.asset-detail {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: $market-space-5;
}

.page-header {
  :deep(.el-breadcrumb) {
    font-size: $market-font-caption;
  }
  :deep(.el-breadcrumb__item) {
    color: $market-text-secondary;
  }
}

.card {
  background: $market-bg-soft;
  border: 1px solid $apple-border-light;
  border-radius: $market-radius-lg;
  padding: $market-space-6;
  box-shadow: $market-shadow-sm;
  transition: $transition-all;

  &:hover {
    box-shadow: $market-shadow-md;
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $market-space-4;
}

.card-title {
  font-size: $market-font-h3;
  font-weight: 600;
  color: $market-text-primary;
  margin: 0;
}

// Hero 头部卡片
.hero-card {
  background: $market-bg-panel;
  border-radius: $market-radius-xl;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: $market-shadow-lg;
}

.quote-header-card {
  .asset-title {
    margin-bottom: $market-space-5;
  }
  
  .asset-code-name {
    display: flex;
    align-items: center;
    gap: $market-space-3;
    flex-wrap: wrap;
  }
  
  .asset-code {
    font-size: $market-font-h2;
    font-weight: 700;
    color: $market-text-primary;
    letter-spacing: 0.02em;
  }
  
  .asset-name {
    font-size: $market-font-body;
    color: $market-text-secondary;
    font-weight: 500;
  }
  
  .market-tag, .type-tag {
    font-size: $market-font-mini;
    border-radius: $market-radius-sm;
    padding: 2px 8px;
  }
}

.main-price-row {
  display: flex;
  align-items: baseline;
  gap: $market-space-5;
  margin-bottom: $market-space-4;
  
  .main-price {
    font-size: $market-font-display;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1;
  }
  
  .change-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: $market-font-body;
    font-weight: 600;
  }

  .change-amount {
    font-size: $market-font-h3;
  }

  .change-pct {
    font-size: $market-font-body;
  }
}

.up { color: $market-up; }
.down { color: $market-down; }
.flat { color: $market-neutral; }

.stale-alert {
  margin-bottom: 0.75rem;
  :deep(.el-alert__content) {
    font-size: 0.8rem;
  }
}

.quote-metrics {
  display: flex;
  gap: $market-space-6;
  flex-wrap: wrap;
  padding: $market-space-4 0;
  border-top: 1px solid $apple-border-light;
  border-bottom: 1px solid $apple-border-light;
  margin-bottom: $market-space-4;
  
  .metric-item {
    display: flex;
    flex-direction: column;
    gap: $market-space-2;
    min-width: 80px;
  }
  
  .metric-label {
    font-size: $market-font-mini;
    color: $market-text-tertiary;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  
  .metric-value {
    font-size: $market-font-body;
    font-weight: 600;
    color: $market-text-primary;
    
    &.up { color: $market-up; }
    &.down { color: $market-down; }
  }
}

.quote-footer {
  font-size: $market-font-mini;
  color: $market-text-tertiary;
  
  .data-source {
    font-style: italic;
  }
}

// 图表卡片
.chart-card {
  padding: $market-space-6;
}

.chart-lazy-skeleton {
  min-height: 360px;
  padding-top: $market-space-3;
}

.chart-type-tabs {
  display: flex;
  gap: $market-space-2;
  background: rgba(0, 0, 0, 0.02);
  padding: 4px;
  border-radius: $market-radius-segmented;
}

.chart-type-btn {
  padding: 6px 16px;
  border-radius: $market-radius-segmented-item;
  border: none;
  background: transparent;
  color: $market-text-secondary;
  font-size: $market-font-caption;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: rgba(0, 0, 0, 0.04);
    color: $market-text-primary;
  }

  &.active {
    background: $market-bg-soft;
    color: $market-accent;
    font-weight: 600;
    box-shadow: $market-shadow-sm;
  }
}

// 公司信息
.info-card {
  .card-title {
    margin-bottom: $market-space-4;
  }
}

.company-info {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: $market-space-4;
  margin-bottom: $market-space-4;
  
  .info-row {
    display: flex;
    flex-direction: column;
    gap: $market-space-2;
    padding: $market-space-3;
    background: rgba(0, 0, 0, 0.02);
    border-radius: $market-radius-md;
  }
  
  .info-label {
    font-size: $market-font-mini;
    color: $market-text-tertiary;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  
  .info-value {
    font-size: $market-font-body;
    color: $market-text-primary;
    font-weight: 500;
  }
}

.company-desc {
  font-size: 0.85rem;
  color: #4B5563;
  line-height: 1.7;
  margin: 0;
}

:deep(.desc-collapse) {
  background: transparent;
  border: none;
  
  .el-collapse-item__header {
    background: transparent;
    color: #3B82F6;
    font-size: 0.85rem;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  }
  
  .el-collapse-item__wrap {
    background: transparent;
  }
  
  .el-collapse-item__content {
    background: transparent;
    padding: 12px 0 0;
  }
}

// 相关内容
.contents-card {
  content-visibility: auto;
  contain-intrinsic-size: 520px;

  .card-title {
    font-size: $market-font-h2;
    font-weight: 700;
  }
}

.sort-tabs {
  display: flex;
  gap: $market-space-2;
  background: rgba(0, 0, 0, 0.02);
  padding: 4px;
  border-radius: $market-radius-segmented;
}

.sort-btn {
  padding: 6px 16px;
  border-radius: $market-radius-segmented-item;
  border: none;
  background: transparent;
  color: $market-text-secondary;
  font-size: $market-font-caption;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: rgba(0, 0, 0, 0.04);
    color: $market-text-primary;
  }

  &.active {
    background: $market-bg-soft;
    color: $market-accent;
    font-weight: 600;
    box-shadow: $market-shadow-sm;
  }
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.content-item {
  padding: $market-space-4 0;
  border-bottom: 1px solid $apple-border-light;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: rgba(0, 113, 227, 0.02);
    margin: 0 (-$market-space-6);
    padding: $market-space-4 $market-space-6;
    border-radius: $market-radius-md;
  }
}

.content-item-main {
  .content-title {
    font-size: $market-font-body;
    font-weight: 600;
    color: $market-text-primary;
    margin: 0 0 $market-space-2;
    line-height: 1.5;
  }
  
  .content-excerpt {
    font-size: $market-font-caption;
    color: $market-text-secondary;
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    line-height: 1.5;
  }
}

.content-item-meta {
  display: flex;
  align-items: center;
  gap: $market-space-2;
  margin-top: $market-space-2;
  font-size: $market-font-mini;
  color: $market-text-tertiary;
  
  .author-clickable {
    color: $market-accent;
    cursor: pointer;
    transition: color 0.2s;

    &:hover {
      color: $market-text-primary;
      text-decoration: underline;
    }
  }
  
  .dot { 
    opacity: 0.4; 
  }
  
  .like-count {
    display: flex;
    align-items: center;
    gap: 4px;
    
    svg {
      width: 12px;
      height: 12px;
    }
  }
}

.content-pagination {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

.view-more {
  text-align: center;
  padding-top: $market-space-4;
  
  .view-more-link {
    font-size: $market-font-caption;
    color: $market-accent;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
    
    &:hover {
      color: $market-text-primary;
      text-decoration: underline;
    }
  }
}

// 快速发帖
.quick-post-card {
  content-visibility: auto;
  contain-intrinsic-size: 280px;

  .card-title {
    font-size: $market-font-h2;
    font-weight: 700;
    margin-bottom: $market-space-4;
  }
}

.quick-post-form {
  display: flex;
  flex-direction: column;
  gap: $market-space-4;
  
  .quick-title-input, .quick-content-input {
    :deep(.el-input__wrapper), :deep(.el-textarea__inner) {
      background: $apple-input-bg;
      border: 1px solid $apple-input-border;
      border-radius: $market-radius-input;
      color: $market-text-primary;
      transition: $transition-all;
      
      &:hover {
        border-color: $market-accent;
      }

      &:focus {
        border-color: $market-accent;
        box-shadow: 0 0 0 3px $market-accent-soft;
      }
      
      &::placeholder {
        color: $market-text-tertiary;
      }
    }
  }
}

.quick-post-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;

  :deep(.el-tag) {
    background: $market-accent-soft;
    border-color: $market-accent;
    color: $market-accent;
    font-weight: 500;
    border-radius: $market-radius-sm;
  }
}

// 免责声明
.disclaimer {
  display: flex;
  align-items: center;
  gap: $market-space-2;
  font-size: $market-font-mini;
  color: $market-text-tertiary;
  padding: $market-space-3 $market-space-4;
  background: $market-bg-panel;
  border: 1px solid $apple-border-light;
  border-radius: $market-radius-md;
  font-style: italic;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.loading-wrapper {
  padding: 2rem;
}

.hero-loading {
  min-height: 220px;
}

.not-found {
  padding: 4rem 2rem;
  display: flex;
  justify-content: center;
}

.quote-skeleton {
  padding: 0.5rem 0;
}

.quote-error {
  padding: 1rem 0;
}

.content-loading {
  padding: 0.5rem 0;
}

.content-empty {
  padding: 2rem;
  display: flex;
  justify-content: center;
}
</style>



