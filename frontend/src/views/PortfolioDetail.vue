<template>
  <div class="portfolio-detail">
    <div v-if="portfoliosStore.loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="!portfoliosStore.currentPortfolio" class="not-found">
      <el-result
        icon="warning"
        title="投资组合不存在"
        sub-title="该投资组合可能已被删除或您没有权限查看"
      >
        <template #extra>
          <el-button type="primary" @click="$router.back()">返回</el-button>
        </template>
      </el-result>
    </div>

    <div v-else class="portfolio-container">
      <!-- 组合头部信息 (Hero区域) -->
      <div class="portfolio-hero">
        <div class="hero-content">
          <div class="hero-main">
            <!-- 第一重点：组合名称 -->
            <h1 class="portfolio-title">{{ portfoliosStore.currentPortfolio.title }}</h1>
            
            <!-- 第二重点：收益率（突出显示） -->
            <div class="hero-return">
              <div class="return-value" :class="pnlClass(displayTotalReturn)">
                {{ fmtRate(displayTotalReturn) || '--' }}
              </div>
              <div class="return-label">总收益率</div>
            </div>

            <div class="hero-kpis">
              <div class="kpi-item">
                <span class="kpi-label">今日收益率</span>
                <span class="kpi-value" :class="pnlClass(portfoliosStore.currentPortfolio.dailyReturn)">
                  {{ fmtRate(portfoliosStore.currentPortfolio.dailyReturn) || '--' }}
                </span>
              </div>
              <div class="kpi-item">
                <span class="kpi-label">近7日收益率</span>
                <span class="kpi-value" :class="pnlClass(portfoliosStore.currentPortfolio.sevenDayReturn)">
                  {{ fmtRate(portfoliosStore.currentPortfolio.sevenDayReturn) || '--' }}
                </span>
              </div>
              <div class="kpi-item">
                <span class="kpi-label">持仓资产数</span>
                <span class="kpi-value">{{ portfoliosStore.currentPortfolio.assetCount ?? portfoliosStore.currentPortfolio.assets?.length ?? 0 }}</span>
              </div>
              <div class="kpi-item">
                <span class="kpi-label">最近更新时间</span>
                <span class="kpi-value">{{ formatDateTime(portfoliosStore.currentPortfolio.updatedAt || portfoliosStore.currentPortfolio.lastRebalanceAt || portfoliosStore.currentPortfolio.createdAt) }}</span>
              </div>
              <div class="kpi-item">
                <span class="kpi-label">可见性</span>
                <span class="kpi-value">{{ formatVisibility(portfoliosStore.currentPortfolio.visibility, portfoliosStore.currentPortfolio.isPublic) }}</span>
              </div>
            </div>

            <!-- 第三重点：风险等级 -->
            <div class="hero-meta-strip">
              <el-tag 
                :type="getRiskLevelType(portfoliosStore.currentPortfolio.riskLevel)"
                size="default"
                class="risk-tag"
                :class="`risk-${portfoliosStore.currentPortfolio.riskLevel.toLowerCase()}`"
              >
                {{ portfoliosStore.currentPortfolio.riskLevel === 'Low' ? '低风险' : portfoliosStore.currentPortfolio.riskLevel === 'Medium' ? '中等风险' : '高风险' }}
              </el-tag>
              
              <div class="meta-divider"></div>
              
              <div class="meta-item">
                <span class="meta-label">点赞</span>
                <span class="meta-value">{{ portfoliosStore.currentPortfolio.likes }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">收藏</span>
                <span class="meta-value">{{ portfoliosStore.currentPortfolio.favorites || 0 }}</span>
              </div>
            </div>

            <!-- 第四重点：作者与创建时间 -->
            <div class="portfolio-author">
              <el-avatar
                :size="36"
                :src="getAvatarUrl(portfoliosStore.currentPortfolio.id)"
                class="author-clickable"
                @click.stop="$router.push({ name: 'UserProfile', params: { userId: portfoliosStore.currentPortfolio.userId } })"
              >
                {{ portfoliosStore.currentPortfolio.userName[0] }}
              </el-avatar>
              <div
                class="author-info author-clickable"
                @click.stop="$router.push({ name: 'UserProfile', params: { userId: portfoliosStore.currentPortfolio.userId } })"
              >
                <p class="author-name">{{ portfoliosStore.currentPortfolio.userName }}</p>
                <p class="create-date">创建于 {{ formatDate(portfoliosStore.currentPortfolio.createdAt) }}</p>
              </div>
            </div>
          </div>

          <!-- 第五重点：操作按钮（右上角） -->
          <div class="hero-actions">
            <el-button
              type="text"
              :class="{ liked: portfoliosStore.currentPortfolio.isLiked }"
              @click="handleLike"
              class="action-btn like-btn"
            >
              <el-icon><Star /></el-icon>
              <span>{{ portfoliosStore.currentPortfolio.isLiked ? '已点赞' : '点赞' }}</span>
            </el-button>

            <el-button
              type="text"
              :class="{ liked: portfoliosStore.currentPortfolio.isFavorited }"
              @click="handleFavorite"
              class="action-btn like-btn"
            >
              <el-icon><Star /></el-icon>
              <span>{{ portfoliosStore.currentPortfolio.isFavorited ? '已收藏' : '收藏' }}</span>
            </el-button>
            
            <el-button
              type="primary"
              @click="showShareDialog = true"
              class="action-btn"
            >
              <el-icon><Share /></el-icon>
              分享组合
            </el-button>

            <el-button
              v-if="authStore.isLoggedIn && !isOwner"
              type="danger"
              plain
              @click="openReportPortfolioDialog"
              class="action-btn"
            >
              <el-icon><Warning /></el-icon>
              举报组合
            </el-button>
          </div>
        </div>
      </div>

      <div class="assets-overview">
        <div class="section-title-wrap">
          <h2 class="section-title">收益趋势</h2>
          <div class="range-tabs">
            <button
              v-for="r in rangeOptions"
              :key="r.value"
              class="range-tab"
              :class="{ active: trendRange === r.value }"
              @click="changeTrendRange(r.value)"
            >
              {{ r.label }}
            </button>
          </div>
        </div>
        <div class="chart-container trend-chart-wrap">
          <el-skeleton v-if="trendLoading" :rows="4" animated />
          <v-chart
            v-else-if="trendChartOption.series?.[0]?.data?.length"
            class="pie-chart"
            :option="trendChartOption"
            autoresize
          />
          <el-empty v-else description="暂无收益趋势数据" />
        </div>
      </div>

      <!-- 资产配置详情 -->
      <div class="portfolio-content">
        <div class="assets-overview">
          <h2 class="section-title">资产配置</h2>
          
          <!-- 饼图 -->
          <div class="chart-container">
            <v-chart 
              class="pie-chart" 
              :option="pieChartOption"
              v-if="portfoliosStore.currentPortfolio.assets?.length"
            />
          </div>

          <!-- 资产列表（增强版：金额+ 比例 + 收益）-->
          <div class="assets-table">
            <div class="table-header table-header--enhanced">
              <span class="col-symbol">代码</span>
              <span class="col-name">名称</span>
              <span class="col-market">市场</span>
              <span class="col-allocation">配置比例</span>
              <span class="col-value">现价</span>
              <span class="col-pnl">市值</span>
              <span class="col-rate">收益率</span>
            </div>
            
            <div 
              v-for="(asset, index) in detailRows"
              :key="`${asset.code}-${index}`"
              class="table-row table-row--enhanced"
            >
              <!-- 代码 -->
              <span class="col-symbol">
                <div 
                  class="color-indicator"
                  :style="{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }"
                ></div>
                {{ asset.code || asset.symbol || '--' }}
              </span>

              <!-- 名称 -->
              <span class="col-name">{{ asset.name }}</span>

              <!-- 市场 -->
              <span class="col-market">
                <el-tag size="small" class="market-tag-sm" v-if="asset.displayMarket || asset.market">
                  {{ asset.market }}
                </el-tag>
                <span v-else class="no-data">--</span>
              </span>

              <!-- 配置比例 -->
              <span class="col-allocation">
                <span class="alloc-badge">{{ Number(asset.weight ?? asset.allocation ?? 0).toFixed(2) }}%</span>
                <div class="alloc-bar-wrap">
                  <div
                    class="alloc-bar-fill"
                    :style="{ width: Math.min(Number(asset.weight ?? asset.allocation ?? 0), 100) + '%', backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }"
                  ></div>
                </div>
              </span>

              <!-- 持仓市值（owner only）-->
              <span class="col-value">
                <span class="mono-val">{{ asset.price != null ? fmtMoney(asset.price) : '--' }}</span>
              </span>

              <span class="col-pnl">
                <span class="mono-val">{{ asset.marketValue != null ? fmtMoney(asset.marketValue) : '--' }}</span>
              </span>

              <span class="col-rate">
                <span
                  class="mono-val rate-val"
                  :class="pnlClass(asset.returnRate)"
                >
                  {{ fmtRate(asset.returnRate) || '--' }}
                </span>
              </span>
            </div>

            <!-- 合计行（owner only）-->
            <div class="table-row table-row--total" v-if="portfolioMarketValue !== null">
              <span class="col-symbol total-label">合计</span>
              <span class="col-name"></span>
              <span class="col-market"></span>
              <span class="col-allocation total-alloc">100%</span>
              <span class="col-value total-value">--</span>
              <span class="col-pnl">
                <span
                  class="mono-val"
                  :class="pnlClass((portfolioMarketValue ?? 0) - Number(perf?.totalCostValue ?? 0))"
                  v-if="perf"
                >
                  {{ fmtPnl((portfolioMarketValue ?? 0) - Number(perf.totalCostValue)) }}
                </span>
              </span>
              <span class="col-rate">
                <span
                  class="mono-val rate-val"
                  :class="pnlClass(perf?.totalUnrealizedReturn)"
                  v-if="perf"
                >
                  {{ fmtRate(perf.totalUnrealizedReturn) }}
                </span>
              </span>
            </div>
          </div>
        </div>

        <div class="portfolio-sidebar">
          <!-- 组合统计 -->
          <div class="stats-card">
            <h3 class="card-title">组合统计</h3>
            <div class="stats-list">
              <div class="stat-row">
                <span class="stat-name">总配置比例</span>
                <span class="stat-data">{{ totalAllocation }}%</span>
              </div>
              <div class="stat-row">
                <span class="stat-name">资产数量</span>
                <span class="stat-data">{{ portfoliosStore.currentPortfolio.assets.length }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-name">风险等级</span>
                <span class="stat-data">{{ portfoliosStore.currentPortfolio.riskLevel }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-name">可见性</span>
                <span class="stat-data">{{ portfoliosStore.currentPortfolio.isPublic ? '公开' : '私有' }}</span>
              </div>
            </div>
          </div>

          <!-- 我的持仓收益（仅 owner）-->
          <div class="stats-card" v-if="isOwner && !holdingPerfLoading && portfolioMarketValue !== null">
            <h3 class="card-title">持仓收益概览</h3>
            <div class="stats-list">
              <div class="stat-row">
                <span class="stat-name">持仓市值</span>
                <span class="stat-data">{{ fmtMoney(portfolioMarketValue) }}</span>
              </div>
              <div class="stat-row" v-if="perf">
                <span class="stat-name">持仓成本</span>
                <span class="stat-data">{{ fmtMoney(perf.totalCostValue) }}</span>
              </div>
              <div class="stat-row" v-if="perf">
                <span class="stat-name">持有收益</span>
                <span class="stat-data" :class="pnlClass(perf.totalUnrealizedPnl)">
                  {{ fmtPnl(perf.totalUnrealizedPnl) }}
                </span>
              </div>
              <div class="stat-row" v-if="perf">
                <span class="stat-name">收益率</span>
                <span class="stat-data" :class="pnlClass(perf.totalUnrealizedReturn)">
                  {{ fmtRate(perf.totalUnrealizedReturn) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="comments-card">
        <h2 class="section-title">策略说明</h2>
        <div class="strategy-note" v-if="strategyMarkdownHtml" v-html="strategyMarkdownHtml"></div>
        <el-empty v-else description="作者尚未填写策略说明" />
      </div>

      <!-- 组合评论区 -->
      <div class="comments-card">
        <h2 class="section-title">大家怎么看这个组合？</h2>
        <el-empty v-if="!comments.length" description="还没有人分享观点，来聊聊这个组合的思路" />
        <div v-else class="comment-list">
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <div class="comment-main">
              <div class="comment-meta">
                <span class="author">{{ c.authorName }}</span>
                <span class="time">{{ formatTime(c.createdAt) }}</span>
              </div>
              <div class="comment-body">
                <template v-if="c.replyToUsername">
                  <span class="reply-to">@{{ c.replyToUsername }}：</span>
                </template>
                {{ c.body }}
              </div>
            </div>
          </div>
        </div>
        <div v-if="authStore.isLoggedIn" class="comment-editor">
          <el-input
            v-model="newComment"
            type="textarea"
            :rows="4"
            resize="none"
            placeholder="写下你对这套组合的看法…&#10;比如配置逻辑、风险判断、收益预期等"
            class="comment-input"
          />
          <el-button type="primary" size="default" class="comment-submit" @click="handleSubmitComment">
            发布评论
          </el-button>
        </div>
      </div>

      <!-- 更新日志 -->
      <div class="updates-card">
        <h2 class="section-title">组合更新日志</h2>
        <el-empty v-if="!updateLogs.length" description="作者还没有发布任何更新日志" />
        <div v-else class="update-timeline">
          <div v-for="u in updateLogs" :key="u.id" class="timeline-item">
            <div class="timeline-marker"></div>
            <div class="timeline-content">
              <div class="update-time">{{ formatTime(u.createdAt) }}</div>
              <div class="update-text">{{ u.content || u.title }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分享对话框-->
    <el-dialog v-model="showShareDialog" title="分享投资组合" width="400px">
      <div class="share-options">
        <p>复制链接分享给朋友：</p>
        <el-input
          :value="shareUrl"
          readonly
          class="share-url"
        >
          <template #append>
            <el-button @click="copyShareUrl">复制</el-button>
          </template>
        </el-input>
      </div>
    </el-dialog>

    <!-- 举报组合对话框 -->
    <ReportDialog
      v-model="showReportDialog"
      target-type="PORTFOLIO"
      :target-id="reportTargetPortfolioId || 0"
      :target-summary="reportTargetPortfolioSummary"
      @submitted="handleReportSubmitted"
    />
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePortfoliosStore } from '../stores/portfolios'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import {
  Star,
  Share,
  Warning
} from '@element-plus/icons-vue'
import ReportDialog from '@/components/ReportDialog.vue'
import { dayjs } from '@/utils/date'
import { createLazyChartComponent, loadPortfolioDetailChartComponent } from '@/utils/chart-loader'
import { getHoldingPerformance } from '../api/holdings'
import type { HoldingPerformanceItem } from '../types'
import {
  getPortfolioComments,
  getPortfolioUpdates,
  createPortfolioComment,
  getPortfolioReturnsHistory
} from '../api/portfolios'

const VChart = createLazyChartComponent(loadPortfolioDetailChartComponent)

const route = useRoute()
const portfoliosStore = usePortfoliosStore()
const authStore = useAuthStore()

const showShareDialog = ref(false)
const showReportDialog = ref(false)
const reportTargetPortfolioId = ref<number | null>(null)
const reportTargetPortfolioSummary = ref('')
const comments = ref<any[]>([])
const newComment = ref('')
const updateLogs = ref<any[]>([])
const trendRange = ref<'7d' | '30d' | 'all'>('30d')
const trendLoading = ref(false)
const trendItems = ref<any[]>([])
const rangeOptions = [
  { label: '近7日', value: '7d' as const },
  { label: '近30日', value: '30d' as const },
  { label: '全部', value: 'all' as const }
]

// 图表颜色
const CHART_COLORS = ['#3B82F6', '#34D399', '#60A5FA', '#F472B6', '#FBBF24', '#818CF8']

// 是否是本人的组合
const isOwner = computed(() => {
  if (!authStore.isLoggedIn || !portfoliosStore.currentPortfolio) return false
  return authStore.user?.id === portfoliosStore.currentPortfolio.userId
})

// 持仓收益数据（仅组合归属于当前用户时加载）
const holdingPerfMap = ref<Map<number, HoldingPerformanceItem>>(new Map())
const holdingPerfLoading = ref(false)
const perf = ref<any>(null)

const fetchHoldingPerf = async () => {
  if (!isOwner.value) return
  holdingPerfLoading.value = true
  try {
    const data = await getHoldingPerformance()
    perf.value = data
    const map = new Map<number, HoldingPerformanceItem>()
    data.items?.forEach(item => map.set(item.assetId, item))
    holdingPerfMap.value = map
  } catch {
    holdingPerfMap.value = new Map()
  } finally {
    holdingPerfLoading.value = false
  }
}

/** 根据 assetId 查找持仓收益 */
const getPerfByAssetId = (assetId: number | null | undefined): HoldingPerformanceItem | undefined => {
  if (!assetId) return undefined
  return holdingPerfMap.value.get(assetId)
}

// ---- 格式化----
const fmtMoney = (val: string | number | null | undefined): string => {
  if (val === null || val === undefined) return '--';
  const n = Number(val)
  if (isNaN(n)) return '--';
  if (n >= 1e8) return `¥${(n / 1e8).toFixed(2)}亿`
  if (n >= 1e4) return `¥${(n / 1e4).toFixed(2)}万`
  return `¥${n.toFixed(2)}`
}

const fmtPnl = (val: string | number | null | undefined): string => {
  if (val === null || val === undefined) return '--';
  const n = Number(val)
  if (isNaN(n)) return '--';
  const pfx = n >= 0 ? '+' : ''
  if (Math.abs(n) >= 1e8) return `${pfx}${(n / 1e8).toFixed(2)}亿`
  if (Math.abs(n) >= 1e4) return `${pfx}${(n / 1e4).toFixed(2)}万`
  return `${pfx}${n.toFixed(2)}`
}

const fmtRate = (val: string | number | null | undefined): string => {
  if (val === null || val === undefined) return ''
  const n = Number(val)
  if (isNaN(n)) return ''
  return `${n >= 0 ? '+' : ''}${(n * 100).toFixed(2)}%`
}

const pnlClass = (val: string | number | null | undefined): string => {
  if (val === null || val === undefined) return ''
  const n = Number(val)
  if (isNaN(n) || n === 0) return 'pnl-zero'
  return n > 0 ? 'pnl-up' : 'pnl-down'
}

/** 本组合内所有资产的持仓总市值（当用户是 owner 且有持仓数据时可用） */
const portfolioMarketValue = computed(() => {
  if (!isOwner.value || !holdingPerfMap.value.size) return null
  const assets = portfoliosStore.currentPortfolio?.assets ?? []
  let total = 0
  let hasAny = false
  for (const a of assets) {
    const perf = getPerfByAssetId(a.assetId)
    if (perf?.hasData && perf.marketValue) {
      total += Number(perf.marketValue)
      hasAny = true
    }
  }
  return hasAny ? total : null
})

const shareUrl = computed(() => {
  return `${window.location.origin}/portfolios/${route.params.id}`
})

const totalAllocation = computed(() => {
  if (!portfoliosStore.currentPortfolio?.assets) return '0.00'
  const sum = portfoliosStore.currentPortfolio.assets.reduce((acc, asset) => acc + Number(asset.allocation), 0)
  return sum.toFixed(2)
})

const displayTotalReturn = computed(() => {
  const p = portfoliosStore.currentPortfolio
  if (!p) return null
  // 详情页优先使用 owner 的实时持仓收益
  if (isOwner.value && perf.value?.totalUnrealizedReturn !== null && perf.value?.totalUnrealizedReturn !== undefined) {
    const n = Number(perf.value.totalUnrealizedReturn)
    if (!isNaN(n)) return n
  }
  // 后端 totalReturn 可能默认 0，避免覆盖已有 returnsYTD
  const total = Number(p.totalReturn)
  if (!isNaN(total) && total !== 0) return total
  const ytd = Number(p.returnsYTD)
  if (!isNaN(ytd)) return ytd
  if (!isNaN(total)) return total
  return null
})

const detailRows = computed(() => {
  const detail = portfoliosStore.currentPortfolio?.holdingDetails
  if (detail?.length) return detail
  return (portfoliosStore.currentPortfolio?.assets || []).map((a: any) => ({
    assetId: a.assetId ?? null,
    code: a.symbol,
    name: a.name,
    market: a.displayMarket || a.market || '',
    weight: Number(a.allocation || 0),
    price: null,
    marketValue: null,
    returnRate: null
  }))
})

const trendChartOption = computed(() => {
  if (!trendItems.value.length) return {}
  const x = trendItems.value.map(i => i.date)
  const y = trendItems.value.map(i => Number(i.returnRate || 0) * 100)
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        const p = params?.[0]
        if (!p) return ''
        return `${p.axisValue}<br/>累计收益率：${p.value >= 0 ? '+' : ''}${Number(p.value).toFixed(2)}%`
      }
    },
    grid: { top: 24, right: 24, bottom: 40, left: 50 },
    xAxis: { type: 'category', data: x },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}%` }
    },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: y,
      lineStyle: { width: 2.5, color: '#3B82F6' },
      markLine: {
        silent: true,
        symbol: ['none', 'none'],
        data: [{ yAxis: 0 }]
      }
    }]
  }
})

const strategyMarkdownHtml = computed(() => {
  const text = portfoliosStore.currentPortfolio?.strategyNote || portfoliosStore.currentPortfolio?.description || ''
  if (!text.trim()) return ''
  // MVP 阶段先做轻量渲染：换行 + 基础转义，避免引入额外依赖
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  return escaped.replace(/\n/g, '<br/>')
})

const pieChartOption = computed(() => {
  if (!portfoliosStore.currentPortfolio?.assets) return {}

  const assets = portfoliosStore.currentPortfolio.assets

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: '#FFFFFF',
      borderColor: 'rgba(29, 78, 216, 0.25)',
      borderWidth: 1,
      textStyle: { color: '#1F2937', fontFamily: 'IBM Plex Mono', fontSize: 12 },
      formatter: (params: any) => {
        const asset = assets[params.dataIndex]
        const perf = getPerfByAssetId(asset?.assetId)
        let extra = ''
        if (perf?.hasData && perf.marketValue) {
          const mv = fmtMoney(perf.marketValue)
          const pnlVal = Number(perf.unrealizedPnl)
          const pnlStr = fmtPnl(perf.unrealizedPnl)
          const rateStr = fmtRate(perf.unrealizedReturn)
          const color = pnlVal >= 0 ? '#10b981' : '#f43f5e'
          extra = `<div style="margin-top:4px;border-top:1px solid rgba(255,255,255,0.1);padding-top:4px">
            <div>市值：<b>${mv}</b></div>
            <div>持有收益 <b style="color:${color}">${pnlStr} (${rateStr})</b></div>
          </div>`
        }
        return `<div>
          <b>${params.name}</b><br/>
          配置比例: <b>${params.value}%</b>${extra}
        </div>`
      }
    },
    legend: {
      orient: 'horizontal',
      bottom: '0%',
      left: 'center',
      textStyle: { color: '#475569', fontFamily: 'Inter' }
    },
    series: [
      {
        name: '资产配置',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        data: assets.map((asset, index) => ({
          value: asset.allocation,
          name: asset.symbol,
          itemStyle: { color: CHART_COLORS[index % CHART_COLORS.length] }
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0,0,0,0.5)'
          }
        }
      }
    ]
  }
})

const handleLike = async () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }

  if (!portfoliosStore.currentPortfolio) return

  try {
    await portfoliosStore.toggleLike(portfoliosStore.currentPortfolio.id)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleFavorite = async () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  if (!portfoliosStore.currentPortfolio) return
  try {
    await portfoliosStore.toggleFavorite(portfoliosStore.currentPortfolio.id)
  } catch {
    ElMessage.error('操作失败')
  }
}

const copyShareUrl = async () => {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    ElMessage.success('链接已复制')
    showShareDialog.value = false
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const getRiskLevelType = (riskLevel: string) => {
  switch (riskLevel) {
    case 'High': return 'danger'
    case 'Medium': return 'warning'
    case 'Low': return 'success'
    default: return 'info'
  }
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY年MM月DD日')
}

const formatTime = (dateStr: string) => {
  return dayjs(dateStr).format('MM-DD HH:mm')
}

const formatDateTime = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const formatVisibility = (visibility?: string, isPublic?: boolean) => {
  if (visibility === 'FOLLOWERS') return '仅粉丝'
  if (visibility === 'PRIVATE') return '私密'
  return isPublic === false ? '私密' : '公开'
}

const fetchTrend = async () => {
  const portfolioId = Number(route.params.id)
  if (!portfolioId) return
  trendLoading.value = true
  try {
    const res = await getPortfolioReturnsHistory(portfolioId, trendRange.value)
    trendItems.value = res.items || []
  } catch {
    trendItems.value = []
  } finally {
    trendLoading.value = false
  }
}

const changeTrendRange = async (v: '7d' | '30d' | 'all') => {
  if (trendRange.value === v) return
  trendRange.value = v
  await fetchTrend()
}

const getAvatarUrl = (id: number) => {
  return `https://picsum.photos/seed/${id}/40/40`
}

const openReportPortfolioDialog = () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  if (!portfoliosStore.currentPortfolio) return
  reportTargetPortfolioId.value = portfoliosStore.currentPortfolio.id
  reportTargetPortfolioSummary.value = `${portfoliosStore.currentPortfolio.title} - ${portfoliosStore.currentPortfolio.description || '投资组合'}`
  showReportDialog.value = true
}

const handleReportSubmitted = () => {
  // 举报提交成功后的回调
}

onMounted(async () => {
  const portfolioId = Number(route.params.id)
  if (portfolioId) {
    try {
      await portfoliosStore.fetchPortfolio(portfolioId)
      await fetchTrend()
      // 如果是本人的组合，同步拉持仓收益（非阻塞）
      fetchHoldingPerf()
      // 组合评论与更新日志
      try {
        const [commentRes, updateRes] = await Promise.all([
          getPortfolioComments(portfolioId),
          getPortfolioUpdates(portfolioId)
        ])
        // 容错处理：确保数据结构正确
        comments.value = commentRes?.items || commentRes || []
        updateLogs.value = updateRes?.items || updateRes || []
      } catch (commentError) {
        // 评论和更新日志加载失败不影响主页面显示
        console.warn('加载评论或更新日志失败:', commentError)
        comments.value = []
        updateLogs.value = []
      }
    } catch (error) {
      console.error('获取投资组合详情失败:', error)
      ElMessage.error('获取投资组合详情失败')
    }
  }
})

const handleSubmitComment = async () => {
  const body = newComment.value.trim()
  if (!body) return
  const portfolioId = Number(route.params.id)
  if (!portfolioId) return
  try {
    const created = await createPortfolioComment(portfolioId, { body })
    comments.value.push(created)
    newComment.value = ''
    ElMessage.success('评论已发布')
  } catch {
    ElMessage.error('发表评论失败')
  }
}
</script>

<style lang="scss" scoped>
.portfolio-detail {
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.loading-container,
.not-found {
  background: #FFFFFF;
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 2rem;
}

.portfolio-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

// Hero区域
.portfolio-hero {
  background: $bg-card;
  border: 1px solid $border-default;
  border-radius: $portfolio-hero-radius;
  padding: $portfolio-hero-padding;
  position: relative;
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: $portfolio-space-8;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: $portfolio-space-6;
  }
}

.hero-main {
  flex: 1;
}

.portfolio-title {
  font-size: $portfolio-title-size;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 $portfolio-space-6 0;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

// 收益率（第二重点）
.hero-return {
  margin-bottom: $portfolio-space-6;
  padding: $portfolio-space-6 0;
  border-top: 1px solid $border-subtle;
  border-bottom: 1px solid $border-subtle;
}

.hero-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: $portfolio-space-3;
  margin-bottom: $portfolio-space-6;
}

.kpi-item {
  background: rgba(29, 78, 216, 0.04);
  border: 1px solid $border-subtle;
  border-radius: 10px;
  padding: $portfolio-space-3;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi-label {
  font-size: $portfolio-mini;
  color: $text-muted;
}

.kpi-value {
  font-size: $portfolio-body;
  color: $text-primary;
  font-weight: 600;
  font-family: 'IBM Plex Mono', monospace;
}

.return-value {
  font-size: $portfolio-return-size;
  font-weight: 700;
  font-family: 'IBM Plex Mono', monospace;
  line-height: 1.2;
  margin-bottom: $portfolio-space-2;

  &.pnl-up {
    color: $portfolio-return-positive;
  }

  &.pnl-down {
    color: $portfolio-return-negative;
  }

  &.pnl-zero {
    color: $text-muted;
  }
}

.return-label {
  font-size: $portfolio-caption;
  color: $text-muted;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

// 横向指标组（风险/点赞）
.hero-meta-strip {
  display: flex;
  align-items: center;
  gap: $portfolio-space-4;
  margin-bottom: $portfolio-space-6;
  flex-wrap: wrap;
}

.risk-tag {
  font-weight: 600 !important;
  font-size: $portfolio-caption !important;
  padding: 6px 12px !important;
  border-radius: $apple-radius-sm !important;

  &.risk-low {
    background: $portfolio-risk-low-bg !important;
    color: $portfolio-risk-low !important;
    border-color: $portfolio-risk-low !important;
  }

  &.risk-medium {
    background: $portfolio-risk-medium-bg !important;
    color: $portfolio-risk-medium !important;
    border-color: $portfolio-risk-medium !important;
  }

  &.risk-high {
    background: $portfolio-risk-high-bg !important;
    color: $portfolio-risk-high !important;
    border-color: $portfolio-risk-high !important;
  }
}

.meta-divider {
  width: 1px;
  height: 20px;
  background: $border-subtle;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-label {
  font-size: $portfolio-mini;
  color: $text-muted;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.meta-value {
  font-size: $portfolio-body;
  font-weight: 600;
  color: $text-primary;
  font-family: 'IBM Plex Mono', monospace;
}

.portfolio-author {
  display: flex;
  align-items: center;
  gap: $portfolio-space-3;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.author-name {
  font-size: $portfolio-body;
  font-weight: 500;
  color: $text-primary;
  margin: 0;
}

.create-date {
  font-size: $portfolio-caption;
  color: $text-muted;
  margin: 0;
  font-family: 'IBM Plex Mono', monospace;
}

.author-clickable {
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    opacity: 0.8;
  }
}

// 操作按钮（右上角）
.hero-actions {
  display: flex;
  flex-direction: column;
  gap: $portfolio-space-3;
  align-self: flex-start;

  @media (max-width: 768px) {
    flex-direction: row;
    align-self: stretch;
    flex-wrap: wrap;
  }
}

.action-btn {
  white-space: nowrap;
}

.like-btn {
  display: flex !important;
  align-items: center !important;
  gap: 0.5rem !important;
  color: $text-muted !important;
  border-radius: 8px !important;
  padding: 0.375rem 0.75rem !important;
  transition: $transition-all !important;

  &:hover {
    color: $error-color !important;
    background: rgba(239, 68, 68, 0.1) !important;
  }

  &.liked {
    color: $error-color !important;
    background: rgba(239, 68, 68, 0.08) !important;
  }
}

.portfolio-content {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 1.5rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.assets-overview {
  background: $bg-card;
  border: 1px solid $border-default;
  border-radius: $portfolio-hero-radius;
  padding: $portfolio-space-8;
}

.section-title-wrap {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: $portfolio-space-5;
}

.range-tabs {
  display: inline-flex;
  border: 1px solid $border-subtle;
  border-radius: 8px;
  overflow: hidden;
}

.range-tab {
  border: none;
  background: transparent;
  color: $text-secondary;
  padding: 6px 10px;
  cursor: pointer;
  font-size: $portfolio-caption;

  &.active {
    background: $primary-color;
    color: #fff;
  }
}

.trend-chart-wrap {
  height: 320px;
}

.section-title {
  font-size: $portfolio-section-title;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 $portfolio-space-8 0;
  letter-spacing: -0.01em;
}

.chart-container {
  height: 420px;
  margin-bottom: $portfolio-space-8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pie-chart {
  width: 100%;
  height: 100%;
}

.assets-table {
  border-radius: $apple-radius-md;
  overflow: hidden;
  border: 1px solid $border-subtle;
  background: $bg-card;
}

.table-header,
.table-row {
  display: grid;
  grid-template-columns: 120px 1fr 100px;
  align-items: center;
  padding: $portfolio-space-4 $portfolio-space-5;
  font-size: $portfolio-body;

  @media (max-width: 640px) {
    grid-template-columns: 80px 1fr 80px;
    padding: $portfolio-space-3;
  }
}

// 增强版（含收益列）
.table-header--enhanced,
.table-row--enhanced,
.table-row--total {
  grid-template-columns: 110px 1fr 70px 140px 110px 110px 90px;

  @media (max-width: 900px) {
    grid-template-columns: 90px 1fr 60px 100px;
  }
}

.table-header {
  background: rgba(15, 23, 42, 0.02);
  font-weight: 600;
  color: $text-muted;
  font-size: $portfolio-caption;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid $border-subtle;
}

.table-row {
  border-bottom: 1px solid $border-subtle;
  transition: background-color 0.2s ease;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: rgba(29, 78, 216, 0.04);
  }
}

.table-row--total {
  background: rgba(29, 78, 216, 0.05) !important;
  border-top: 2px solid rgba(29, 78, 216, 0.15) !important;
  border-bottom: none !important;
  font-weight: 600 !important;
}

.total-label {
  font-weight: 700 !important;
  color: $primary-color !important;
  font-size: $portfolio-body !important;
}

.total-alloc,
.total-value {
  font-weight: 700 !important;
  color: $text-primary !important;
}

// 合计行的配置比例列：纯文字，不需要进度条布局
.total-alloc {
  flex-direction: row !important;
  align-items: center !important;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.8rem;
  color: $primary-color !important;
}

.col-symbol {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  color: $text-primary;
  font-family: 'IBM Plex Mono', monospace;
}

.color-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.col-name {
  color: $text-secondary;
  font-size: 0.8125rem;
}

.col-market {
  .market-tag-sm {
    font-size: 0.65rem !important;
    padding: 0 5px !important;
    height: 18px !important;
    line-height: 18px !important;
  }
}

.col-allocation {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 600;
  color: $primary-color;
  font-family: 'IBM Plex Mono', monospace;
}

.alloc-badge {
  font-size: $portfolio-body;
  font-weight: 600;
}

.alloc-bar-wrap {
  width: 100%;
  max-width: 120px;
  height: 4px;
  background: rgba(15, 23, 42, 0.06);
  border-radius: 2px;
  overflow: hidden;
}

.alloc-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.4s ease;
}

.col-value,
.col-pnl,
.col-rate {
  text-align: right;
  font-size: 0.8125rem;
}

.mono-val {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.8125rem;
}

.rate-val {
  font-size: 0.75rem;
}

.no-data {
  color: $text-muted;
  font-size: 0.8125rem;
}

.pnl-up   { color: #10b981; }
.pnl-down { color: #f43f5e; }
.pnl-zero { color: $text-muted; }

.portfolio-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.comments-card,
.updates-card {
  margin-top: $portfolio-space-6;
  background: $bg-card;
  border: 1px solid $border-default;
  border-radius: $apple-radius-md;
  padding: $portfolio-space-8;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: $portfolio-space-5;
  margin-bottom: $portfolio-space-6;
}

.comment-item {
  padding-bottom: $portfolio-space-4;
  border-bottom: 1px solid $border-subtle;

  &:last-child {
    border-bottom: none;
  }
}

.comment-meta {
  display: flex;
  gap: $portfolio-space-3;
  font-size: $portfolio-caption;
  color: $text-muted;
  margin-bottom: $portfolio-space-2;
}

.comment-body {
  font-size: $portfolio-body;
  color: $text-primary;
  line-height: 1.6;
}

.strategy-note {
  color: $text-primary;
  line-height: 1.7;

  :deep(p) {
    margin: 0 0 10px;
  }

  :deep(strong) {
    font-weight: 700;
  }
}

.comment-editor {
  margin-top: $portfolio-space-6;
  display: flex;
  flex-direction: column;
  gap: $portfolio-space-4;
}

.comment-input {
  :deep(.el-textarea__inner) {
    border-radius: $apple-input-radius;
    border-color: $border-subtle;
    font-size: $portfolio-body;
    line-height: 1.6;
    padding: $portfolio-space-4;
  }
}

.comment-submit {
  align-self: flex-end;
  border-radius: $apple-input-radius;
  font-weight: 500;
}

.update-timeline {
  position: relative;
  padding-left: $portfolio-space-6;
  
  &::before {
    content: '';
    position: absolute;
    left: 7px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: $border-subtle;
  }
}

.timeline-item {
  position: relative;
  margin-bottom: $portfolio-space-6;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.timeline-marker {
  position: absolute;
  left: -$portfolio-space-6 - 3px;
  top: 4px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: $primary-color;
  border: 2px solid $bg-card;
  z-index: 1;
}

.timeline-content {
  display: flex;
  flex-direction: column;
  gap: $portfolio-space-2;
}

.update-time {
  font-size: $portfolio-caption;
  color: $text-muted;
  font-family: 'IBM Plex Mono', monospace;
}

.update-text {
  font-size: $portfolio-body;
  color: $text-primary;
  line-height: 1.6;
}

.stats-card {
  background: $bg-card;
  border: 1px solid $border-default;
  border-radius: $apple-radius-md;
  padding: $portfolio-space-6;
}

.card-title {
  font-size: $portfolio-body;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 $portfolio-space-5 0;
  letter-spacing: -0.01em;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: $portfolio-space-3;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: $portfolio-caption;
  padding: $portfolio-space-2 0;
  border-bottom: 1px solid rgba(15, 23, 42, 0.04);

  &:last-child {
    border-bottom: none;
  }
}

.stat-name {
  color: $text-muted;
  font-size: $portfolio-caption;
}

.stat-data {
  font-weight: 600;
  color: $text-primary;
  font-family: 'IBM Plex Mono', monospace;
  font-size: $portfolio-body;
}

.share-options {
  text-align: center;

  p {
    margin-bottom: 1rem;
    color: $text-secondary;
    font-size: 0.875rem;
  }
}

.share-url {
  :deep(.el-input-group__append) {
    background: $gradient-primary;
    border-color: $primary-color;
    color: white;
    font-weight: 600;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>






