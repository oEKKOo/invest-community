<template>
  <div class="asset-detail">
    <!-- 面包屑导航-->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/market' }">行情列表</el-breadcrumb-item>
        <el-breadcrumb-item>{{ asset?.name || assetId }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 加载状态-->
    <div v-if="assetLoading" class="loading-wrapper">
      <el-skeleton :rows="8" animated />
    </div>

    <template v-else-if="asset">
      <!-- 区块 1: 标的头部卡片 -->
      <div class="quote-header-card card">
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
      <div class="chart-card card">
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

        <KlineChart
          v-if="chartType === 'kline'"
          :assetId="Number(assetId)"
          :limit="200"
        />
        <IntradayChart
          v-else-if="chartType === 'intraday'"
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
              <span class="author">{{ item.authorName }}</span>
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
          <h3 class="card-title">发表看法</h3>
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
            :rows="3"
            placeholder="分享你对这支股票的看法..."
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { get } from '@/api/index'
import { getAssetQuote, getAssetContents } from '@/api/market'
import { createPost } from '@/api/posts'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { useQuoteStream } from '@/composables/useQuoteStream'
import KlineChart from '@/components/market/KlineChart.vue'
import IntradayChart from '@/components/market/IntradayChart.vue'
import type { AssetQuote } from '@/types/market'
import type { Asset } from '@/types'

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

// 加载资产基础信息
const loadAsset = async () => {
  assetLoading.value = true
  try {
    const data = await get<AssetDetail>(`/assets/${assetId.value}/`)
    asset.value = data
    // 设置页面标题
    document.title = `${data.code} - ${data.name} - 投研社区`
    // 如果资产详情里已有行情数据，直接使用
    if (data.quote) {
      quote.value = data.quote
      // 同步到market store（供 watch 监听）并启动 SSE 实时推送
      marketStore.updateQuoteFromStream({ assetId: Number(assetId.value), ...data.quote })
      connectSSE()
    } else {
      loadQuote()
    }
  } catch (e) {
    asset.value = null
  } finally {
    assetLoading.value = false
  }
}

// 加载行情
const loadQuote = async () => {
  quoteLoading.value = true
  quoteError.value = false
  try {
    const data = await getAssetQuote(Number(assetId.value))
    quote.value = data
    marketStore.updateQuoteFromStream(data)
    // 启动 SSE 实时推送
    connectSSE()
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

onMounted(() => {
  loadAsset()
  loadContents()
})

onUnmounted(() => {
  disconnectSSE()
})
</script>

<style lang="scss" scoped>
.asset-detail {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.page-header {
  :deep(.el-breadcrumb) {
    font-size: 0.85rem;
  }
  :deep(.el-breadcrumb__item) {
    color: #6B7A99;
  }
}

.card {
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 14px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1F2937;
  margin: 0;
}

// 头部卡片
.quote-header-card {
  .asset-title {
    margin-bottom: 1rem;
  }
  
  .asset-code-name {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }
  
  .asset-code {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1F2937;
    letter-spacing: 0.02em;
  }
  
  .asset-name {
    font-size: 1rem;
    color: #6B7280;
    font-weight: 500;
  }
  
  .market-tag, .type-tag {
    font-size: 0.7rem;
  }
}

.main-price-row {
  display: flex;
  align-items: baseline;
  gap: 1.25rem;
  margin-bottom: 0.75rem;
  
  .main-price {
    font-size: 2.25rem;
    font-weight: 700;
    letter-spacing: -0.02em;
  }
  
  .change-info {
    display: flex;
    gap: 0.5rem;
    font-size: 1rem;
    font-weight: 600;
  }
}

.up { color: #f56c6c; }
.down { color: #67c23a; }
.flat { color: #909399; }

.stale-alert {
  margin-bottom: 0.75rem;
  :deep(.el-alert__content) {
    font-size: 0.8rem;
  }
}

.quote-metrics {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  padding: 0.75rem 0;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  margin-bottom: 0.75rem;
  
  .metric-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .metric-label {
    font-size: 0.7rem;
    color: #6B7280;
  }
  
  .metric-value {
    font-size: 0.9rem;
    font-weight: 600;
    color: #1F2937;
    
    &.up { color: #f56c6c; }
    &.down { color: #67c23a; }
  }
}

.quote-footer {
  font-size: 0.7rem;
  color: #6B7280;
  
  .data-source {
    font-style: italic;
  }
}

// 图表卡片
.chart-type-tabs {
  display: flex;
  gap: 4px;
}

.chart-type-btn {
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: transparent;
  color: #6B7280;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: rgba(0, 0, 0, 0.04);
    color: #374151;
  }

  &.active {
    background: rgba(29, 78, 216, 0.12);
    border-color: rgba(29, 78, 216, 0.25);
    color: #3B82F6;
    font-weight: 600;
  }
}

// 公司信息
.company-info {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  
  .info-row {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .info-label {
    font-size: 0.7rem;
    color: #6B7280;
  }
  
  .info-value {
    font-size: 0.875rem;
    color: #374151;
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
.sort-tabs {
  display: flex;
  gap: 4px;
}

.sort-btn {
  padding: 3px 10px;
  border-radius: 5px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: transparent;
  color: #6B7280;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;

  &.active {
    background: rgba(29, 78, 216, 0.10);
    border-color: rgba(29, 78, 216, 0.18);
    color: #3B82F6;
  }
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.content-item {
  padding: 1rem 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: background 0.2s;
  
  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: #F9FAFB;
    margin: 0 -1.5rem;
    padding: 1rem 1.5rem;
    border-radius: 8px;
  }
}

.content-item-main {
  .content-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #1F2937;
    margin: 0 0 4px;
    line-height: 1.4;
  }
  
  .content-excerpt {
    font-size: 0.8rem;
    color: #6B7280;
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.content-item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  font-size: 0.75rem;
  color: #9CA3AF;
  
  .dot { opacity: 0.5; }
  
  .like-count {
    display: flex;
    align-items: center;
    gap: 2px;
    
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
  padding-top: 0.75rem;
  
  .view-more-link {
    font-size: 0.85rem;
    color: #3B82F6;
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
}

// 快速发帖
.quick-post-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  
  .quick-title-input, .quick-content-input {
    :deep(.el-input__wrapper), :deep(.el-textarea__inner) {
      background: #FFFFFF;
      border-color: rgba(0, 0, 0, 0.1);
      color: #1F2937;
      
      &::placeholder {
        color: #9CA3AF;
      }
    }
  }
}

.quick-post-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

// 免责声明
.disclaimer {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #6B7280;
  padding: 0.75rem 1rem;
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 8px;
  font-style: italic;
}

.loading-wrapper {
  padding: 2rem;
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



