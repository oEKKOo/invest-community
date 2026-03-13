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
      <!-- 组合头部信息 -->
      <div class="portfolio-header">
        <div class="header-main">
          <h1 class="portfolio-title">{{ portfoliosStore.currentPortfolio.title }}</h1>
          <p class="portfolio-description">{{ portfoliosStore.currentPortfolio.description }}</p>
          
          <div class="portfolio-meta">
            <el-tag 
              :type="getRiskLevelType(portfoliosStore.currentPortfolio.riskLevel)"
              size="large"
              class="risk-tag"
            >
              {{ portfoliosStore.currentPortfolio.riskLevel }} 风险
            </el-tag>
            
            <div class="portfolio-stats">
              <div class="stat-item">
                <span class="stat-label">收益</span>
                <span class="stat-value" :class="perf ? pnlClass(perf.totalUnrealizedReturn) : ''">
                  {{ perf ? fmtRate(perf.totalUnrealizedReturn) : '--' }}
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">点赞</span>
                <span class="stat-value">{{ portfoliosStore.currentPortfolio.likes }}</span>
              </div>
            </div>
          </div>

          <div class="portfolio-author">
            <el-avatar
              :size="40"
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
              <p class="create-date">创建于：{{ formatDate(portfoliosStore.currentPortfolio.createdAt) }}</p>
            </div>
          </div>
        </div>

        <div class="header-actions">
          <el-button
            type="text"
            :class="{ liked: portfoliosStore.currentPortfolio.isLiked }"
            @click="handleLike"
            class="like-btn"
          >
            <el-icon><Star /></el-icon>
            <span>{{ portfoliosStore.currentPortfolio.isLiked ? '已点赞' : '点赞' }}</span>
          </el-button>
          
          <el-button
            type="primary"
            @click="showShareDialog = true"
          >
            <el-icon><Share /></el-icon>
            分享组合
          </el-button>

          <el-button
            v-if="authStore.isLoggedIn && !isOwner"
            type="danger"
            plain
            @click="openReportPortfolioDialog"
          >
            <el-icon><Warning /></el-icon>
            举报组合
          </el-button>
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
              <span class="col-value" v-if="isOwner">持仓市值</span>
              <span class="col-pnl" v-if="isOwner">持有收益</span>
              <span class="col-rate" v-if="isOwner">收益率</span>
            </div>
            
            <div 
              v-for="(asset, index) in portfoliosStore.currentPortfolio.assets"
              :key="asset.symbol"
              class="table-row table-row--enhanced"
            >
              <!-- 代码 -->
              <span class="col-symbol">
                <div 
                  class="color-indicator"
                  :style="{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }"
                ></div>
                {{ asset.symbol }}
              </span>

              <!-- 名称 -->
              <span class="col-name">{{ asset.name }}</span>

              <!-- 市场 -->
              <span class="col-market">
                <el-tag size="small" class="market-tag-sm" v-if="asset.displayMarket || asset.market">
                  {{ asset.displayMarket || asset.market }}
                </el-tag>
                <span v-else class="no-data">--</span>
              </span>

              <!-- 配置比例 -->
              <span class="col-allocation">
                <span class="alloc-badge">{{ asset.allocation }}%</span>
                <div class="alloc-bar-wrap">
                  <div
                    class="alloc-bar-fill"
                    :style="{ width: Math.min(asset.allocation, 100) + '%', backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }"
                  ></div>
                </div>
              </span>

              <!-- 持仓市值（owner only）-->
              <span class="col-value" v-if="isOwner">
                <template v-if="holdingPerfLoading">
                  <el-skeleton-item variant="text" style="width:60px" />
                </template>
                <template v-else-if="getPerfByAssetId(asset.assetId)?.hasData">
                  <span class="mono-val">{{ fmtMoney(getPerfByAssetId(asset.assetId)?.marketValue) }}</span>
                </template>
                <span v-else class="no-data">--</span>
              </span>

              <!-- 持有收益（owner only）-->
              <span class="col-pnl" v-if="isOwner">
                <template v-if="holdingPerfLoading">
                  <el-skeleton-item variant="text" style="width:60px" />
                </template>
                <template v-else-if="getPerfByAssetId(asset.assetId)?.hasData">
                  <span
                    class="mono-val"
                    :class="pnlClass(getPerfByAssetId(asset.assetId)?.unrealizedPnl)"
                  >
                    {{ fmtPnl(getPerfByAssetId(asset.assetId)?.unrealizedPnl) }}
                  </span>
                </template>
                <span v-else class="no-data">--</span>
              </span>

              <!-- 收益率（owner only）-->
              <span class="col-rate" v-if="isOwner">
                <template v-if="holdingPerfLoading">
                  <el-skeleton-item variant="text" style="width:50px" />
                </template>
                <template v-else-if="getPerfByAssetId(asset.assetId)?.hasData">
                  <span
                    class="mono-val rate-val"
                    :class="pnlClass(getPerfByAssetId(asset.assetId)?.unrealizedReturn)"
                  >
                    {{ fmtRate(getPerfByAssetId(asset.assetId)?.unrealizedReturn) }}
                  </span>
                </template>
                <span v-else class="no-data">--</span>
              </span>
            </div>

            <!-- 合计行（owner only）-->
            <div class="table-row table-row--total" v-if="isOwner && portfolioMarketValue !== null">
              <span class="col-symbol total-label">合计</span>
              <span class="col-name"></span>
              <span class="col-market"></span>
              <span class="col-allocation total-alloc">100%</span>
              <span class="col-value total-value">{{ fmtMoney(portfolioMarketValue) }}</span>
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

      <!-- 组合评论区 -->
      <div class="comments-card">
        <h2 class="section-title">组合讨论</h2>
        <el-empty v-if="!comments.length" description="还没有人发表评论，抢沙发～" />
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
            :rows="3"
            resize="none"
            placeholder="发表你对该组合的看法..."
          />
          <el-button type="primary" size="small" class="comment-submit" @click="handleSubmitComment">
            发布评论
          </el-button>
        </div>
      </div>

      <!-- 更新日志 -->
      <div class="updates-card">
        <h2 class="section-title">组合更新日志</h2>
        <el-empty v-if="!updateLogs.length" description="作者还没有发布任何更新日志" />
        <ul v-else class="update-list">
          <li v-for="u in updateLogs" :key="u.id" class="update-item">
            <div class="update-header">
              <span class="update-title">{{ u.title }}</span>
              <span class="update-time">{{ formatDate(u.createdAt) }}</span>
            </div>
            <div class="update-content">
              {{ u.content }}
            </div>
          </li>
        </ul>
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
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import {
  Star,
  Share,
  Warning
} from '@element-plus/icons-vue'
import ReportDialog from '@/components/ReportDialog.vue'
import dayjs from 'dayjs'
import { getHoldingPerformance } from '../api/holdings'
import type { HoldingPerformanceItem } from '../types'

