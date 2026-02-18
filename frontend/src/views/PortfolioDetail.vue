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
                <span class="stat-label">年化收益</span>
                <span class="stat-value positive">+{{ portfoliosStore.currentPortfolio.returnsYTD }}%</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">点赞数</span>
                <span class="stat-value">{{ portfoliosStore.currentPortfolio.likes }}</span>
              </div>
            </div>
          </div>

          <div class="portfolio-author">
            <el-avatar :size="40" :src="getAvatarUrl(portfoliosStore.currentPortfolio.id)">
              {{ portfoliosStore.currentPortfolio.userName[0] }}
            </el-avatar>
            <div class="author-info">
              <p class="author-name">{{ portfoliosStore.currentPortfolio.userName }}</p>
              <p class="create-date">创建于 {{ formatDate(portfoliosStore.currentPortfolio.createdAt) }}</p>
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

          <!-- 资产列表 -->
          <div class="assets-table">
            <div class="table-header">
              <span class="col-symbol">代码</span>
              <span class="col-name">名称</span>
              <span class="col-allocation">配置比例</span>
            </div>
            
            <div 
              v-for="(asset, index) in portfoliosStore.currentPortfolio.assets"
              :key="asset.symbol"
              class="table-row"
            >
              <span class="col-symbol">
                <div 
                  class="color-indicator"
                  :style="{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }"
                ></div>
                {{ asset.symbol }}
              </span>
              <span class="col-name">{{ asset.name }}</span>
              <span class="col-allocation">{{ asset.allocation }}%</span>
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
        </div>
      </div>
    </div>

    <!-- 分享对话框 -->
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
  Share
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent])

const route = useRoute()
const portfoliosStore = usePortfoliosStore()
const authStore = useAuthStore()

const showShareDialog = ref(false)

// 图表颜色
const CHART_COLORS = ['#A78BFA', '#34D399', '#60A5FA', '#F472B6', '#FBBF24', '#818CF8']

const shareUrl = computed(() => {
  return `${window.location.origin}/portfolios/${route.params.id}`
})

const totalAllocation = computed(() => {
  if (!portfoliosStore.currentPortfolio?.assets) return 0
  return portfoliosStore.currentPortfolio.assets.reduce((sum, asset) => sum + asset.allocation, 0)
})

const pieChartOption = computed(() => {
  if (!portfoliosStore.currentPortfolio?.assets) return {}

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% ({d}%)',
      backgroundColor: 'rgba(20, 27, 45, 0.95)',
      borderColor: 'rgba(124, 58, 237, 0.4)',
      borderWidth: 1,
      textStyle: {
        color: '#F0F4FF',
        fontFamily: 'IBM Plex Mono'
      }
    },
    legend: {
      orient: 'horizontal',
      bottom: '0%',
      left: 'center',
      textStyle: {
        color: '#A0AABF',
        fontFamily: 'IBM Plex Sans'
      }
    },
    series: [
      {
        name: '资产配置',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        data: portfoliosStore.currentPortfolio.assets.map((asset, index) => ({
          value: asset.allocation,
          name: asset.symbol,
          itemStyle: {
            color: CHART_COLORS[index % CHART_COLORS.length]
          }
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
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

const getAvatarUrl = (id: number) => {
  return `https://picsum.photos/seed/${id}/40/40`
}

onMounted(async () => {
  const portfolioId = Number(route.params.id)
  if (portfolioId) {
    try {
      await portfoliosStore.fetchPortfolio(portfolioId)
    } catch (error) {
      ElMessage.error('获取投资组合详情失败')
    }
  }
})
</script>

<style lang="scss" scoped>
.portfolio-detail {
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.loading-container,
.not-found {
  background: linear-gradient(145deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
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
  background: linear-gradient(145deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
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
  background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
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

.table-header {
  background: rgba(255, 255, 255, 0.04);
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

.col-allocation {
  font-weight: 700;
  color: $primary-light;
  text-align: right;
  font-family: 'IBM Plex Mono', monospace;
}

.portfolio-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.stats-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
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