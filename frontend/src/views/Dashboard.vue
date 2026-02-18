<template>
  <div class="dashboard">
    <!-- Hero Section / Market Overview -->
    <div class="hero-section">
      <div class="market-overview">
        <div class="market-header">
          <div>
            <h2 class="market-title">市场情绪</h2>
            <p class="market-subtitle">S&P 500 指数概览</p>
          </div>
          <div class="market-performance">
            <span class="performance-value">+2.4%</span>
            <el-icon class="trend-icon"><TrendCharts /></el-icon>
          </div>
        </div>
        <div class="chart-container">
          <v-chart 
            class="chart" 
            :option="chartOption" 
            v-if="dashboardStore.dashboardData?.marketSeries"
          />
        </div>
      </div>
      
      <div class="cta-card">
        <div>
          <h3 class="cta-title">构建你的投资组合</h3>
          <p class="cta-subtitle">分享你的投资策略，与社区一起成长</p>
        </div>
        <el-button 
          type="primary" 
          size="large" 
          class="cta-button"
          @click="$router.push('/portfolios')"
        >
          创建投资组合
        </el-button>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="content-grid">
      <!-- Trending Discussions -->
      <section class="trending-section">
        <div class="section-header">
          <h2 class="section-title">热门讨论</h2>
          <el-button 
            type="text" 
            @click="$router.push('/community')"
            class="view-all-btn"
          >
            查看全部
          </el-button>
        </div>
        
        <div class="posts-list" v-if="dashboardStore.dashboardData?.trendingPosts">
          <div 
            v-for="post in dashboardStore.dashboardData.trendingPosts" 
            :key="post.id"
            class="post-card"
            @click="$router.push(`/posts/${post.id}`)"
          >
            <div class="post-content">
              <div class="post-meta">
                <el-tag size="small" class="post-tag">
                  {{ post.tags?.[0] || 'Discussion' }}
                </el-tag>
                <span class="post-date">{{ formatDate(post.createdAt) }}</span>
              </div>
              <h3 class="post-title">{{ post.title }}</h3>
              <p class="post-excerpt">{{ post.content }}</p>
              <div class="post-stats">
                <span class="stat-item">
                  <el-icon><Star /></el-icon>
                  {{ post.likes }}
                </span>
                <span class="stat-item">
                  <el-icon><ChatLineRound /></el-icon>
                  {{ post.comments }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="loading-placeholder">
          <el-skeleton :rows="3" animated />
        </div>
      </section>

      <!-- Top Portfolios Sidebar -->
      <aside class="sidebar-section">
        <h2 class="section-title">顶级投资组合</h2>
        
        <div class="portfolios-list" v-if="dashboardStore.dashboardData?.topPortfolios">
          <div 
            v-for="portfolio in dashboardStore.dashboardData.topPortfolios" 
            :key="portfolio.id"
            class="portfolio-card"
            @click="$router.push(`/portfolios/${portfolio.id}`)"
          >
            <div class="portfolio-header">
              <h4 class="portfolio-title">{{ portfolio.title }}</h4>
              <span class="portfolio-return positive">
                +{{ portfolio.returnsYTD }}%
              </span>
            </div>
            <div class="portfolio-author">
              <el-avatar :size="24" :src="getAvatarUrl(portfolio.id)">
                {{ portfolio.userName[0] }}
              </el-avatar>
              <span class="author-name">by {{ portfolio.userName }}</span>
            </div>
          </div>
          
          <div class="portfolio-footer">
            <el-button 
              type="text" 
              @click="$router.push('/portfolios')"
              class="browse-btn"
            >
              浏览排行榜
            </el-button>
          </div>
        </div>

        <div v-else class="loading-placeholder">
          <el-skeleton :rows="2" animated />
        </div>

        <!-- Community Stats -->
        <div class="stats-card">
          <p class="stats-label">社区统计</p>
          <div class="stats-grid">
            <div class="stat-item">
              <h4 class="stat-value">
                {{ dashboardStore.dashboardData?.communityStats?.activeInvestorsCount || '12.4k' }}
              </h4>
              <p class="stat-label">活跃投资者</p>
            </div>
            <div class="stat-item">
              <h4 class="stat-value">
                {{ dashboardStore.dashboardData?.communityStats?.strategiesSharedCount || '342' }}
              </h4>
              <p class="stat-label">策略分享</p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { onMounted, computed } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import {
  TrendCharts,
  Star,
  ChatLineRound
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const dashboardStore = useDashboardStore()

// Chart configuration
const chartOption = computed(() => {
  if (!dashboardStore.dashboardData?.marketSeries) return {}
  
  return {
    grid: {
      top: 20,
      right: 20,
      bottom: 20,
      left: 20
    },
    xAxis: {
      type: 'category',
      data: dashboardStore.dashboardData.marketSeries.map(item => item.name),
      show: false
    },
    yAxis: {
      type: 'value',
      show: false
    },
    series: [
      {
        data: dashboardStore.dashboardData.marketSeries.map(item => item.value),
        type: 'line',
        smooth: true,
        lineStyle: {
          color: '#A78BFA',
          width: 2.5
        },
        symbol: 'none',
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(124, 58, 237, 0.35)' },
              { offset: 1, color: 'rgba(124, 58, 237, 0)' }
            ]
          }
        }
      }
    ],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(20, 27, 45, 0.95)',
      borderColor: 'rgba(124, 58, 237, 0.4)',
      borderWidth: 1,
      textStyle: {
        color: '#F0F4FF',
        fontFamily: 'IBM Plex Mono'
      }
    }
  }
})

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD')
}