use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent])

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
      // 如果是本人的组合，同步拉持仓收益（非阻塞）
      fetchHoldingPerf()
      // 组合评论与更新日志
      const [commentRes, updateRes] = await Promise.all([
        getPortfolioComments(portfolioId),
        getPortfolioUpdates(portfolioId)
      ])
      comments.value = commentRes.items
      updateLogs.value = updateRes.items
    } catch (error) {
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

.portfolio-header {
  background: #FFFFFF;
  border: 1px solid $border-default;
  border-radius: $border-radius;
  padding: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1.5rem;
  }
}

.header-main {
  flex: 1;
}

.portfolio-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 0.75rem 0;
  line-height: 1.2;
  letter-spacing: -0.03em;
}

.portfolio-description {
  font-size: 0.9375rem;
  color: $text-secondary;
  line-height: 1.6;
  margin: 0 0 1.5rem 0;
  max-width: 600px;
}

.portfolio-meta {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;

  @media (max-width: 640px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
}

.risk-tag {
  font-weight: 700 !important;
}

.portfolio-stats {
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.6875rem;
  color: $text-muted;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.25rem;
}

.stat-value {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
  color: $text-primary;
  font-family: 'IBM Plex Mono', monospace;

  &.positive {
    color: $success-color;
  }
}

.portfolio-author {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.author-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: $text-primary;
  margin: 0;
}

.create-date {
  font-size: 0.75rem;
  color: $text-muted;
  margin: 0;
  font-family: 'IBM Plex Mono', monospace;
}

.header-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-self: flex-start;

  @media (max-width: 768px) {
    flex-direction: row;
    align-self: stretch;
  }
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
  background: #FFFFFF;
  border: 1px solid $border-default;
  border-radius: $border-radius;
  padding: 1.75rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 1.5rem 0;
  letter-spacing: -0.01em;
}

