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
const CHART_COLORS = ['#2563eb', '#7c3aed', '#db2777', '#ea580c', '#16a34a', '#4b5563']

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
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: '0%',
      left: 'center'
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
  animation: fadeIn 0.3s ease-out;
}

.loading-container {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.not-found {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.portfolio-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.portfolio-header {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1.5rem;
  }
}

.header-main {
  flex: 1;
}

.portfolio-title {
  font-size: 2rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0 0 0.75rem 0;
  line-height: 1.2;
}

.portfolio-description {
  font-size: 1rem;
  color: #6b7280;
  line-height: 1.6;
  margin: 0 0 1.5rem 0;
  max-width: 600px;
}

.portfolio-meta {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 1.5rem;

  @media (max-width: 640px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
}

.risk-tag {
  font-weight: bold;
}

.portfolio-stats {
  display: flex;
  gap: 2rem;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.stat-value {
  display: block;
  font-size: 1.25rem;
  font-weight: bold;
  color: #1f2937;

  &.positive {
    color: #059669;
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
  color: #1f2937;
  margin: 0;
}

.create-date {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0;
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6b7280;

  &:hover {
    color: #ef4444;
  }

  &.liked {
    color: #ef4444;
  }
}

.portfolio-content {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 2rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.assets-overview {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 1.25rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0 0 1.5rem 0;
}

.chart-container {
  height: 400px;
  margin-bottom: 2rem;
}

.pie-chart {
  width: 100%;
  height: 100%;
}

.assets-table {
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.table-header,
.table-row {
  display: grid;
  grid-template-columns: 120px 1fr 100px;
  align-items: center;
  padding: 1rem;
  font-size: 0.875rem;

  @media (max-width: 640px) {
    grid-template-columns: 80px 1fr 80px;
    padding: 0.75rem;
  }
}

.table-header {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

.table-row {
  border-bottom: 1px solid #f3f4f6;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: #f9fafb;
  }
}

.col-symbol {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #1f2937;
}

.color-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.col-name {
  color: #6b7280;
}

.col-allocation {
  font-weight: 600;
  color: #2563eb;
  text-align: right;
}

.portfolio-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.stats-card {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-title {
  font-size: 1rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0 0 1rem 0;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}

.stat-name {
  color: #6b7280;
}

.stat-data {
  font-weight: 600;
  color: #1f2937;
}

.share-options {
  text-align: center;

  p {
    margin-bottom: 1rem;
    color: #6b7280;
  }
}

.share-url {
  :deep(.el-input-group__append) {
    background: #2563eb;
    border-color: #2563eb;
    color: white;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>