const getAvatarUrl = (id: number) => {
  return `https://picsum.photos/seed/${id}/40/40`
}

onMounted(() => {
  dashboardStore.fetchDashboardData()
})
</script>

<style lang="scss" scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

// ============================================
// Hero Section
// ============================================
.hero-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.25rem;
  margin-bottom: 2rem;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}

.market-overview {
  background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
  border: 1px solid $border-default;
  border-radius: $border-radius-lg;
  padding: 1.5rem;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -60px;
    right: -60px;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, rgba(124, 58, 237, 0.12) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
  }
}

.market-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.25rem;
  position: relative;
  z-index: 1;
}

.market-title {
  font-size: 1rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 0.25rem 0;
  letter-spacing: -0.01em;
}

.market-subtitle {
  font-size: 0.8125rem;
  color: $text-muted;
  margin: 0;
}

.market-performance {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: $success-color;
  font-weight: 700;
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.25);
  border-radius: 8px;
  padding: 0.375rem 0.75rem;
}

.performance-value {
  font-size: 1rem;
  font-family: 'IBM Plex Mono', monospace;
}

.trend-icon {
  font-size: 1.125rem;
}

.chart-container {
  height: 200px;
  position: relative;
  z-index: 1;
}

.chart {
  width: 100%;
  height: 100%;
}

.cta-card {
  background: $gradient-primary;
  border-radius: $border-radius-lg;
  padding: 1.5rem;
  color: white;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: $shadow-purple;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -30px;
    right: -30px;
    width: 150px;
    height: 150px;
    background: rgba(255, 255, 255, 0.07);
    border-radius: 50%;
    pointer-events: none;
  }

  &::after {
    content: '';
    position: absolute;
    bottom: -40px;
    left: -20px;
    width: 120px;
    height: 120px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 50%;
    pointer-events: none;
  }
}

.cta-title {
  font-size: 1.1875rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
  position: relative;
  z-index: 1;
}

.cta-subtitle {
  font-size: 0.8125rem;
  opacity: 0.85;
  margin: 0 0 1.5rem 0;
  line-height: 1.5;
  position: relative;
  z-index: 1;
}

.cta-button {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  position: relative;
  z-index: 1;
  
  &:hover {
    background: rgba(255, 255, 255, 0.25) !important;
    border-color: rgba(255, 255, 255, 0.5) !important;
  }
}

