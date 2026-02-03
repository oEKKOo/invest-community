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
          color: '#2563eb',
          width: 3
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
              { offset: 0, color: 'rgba(37, 99, 235, 0.2)' },
              { offset: 1, color: 'rgba(37, 99, 235, 0)' }
            ]
          }
        }
      }
    ],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      textStyle: {
        color: '#fff'
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
  animation: fadeIn 0.3s ease-out;
}

.hero-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}

.market-overview {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #f3f4f6;
}

.market-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.market-title {
  font-size: 1.125rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
}

.market-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}

.market-performance {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #059669;
  font-weight: bold;
}

.performance-value {
  font-size: 1.125rem;
}

.trend-icon {
  font-size: 1.25rem;
}

.chart-container {
  height: 200px;
}

.chart {
  width: 100%;
  height: 100%;
}

.cta-card {
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  border-radius: 1rem;
  padding: 1.5rem;
  color: white;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 10px 25px rgba(37, 99, 235, 0.2);
}

.cta-title {
  font-size: 1.25rem;
  font-weight: bold;
  margin: 0 0 0.5rem 0;
}

.cta-subtitle {
  font-size: 0.875rem;
  opacity: 0.9;
  margin: 0 0 1rem 0;
}

.cta-button {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.4);
  }
}

.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}

.trending-section {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .section-title {
    font-size: 1.25rem;
    font-weight: bold;
    color: #1f2937;
    margin: 0;
  }

  .view-all-btn {
    color: #2563eb;
    font-weight: 600;
  }
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.post-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.25rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s ease-in-out;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.post-tag {
  font-size: 0.75rem;
  font-weight: bold;
  text-transform: uppercase;
}

.post-date {
  font-size: 0.75rem;
  color: #6b7280;
}

.post-title {
  font-size: 1.125rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
  
  &:hover {
    color: #2563eb;
  }
}

.post-excerpt {
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
  margin: 0 0 1rem 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.post-stats {
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #6b7280;
  transition: color 0.2s ease-in-out;

  &:hover {
    color: #ef4444;
  }
}

.sidebar-section {
  .section-title {
    font-size: 1.25rem;
    font-weight: bold;
    color: #1f2937;
    margin: 0 0 1rem 0;
  }
}

.portfolios-list {
  background: white;
  border-radius: 0.75rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.portfolio-card {
  padding: 1rem;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: background-color 0.2s ease-in-out;

  &:hover {
    background-color: #f9fafb;
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
  font-size: 0.875rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0;
  flex: 1;
  padding-right: 1rem;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.portfolio-return {
  font-size: 0.75rem;
  font-weight: bold;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;

  &.positive {
    background: #dcfce7;
    color: #166534;
  }
}

.portfolio-author {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.author-name {
  font-size: 0.75rem;
  color: #6b7280;
}

.portfolio-footer {
  padding: 1rem;
  background: #f9fafb;
  text-align: center;
}

.browse-btn {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;

  &:hover {
    color: #2563eb;
  }
}

.stats-card {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 1rem;
  padding: 1.5rem;
  color: white;
  box-shadow: 0 10px 25px rgba(99, 102, 241, 0.2);

  .stats-label {
    font-size: 0.75rem;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.8;
    margin: 0 0 1rem 0;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: bold;
    margin: 0 0 0.25rem 0;
  }

  .stat-label {
    font-size: 0.75rem;
    opacity: 0.7;
    margin: 0;
  }
}

.loading-placeholder {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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