.chart-container {
  height: 380px;
  margin-bottom: 1.5rem;
}

.pie-chart {
  width: 100%;
  height: 100%;
}

.assets-table {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid $border-subtle;
}

.table-header,
.table-row {
  display: grid;
  grid-template-columns: 120px 1fr 100px;
  align-items: center;
  padding: 0.875rem 1rem;
  font-size: 0.875rem;

  @media (max-width: 640px) {
    grid-template-columns: 80px 1fr 80px;
    padding: 0.75rem;
  }
}

// 增强版（含收益列）
.table-header--enhanced,
.table-row--enhanced,
.table-row--total {
  grid-template-columns: 110px 1fr 70px 120px 110px 110px 90px;

  @media (max-width: 900px) {
    grid-template-columns: 90px 1fr 60px 100px;
  }
}

.table-header {
  background: rgba(15, 23, 42, 0.03);
  font-weight: 600;
  color: $text-muted;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 1px solid $border-subtle;
}

.table-row {
  border-bottom: 1px solid $border-subtle;
  transition: background-color 0.2s ease;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: rgba(124, 58, 237, 0.06);
  }
}

.table-row--total {
  background: rgba(124, 58, 237, 0.06) !important;
  border-top: 1px solid rgba(29, 78, 216, 0.12) !important;
  border-bottom: none !important;
}

.total-label {
  font-weight: 700 !important;
  color: $primary-color !important;
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
  gap: 3px;
  font-weight: 700;
  color: $primary-color;
  font-family: 'IBM Plex Mono', monospace;
}

.alloc-badge {
  font-size: 0.8rem;
}

.alloc-bar-wrap {
  width: 80%;
  height: 3px;
  background: rgba(255,255,255,0.08);
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
  margin-top: 1rem;
  background: #ffffff;
  border: 1px solid $border-default;
  border-radius: $border-radius;
  padding: 1.5rem;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.comment-item {
  padding-bottom: 0.5rem;
  border-bottom: 1px solid $border-subtle;

  &:last-child {
    border-bottom: none;
  }
}

.comment-meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: $text-muted;
  margin-bottom: 0.15rem;
}

.comment-body {
  font-size: 0.85rem;
  color: $text-primary;
}

.comment-editor {
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.comment-submit {
  align-self: flex-end;
}

.update-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.update-item {
  padding-bottom: 0.5rem;
  border-bottom: 1px solid $border-subtle;

  &:last-child {
    border-bottom: none;
  }
}

.update-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  margin-bottom: 0.25rem;
}

.update-title {
  font-weight: 600;
}

.update-time {
  color: $text-muted;
}

.update-content {
  font-size: 0.85rem;
  color: $text-secondary;
}

.stats-card {
  background: #FFFFFF;
  border: 1px solid $border-default;
  border-radius: $border-radius;
  padding: 1.375rem;
}

.card-title {
  font-size: 0.875rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 1rem 0;
  letter-spacing: -0.01em;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8125rem;
  padding: 0.375rem 0;
  border-bottom: 1px solid $border-subtle;

  &:last-child {
    border-bottom: none;
  }
}

.stat-name {
  color: $text-muted;
}

.stat-data {
  font-weight: 600;
  color: $text-primary;
  font-family: 'IBM Plex Mono', monospace;
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