// ============================================
// Content Grid
// ============================================
.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-title {
  font-size: 1.0625rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0;
  letter-spacing: -0.01em;
}

.view-all-btn {
  color: $primary-light !important;
  font-weight: 600 !important;
  font-size: 0.8125rem !important;

  &:hover {
    color: $primary-color !important;
  }
}

// ============================================
// Posts List
// ============================================
.posts-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.post-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 1.125rem 1.25rem;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    border-color: rgba(124, 58, 237, 0.3);
    background: linear-gradient(145deg, rgba(124, 58, 237, 0.07) 0%, rgba(255,255,255,0.02) 100%);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    transform: translateY(-2px);
  }
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.625rem;
}

.post-tag {
  font-size: 0.6875rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
}

.post-date {
  font-size: 0.75rem;
  color: $text-muted;
  font-family: 'IBM Plex Mono', monospace;
}

.post-title {
  font-size: 0.9375rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
  letter-spacing: -0.01em;
  
  &:hover {
    color: $primary-light;
  }
}

.post-excerpt {
  font-size: 0.8125rem;
  color: $text-secondary;
  line-height: 1.6;
  margin: 0 0 0.875rem 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.post-stats {
  display: flex;
  gap: 1.25rem;
  padding-top: 0.625rem;
  border-top: 1px solid $border-subtle;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  color: $text-muted;
  transition: $transition-colors;
  cursor: pointer;

  &:hover {
    color: $primary-light;
  }
}

// ============================================
// Sidebar Section
// ============================================
.sidebar-section {
  .section-title {
    margin-bottom: 1rem;
  }
}

.portfolios-list {
  background: linear-gradient(145deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  overflow: hidden;
  margin-bottom: 1.25rem;
}

.portfolio-card {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid $border-subtle;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    background: rgba(124, 58, 237, 0.07);
  }

  &:last-child {
    border-bottom: none;
  }
}

.portfolio-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.portfolio-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: $text-primary;
  margin: 0;
  flex: 1;
  padding-right: 0.75rem;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  line-height: 1.35;
}

.portfolio-return {
  font-size: 0.6875rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  font-family: 'IBM Plex Mono', monospace;
  flex-shrink: 0;

  &.positive {
    background: rgba(34, 197, 94, 0.15);
    color: #4ADE80;
    border: 1px solid rgba(34, 197, 94, 0.25);
  }
}

.portfolio-author {
  display: flex;
  align-items: center;
  gap: 0.5rem;

  :deep(.el-avatar) {
    border: 1.5px solid $border-subtle !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
  }
}

.author-name {
  font-size: 0.75rem;
  color: $text-muted;
}

.portfolio-footer {
  padding: 0.75rem 1rem;
  text-align: center;
  border-top: 1px solid $border-subtle;
}

.browse-btn {
  font-size: 0.8125rem !important;
  font-weight: 600 !important;
  color: $text-muted !important;

  &:hover {
    color: $primary-light !important;
  }
}

.stats-card {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(124, 58, 237, 0.15) 100%);
  border: 1px solid rgba(124, 58, 237, 0.3);
  border-radius: $border-radius;
  padding: 1.25rem;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -20px;
    right: -20px;
    width: 100px;
    height: 100px;
    background: rgba(124, 58, 237, 0.15);
    border-radius: 50%;
    pointer-events: none;
  }

  .stats-label {
    font-size: 0.6875rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: $primary-light;
    margin: 0 0 1rem 0;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    position: relative;
    z-index: 1;
  }

  .stat-value {
    font-size: 1.375rem;
    font-weight: 700;
    color: $text-primary;
    margin: 0 0 0.25rem 0;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: -0.02em;
  }

  .stat-label {
    font-size: 0.75rem;
    color: $text-muted;
    margin: 0;
  }
}

.loading-placeholder {
  background: linear-gradient(145deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 1.5rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>