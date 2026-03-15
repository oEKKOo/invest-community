<template>
  <div class="dashboard">

    <!-- ===== 免责声明===== -->
    <div class="disclaimer-bar">
      <el-icon><InfoFilled /></el-icon>
      <span>行情数据来自 Finnhub Finance，仅供学习参考，不构成投资建议。</span>
    </div>

    <!-- ============================================================ -->
    <!-- 第一层：市场总览                                              -->
    <!-- ============================================================ -->
    <section class="market-section">
      <div class="market-section-header">
        <div class="market-title-block">
          <h2 class="market-main-title">市场总览</h2>
          <span class="market-subtitle">实时行情 · 数据60s 刷新</span>
        </div>
        <div class="market-controls">
          <div class="rank-type-btns">
            <button
              v-for="rt in rankTypes"
              :key="rt.key"
              class="rank-type-btn"
              :class="{ active: activeRankType === rt.key }"
              @click="switchRankType(rt.key)"
            >{{ rt.label }}</button>
          </div>
          <router-link to="/market/rankings" class="full-ranking-link">完整榜单 </router-link>
        </div>
      </div>

      <div class="market-body">
        <!-- 左：行情榜单卡片 (4项精选) -->
        <div class="rankings-panel">
          <div v-if="marketLoading" class="loading-grid">
            <div v-for="n in 4" :key="n" class="skeleton-card">
              <el-skeleton animated :rows="2" />
            </div>
          </div>
          <div v-else class="rankings-grid">
            <div
              v-for="(item, idx) in displayedRankings"
              :key="item.assetId"
              class="rank-card"
              @click="$router.push(`/assets/${item.assetId}`)"
            >
              <div class="rank-card-top">
                <span class="rank-num">#{{ idx + 1 }}</span>
                <div class="rank-tags">
                  <el-tag size="small" class="market-tag">{{ formatMarket(item.market) }}</el-tag>
                </div>
              </div>
              <div class="rank-card-middle">
                <span class="rank-code">{{ item.code }}</span>
                <span class="rank-name">{{ item.name }}</span>
              </div>
              <div class="rank-card-bottom">
                <span class="rank-price">
                  {{ item.price != null ? formatPrice(item.price) : '--' }}
                </span>
                <span class="rank-pct" :class="getChangeClass(item.changePct)">
                  {{ formatChangePct(item.changePct) }}
                </span>
              </div>
            </div>
            <div v-if="!marketLoading && displayedRankings.length === 0" class="rankings-empty">
              <el-icon :size="32"><DataLine /></el-icon>
              <p>暂无行情数据</p>
              <span>请先在后台同步市场数据</span>
            </div>
          </div>
        </div>

        <!-- 右：走势图-->
        <div class="chart-panel">
          <div class="chart-panel-header">
            <span class="chart-panel-title">Market Trend</span>
            <div class="chart-tab-group">
              <button
                v-for="tab in chartTabs"
                :key="tab.key"
                class="chart-tab-btn"
                :class="{ active: activeChartTab === tab.key }"
                @click="activeChartTab = tab.key"
              >{{ tab.label }}</button>
            </div>
          </div>
          <div class="chart-area">
            <v-chart
              v-if="dashboardStore.dashboardData?.marketSeries?.length"
              class="echarts-chart"
              :option="chartOption"
              autoresize
            />
            <div v-else class="chart-skeleton">
              <el-skeleton :rows="4" animated />
            </div>
          </div>
          <div class="chart-data-source">
            数据来源：Finnhub · S&P 500 指数概览
          </div>
        </div>
      </div>
    </section>

    <!-- ============================================================ -->
    <!-- 第二层+ 第三/四层：主内容(信息+ 侧边栏)            -->
    <!-- ============================================================ -->
    <div class="main-content-grid">

      <!-- ===== 左主列：信息===== -->
      <section class="feed-section">
        <div class="feed-header">
          <div class="feed-segmented-control">
            <button
              v-for="tab in feedTabs"
              :key="tab.name"
              :class="['feed-segmented-item', { active: activeFeedTab === tab.name, disabled: tab.disabled }]"
              :disabled="tab.disabled"
              @click="!tab.disabled && onFeedTabChange(tab.name)"
            >
              {{ tab.label }}
            </button>
          </div>
          <router-link to="/community" class="to-community-btn">
            社区广场 
          </router-link>
        </div>

        <!-- 登录提示（关注Tab时未登录）-->
        <div v-if="(activeFeedTab === 'follow' || activeFeedTab === 'followPortfolios') && !authStore.isLoggedIn" class="login-hint">
          <el-icon><Lock /></el-icon>
          <span>登录后查看关注用户的最新动态</span>
          <el-button type="primary" size="small" @click="$router.push('/login')">立即登录</el-button>
        </div>

    <!-- 加载中-->
    <div v-else-if="feedLoading" class="feed-loading">
      <div v-for="n in 4" :key="n" class="post-skeleton">
        <el-skeleton :rows="3" animated />
      </div>
    </div>

    <!-- 关注组合流：单独使用组合卡片 UI -->
    <div v-else-if="activeFeedTab === 'followPortfolios'">
      <div v-if="followPortfoliosFeed.length" class="portfolio-feed">
        <div
          v-for="pf in followPortfoliosFeed"
          :key="pf.id"
          class="portfolio-card-main"
          @click="$router.push(`/portfolios/${pf.id}`)"
        >
          <div class="portfolio-card-header">
            <div class="portfolio-title">{{ pf.title }}</div>
            <span
              class="portfolio-return"
              :class="(pf.returnsYTD || 0) >= 0 ? 'up' : 'down'"
            >
              {{ (pf.returnsYTD || 0) >= 0 ? '+' : '' }}{{ ((pf.returnsYTD || 0) * 100).toFixed(2) }}%
            </span>
          </div>
          <div class="portfolio-meta">
            <el-avatar
              :size="28"
              class="post-avatar author-clickable"
              @click.stop="$router.push({ name: 'UserProfile', params: { userId: pf.userId } })"
            >
              {{ (pf.userName || 'U')[0].toUpperCase() }}
            </el-avatar>
            <span
              class="portfolio-owner author-clickable"
              @click.stop="$router.push({ name: 'UserProfile', params: { userId: pf.userId } })"
            >
              {{ pf.userName }}
            </span>
            <span class="portfolio-risk-tag">
              {{ RISK_LABELS[pf.riskLevel] || pf.riskLevel }}
            </span>
          </div>
          <p v-if="pf.description" class="portfolio-desc">
            {{ pf.description }}
          </p>
        </div>
      </div>
      <div v-else class="feed-empty">
        <el-empty description="暂无关注组合动态，去关注一些优秀投资者吧" />
      </div>
    </div>

    <!-- 帖子流 -->
    <div v-else-if="feedPosts.length" class="posts-feed">
      <div
        v-for="post in feedPosts"
        :key="post.id"
        class="post-card"
        @click="$router.push(`/posts/${post.id}`)"
      >
            <!-- 帖子头部：作者信息-->
            <div class="post-card-header">
              <el-avatar
                :size="36"
                class="post-avatar author-clickable"
                @click.stop="$router.push({ name: 'UserProfile', params: { userId: post.authorId } })"
              >
                {{ (post.authorName || 'U')[0].toUpperCase() }}
              </el-avatar>
              <div
                class="post-author-info author-clickable"
                @click.stop="$router.push({ name: 'UserProfile', params: { userId: post.authorId } })"
              >
                <span class="post-author-name">{{ post.authorName }}</span>
                <span class="post-date">{{ formatDate(post.createdAt) }}</span>
              </div>
              <div class="post-header-right">
                <el-tag
                  v-if="post.tags?.[0]"
                  size="small"
                  class="post-tag"
                >{{ post.tags[0] }}</el-tag>
              </div>
            </div>

            <!-- 帖子内容 -->
            <h3 class="post-title">{{ post.title }}</h3>
            <p class="post-excerpt">{{ post.content }}</p>

            <!-- 关联标的 -->
            <div v-if="post.assets?.length" class="post-assets">
              <span class="assets-label">关联标的</span>
              <span
                v-for="asset in post.assets.slice(0, 4)"
                :key="asset.id"
                class="asset-chip"
                @click.stop="$router.push(`/assets/${asset.id}`)"
              >
                <span class="asset-chip-code">{{ asset.code }}</span>
                <span v-if="asset.name" class="asset-chip-name">{{ asset.name }}</span>
              </span>
            </div>

                <!-- 帖子底部：互动数-->
            <div class="post-footer">
              <div class="post-interactions">
                <span
                  class="interaction-btn"
                  :class="{ liked: post.isLiked }"
                  @click.stop="togglePostLike(post)"
                >
                  <el-icon><Star /></el-icon>
                  <span>{{ post.likes }}</span>
                </span>
                <span class="interaction-btn">
                  <el-icon><ChatLineRound /></el-icon>
                  <span>{{ post.comments }}</span>
                </span>
              </div>
              <span v-if="post.isFavorited" class="favorited-badge">
                <el-icon><CollectionTag /></el-icon>已收藏
              </span>
            </div>
          </div>
        </div>

        <!-- 空状态-->
        <div v-else class="feed-empty">
          <el-empty description="暂无内容，来发表第一篇帖子吧" />
        </div>

        <div class="feed-footer">
          <el-button
            type="text"
            class="see-more-btn"
            @click="$router.push('/community')"
          >
            查看更多内容 
          </el-button>
        </div>
      </section>

      <!-- ===== 右侧边栏 ===== -->
      <aside class="right-sidebar">

        <!-- 第四层：投资组合收益排行 -->
        <div class="sidebar-card">
          <div class="sidebar-card-header">
            <div class="sidebar-card-title">
              <span class="title-emoji">
                <el-icon>
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6">
                    <path d="M8 4h8v3a4 4 0 0 1-4 4 4 4 0 0 1-4-4V4Z" />
                    <path d="M8 4H5a2 2 0 0 0-2 2v1a4 4 0 0 0 4 4" />
                    <path d="M16 4h3a2 2 0 0 1 2 2v1a4 4 0 0 1-4 4" />
                    <path d="M10 15h4" />
                    <path d="M9 19h6" />
                  </svg>
                </el-icon>
              </span>
              <h3>本周收益排行</h3>
            </div>
            <router-link to="/portfolios" class="sidebar-more-link">全部 组合</router-link>
          </div>
          <div v-if="portfolioLoading" class="sidebar-skeleton">
            <el-skeleton :rows="4" animated />
          </div>
          <div v-else-if="topPortfolios.length" class="portfolio-ranking-list">
            <div
              v-for="(pf, idx) in topPortfolios"
              :key="pf.id"
              class="portfolio-rank-item"
              @click="$router.push(`/portfolios/${pf.id}`)"
            >
              <span class="pf-medal">#{{ idx + 1 }}</span>
              <div class="pf-info">
                <span class="pf-title">{{ pf.title }}</span>
                <div class="pf-meta">
                  <el-avatar
                    :size="14"
                    class="pf-avatar author-clickable"
                    @click.stop="$router.push({ name: 'UserProfile', params: { userId: pf.userId } })"
                  >
                    {{ (pf.userName || 'U')[0] }}
                  </el-avatar>
                  <span
                    class="pf-user author-clickable"
                    @click.stop="$router.push({ name: 'UserProfile', params: { userId: pf.userId } })"
                  >
                    {{ pf.userName }}
                  </span>
                  <span class="pf-risk">{{ RISK_LABELS[pf.riskLevel] || pf.riskLevel }}</span>
                </div>
              </div>
              <div class="pf-right">
                <span
                  class="pf-return"
                  :class="(pf.returnsYTD || 0) >= 0 ? 'up' : 'down'"
                >
                  {{ (pf.returnsYTD || 0) >= 0 ? '+' : '' }}{{ ((pf.returnsYTD || 0) * 100).toFixed(2) }}%
                </span>
                <span class="pf-likes">
                  <el-icon><Star /></el-icon>{{ pf.likes }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="sidebar-empty">
            <el-empty :image-size="48" description="暂无组合数据" />
          </div>
          <div class="sidebar-card-footer">
            <el-button
              size="small"
              class="sidebar-action-btn"
              @click="$router.push('/portfolios')"
            >
              浏览全部组合
            </el-button>
            <el-button
              v-if="authStore.isLoggedIn"
              type="primary"
              size="small"
              class="sidebar-action-btn"
              @click="$router.push('/portfolios')"
            >
              创建组合
            </el-button>
          </div>
        </div>

        <!-- 第三层：热门标的讨论 -->
        <div class="sidebar-card">
          <div class="sidebar-card-header">
            <div class="sidebar-card-title">
              <span class="title-emoji">
                <el-icon>
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6">
                    <path d="M12 3s2 2.5 2 5.5S12 14 12 14s-2-2-2-5.5S12 3 12 3Z" />
                    <path d="M8.5 8.5C7 10 6 11.5 6 14a6 6 0 0 0 12 0c0-2.5-1-4-2.5-5.5" />
                  </svg>
                </el-icon>
              </span>
              <h3>热门标的讨论</h3>
            </div>
            <router-link to="/market" class="sidebar-more-link">行情 列表</router-link>
          </div>
          <div v-if="hotAssetsLoading" class="sidebar-skeleton">
            <el-skeleton :rows="4" animated />
          </div>
          <div v-else-if="hotAssets.length" class="hot-assets-list">
            <div
              v-for="(asset, idx) in hotAssets"
              :key="asset.assetId"
              class="hot-asset-item"
              @click="$router.push(`/assets/${asset.assetId}`)"
            >
              <span class="hot-rank-num" :class="idx < 3 ? 'hot-top3' : ''">{{ idx + 1 }}</span>
              <div class="hot-asset-info">
                <span class="hot-code">{{ asset.code }}</span>
                <span class="hot-name">{{ asset.name }}</span>
              </div>
              <div class="hot-right">
                <span class="hot-pct" :class="getChangeClass(asset.changePct)">
                  {{ formatChangePct(asset.changePct) }}
                </span>
                <span class="hot-market">{{ formatMarket(asset.market) }}</span>
              </div>
            </div>
          </div>
          <div v-else class="sidebar-empty">
            <el-empty :image-size="48" description="暂无热门标的" />
          </div>
          <router-link to="/market/rankings">
            <el-button type="text" class="full-ranking-btn">查看完整涨跌幅榜单</el-button>
          </router-link>
        </div>

        <!-- 第五层：社区活跃度统计-->
        <div class="sidebar-card community-stats-card">
          <div class="sidebar-card-title">
            <span class="title-emoji">
              <el-icon>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6">
                  <rect x="4" y="10" width="3" height="8" rx="1" />
                  <rect x="10.5" y="6" width="3" height="12" rx="1" />
                  <rect x="17" y="3" width="3" height="15" rx="1" />
                </svg>
              </el-icon>
            </span>
            <h3>社区活跃度统计</h3>
          </div>
          <div class="community-stats-grid">
            <div class="cs-stat">
              <span class="cs-icon">
                <el-icon>
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6">
                    <circle cx="9" cy="8" r="3" />
                    <path d="M4 18a5 5 0 0 1 10 0" />
                    <circle cx="17" cy="7" r="2.5" />
                    <path d="M14.5 17a4 4 0 0 1 5.5-3.5" />
                  </svg>
                </el-icon>
              </span>
              <div class="cs-content">
                <span class="cs-value">{{ formatNumber(communityStats.activeInvestorsCount) }}</span>
                <span class="cs-label">活跃投资者</span>
              </div>
            </div>
            <div class="cs-stat">
              <span class="cs-icon">
                <el-icon>
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6">
                    <path d="M4 5a2 2 0 0 1 2-2h7.5L20 9.5V19a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z" />
                    <path d="M14 3v6h6" />
                    <path d="M8 13h8" />
                    <path d="M8 17h5" />
                  </svg>
                </el-icon>
              </span>
              <div class="cs-content">
                <span class="cs-value">{{ formatNumber(communityStats.strategiesSharedCount) }}</span>
                <span class="cs-label">策略分享</span>
              </div>
            </div>
            <div class="cs-stat" v-if="authStore.isAdmin">
              <span class="cs-icon">
                <el-icon>
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6">
                    <path d="M12 9v4" />
                    <circle cx="12" cy="17" r="0.8" fill="currentColor" />
                    <path d="M10.29 3.86 3.82 15a2 2 0 0 0 1.71 3h12.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
                  </svg>
                </el-icon>
              </span>
              <div class="cs-content">
                <span class="cs-value admin-value">{{ adminStats.pendingPostsCount }}</span>
                <span class="cs-label">待审内容</span>
              </div>
            </div>
            <div class="cs-stat" v-if="authStore.isAdmin">
              <span class="cs-icon">
                <el-icon>
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6">
                    <path d="M6 3v18" />
                    <path d="M7 4h9l-2 4 2 4H7" />
                  </svg>
                </el-icon>
              </span>
              <div class="cs-content">
                <span class="cs-value admin-value">{{ adminStats.openReportsCount }}</span>
                <span class="cs-label">待处举报</span>
              </div>
            </div>
          </div>

          <!-- 管理员入口-->
          <div v-if="authStore.isAdmin" class="admin-entry" @click="$router.push('/admin')">
            <el-icon><Setting /></el-icon>
            <span>进入管理后台</span>
            <el-icon><ArrowRight /></el-icon>
          </div>

          <!-- 快捷操作 -->
          <div class="quick-actions">
            <div
              v-if="!authStore.isLoggedIn"
              class="quick-action-item"
              @click="$router.push('/login')"
            >
              <span>加入社区</span>
            </div>
            <template v-else>
              <div
                class="quick-action-item"
                @click="$router.push('/community')"
              >
                <span>发布讨论</span>
              </div>
              <div
                class="quick-action-item"
                @click="$router.push('/holdings')"
              >
                <span>管理持仓</span>
              </div>
              <div
                class="quick-action-item"
                @click="$router.push('/portfolios')"
              >
                <span>新建组合</span>
              </div>
              <div
                class="quick-action-item"
                @click="$router.push('/market')"
              >
                <span>查看行情</span>
              </div>
            </template>
          </div>
        </div>

        <!-- 第六层：简单推荐入口-->
        <div class="sidebar-card recommend-card">
          <div class="sidebar-card-title">
            <span class="title-emoji">
              <el-icon>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6">
                  <path d="M9 18h6" />
                  <path d="M10 22h4" />
                  <path d="M8 14a4 4 0 0 1-1.2-2.83A5.2 5.2 0 0 1 12 6.1a5.2 5.2 0 0 1 5.2 5.07A4 4 0 0 1 16 14c-1 1.2-1 1.8-1 2H9c0-.2 0-.8-1-2Z" />
                </svg>
              </el-icon>
            </span>
            <h3>为你推荐</h3>
          </div>
          <div class="recommend-list">
            <div
              v-for="item in recommendList"
              :key="item.id"
              class="recommend-item"
              @click="$router.push(item.link)"
            >
              <span class="rec-icon">
                <el-icon>
                  <component :is="item.icon" />
                </el-icon>
              </span>
              <div class="rec-info">
                <span class="rec-title">{{ item.title }}</span>
                <span class="rec-desc">{{ item.desc }}</span>
              </div>
              <el-icon class="rec-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>

      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useMarketStore } from '@/stores/market'
import { usePortfoliosStore } from '@/stores/portfolios'
import { useAuthStore } from '@/stores/auth'
import { getPosts } from '@/api/posts'
import { getAdminStats } from '@/api/admin'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import {
  InfoFilled,
  Star,
  ChatLineRound,
  ArrowRight,
  DataLine,
  CollectionTag,
  Lock,
  Setting
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { Post } from '@/types'
import type { MarketRankingItem } from '@/types/market'
import type { Portfolio } from '@/types'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

// ==================== Stores ====================
const dashboardStore = useDashboardStore()
const marketStore = useMarketStore()
const portfoliosStore = usePortfoliosStore()
const authStore = useAuthStore()

// ==================== Constants ====================
const MEDALS = ['🥇', '🥈', '🥉']
const RISK_LABELS: Record<string, string> = { Low: '稳健', Medium: '均衡', High: '激进' }

const rankTypes = [
  { key: 'gainers', label: '涨幅榜单' },
  { key: 'losers', label: '跌幅榜单' },
  { key: 'active', label: '活跃榜单' }
]

const chartTabs = [
  { key: '7d', label: '7天' },
  { key: '1d', label: '日K' },
  { key: 'intraday', label: '分时' }
]

// ============================================================
// 第一层：市场总览数据
// ============================================================
const marketLoading = ref(false)
const activeRankType = ref<'gainers' | 'losers' | 'active'>('gainers')
const displayedRankings = ref<MarketRankingItem[]>([])
const activeChartTab = ref('7d')

const fetchMarketRankings = async (type: string = activeRankType.value) => {
  marketLoading.value = true
  try {
    const items = await marketStore.fetchRankings(type)
    displayedRankings.value = items.slice(0, 4)
  } catch (e) {
    console.error('获取市场榜单失败:', e)
    displayedRankings.value = []
  } finally {
    marketLoading.value = false
  }
}

const switchRankType = async (type: string) => {
  activeRankType.value = type
  await fetchMarketRankings(type)
}

// ECharts 配置
const chartOption = computed(() => {
  if (!dashboardStore.dashboardData?.marketSeries) return {}
  return {
    grid: { top: 20, right: 16, bottom: 28, left: 48 },
    xAxis: {
      type: 'category',
      data: dashboardStore.dashboardData.marketSeries.map((item: any) => item.name),
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#F1F5F9', type: 'dashed' } }
    },
    series: [{
      data: dashboardStore.dashboardData.marketSeries.map((item: any) => item.value),
      type: 'line',
      smooth: true,
      lineStyle: { color: '#1D4ED8', width: 2.5 },
      symbol: 'circle',
      symbolSize: 4,
      itemStyle: { color: '#1D4ED8' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(29, 78, 216, 0.18)' },
            { offset: 1, color: 'rgba(29, 78, 216, 0.02)' }
          ]
        }
      }
    }],
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#CBD5E1',
      borderWidth: 1,
      textStyle: { color: '#1F2937', fontFamily: 'Inter', fontSize: 12 }
    }
  }
})

// ============================================================
// 第二层：信息流
// ============================================================
const activeFeedTab = ref('new')
const feedPosts = ref<Post[]>([])
const followPortfoliosFeed = ref<Portfolio[]>([])
const feedLoading = ref(false)

const feedTabs = computed(() => [
  { name: 'new', label: '最新', disabled: false },
  { name: 'hot', label: '热门', disabled: false },
  { name: 'follow', label: '关注-帖子', disabled: !authStore.isLoggedIn },
  { name: 'followPortfolios', label: '关注-组合', disabled: !authStore.isLoggedIn },
  { name: 'recommend', label: '推荐', disabled: false }
])

const fetchFeed = async (tab: string = activeFeedTab.value) => {
  feedLoading.value = true
  try {
    if (tab === 'recommend') {
      if (dashboardStore.dashboardData?.trendingPosts?.length) {
        feedPosts.value = dashboardStore.dashboardData.trendingPosts
        return
      }
    }

    if (tab === 'follow') {
      if (!authStore.isLoggedIn) {
        feedPosts.value = []
        return
      }
      const { getFollowingFeed } = await import('@/api/users')
      const res = await getFollowingFeed({ page: 1, pageSize: 8 })
      feedPosts.value = res.items
      return
    }

    if (tab === 'followPortfolios') {
      if (!authStore.isLoggedIn) {
        followPortfoliosFeed.value = []
        return
      }
      const { getFollowingPortfoliosFeed } = await import('@/api/users')
      const res = await getFollowingPortfoliosFeed({ page: 1, pageSize: 8 })
      followPortfoliosFeed.value = res.items
      return
    }

    const sortMap: Record<string, string> = {
      new: 'new',
      hot: 'hot',
      follow: 'new',
      followPortfolios: 'new',
      recommend: 'hot'
    }
    const response = await getPosts({ sort: sortMap[tab] as any, pageSize: 8 })
    feedPosts.value = response.items
  } catch (e) {
    console.error('获取信息流失败:', e)
    feedPosts.value = []
  } finally {
    feedLoading.value = false
  }
}

const onFeedTabChange = (tab: string) => {
  activeFeedTab.value = tab
  fetchFeed(tab)
}

const togglePostLike = async (post: Post) => {
  if (!authStore.isLoggedIn) {
    return
  }
  try {
    const { like, unlike } = await import('@/api/likes')
    if (post.isLiked) {
      await unlike({ targetType: 'POST', targetId: post.id })
      post.isLiked = false
      post.likes = (post.likes || 1) - 1
    } else {
      await like({ targetType: 'POST', targetId: post.id })
      post.isLiked = true
      post.likes = (post.likes || 0) + 1
    }
  } catch (e) {
    console.error('点赞操作失败:', e)
  }
}

// ============================================================
// 第四层：投资组合排行
// ============================================================
const portfolioLoading = ref(false)
const topPortfolios = ref<Portfolio[]>([])

const fetchTopPortfolios = async () => {
  portfolioLoading.value = true
  try {
    await portfoliosStore.fetchTopPortfolios(5)
    topPortfolios.value = portfoliosStore.topPortfolios
  } catch (e) {
    console.error('获取热门组合失败:', e)
    topPortfolios.value = []
  } finally {
    portfolioLoading.value = false
  }
}

// ============================================================
// 第三层：热门标的讨论
// ============================================================
const hotAssetsLoading = ref(false)
const hotAssets = ref<MarketRankingItem[]>([])

const fetchHotAssets = async () => {
  hotAssetsLoading.value = true
  try {
    const items = await marketStore.fetchRankings('active')
    hotAssets.value = items.slice(0, 8)
  } catch (e) {
    console.error('获取热门标的失败:', e)
    hotAssets.value = []
  } finally {
    hotAssetsLoading.value = false
  }
}

// ============================================================
// 第五层：社区活跃统计
// ============================================================
const communityStats = computed(() => {
  return dashboardStore.dashboardData?.communityStats || {
    activeInvestorsCount: 0,
    strategiesSharedCount: 0
  }
})

const adminStats = ref({ pendingPostsCount: 0, openReportsCount: 0, newUsers24h: 0 })

const fetchAdminStatsData = async () => {
  if (!authStore.isAdmin) return
  try {
    const data = await getAdminStats()
    adminStats.value = data
  } catch (e) {
    // 非关键数据，静默失败
  }
}

// ============================================================
// 第六层：推荐入口（基于规则的静态推荐）
// ============================================================
const recommendList = computed(() => {
  const items = [
    {
      id: 'market',
      icon: DataLine,
      title: '行情列表',
      desc: '浏览 A/H/美股行情数据',
      link: '/market'
    },
    {
      id: 'rankings',
      icon: CollectionTag,
      title: '涨跌幅榜',
      desc: '今日热门股票排行',
      link: '/market/rankings'
    },
    {
      id: 'portfolios',
      icon: Star,
      title: '投资组合',
      desc: '分享你的投资策略',
      link: '/portfolios'
    }
  ]
  if (authStore.isLoggedIn) {
    items.push({
      id: 'holdings',
      icon: DataLine,
      title: '我的持仓',
      desc: '查看持仓收益分析',
      link: '/holdings'
    })
  }
  return items
})

// ============================================================
// 工具函数
// ============================================================
const formatPrice = (price: number | null) => {
  if (price == null) return '--'
  return price.toFixed(2)
}

const formatChangePct = (pct: number | null | undefined) => {
  if (pct == null) return '--'
  const sign = pct >= 0 ? '+' : ''
  return `${sign}${Number(pct).toFixed(2)}%`
}

const getChangeClass = (pct: number | null | undefined) => {
  if (pct == null) return 'flat'
  if (Number(pct) > 0) return 'up'
  if (Number(pct) < 0) return 'down'
  return 'flat'
}

const formatMarket = (market: string | null | undefined) => {
  const map: Record<string, string> = {
    SH: 'A股沪市', SZ: 'A股深市', HK: '港股', US: '美股'
  }
  return market ? (map[market] || market) : '--'
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('MM-DD HH:mm')
}

const formatNumber = (n: number | string | null | undefined) => {
  if (n == null || n === 0) return '0'
  const num = Number(n)
  if (isNaN(num)) return '--'
  if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿'
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  return num.toString()
}

// ============================================================
// 生命周期
// ============================================================
onMounted(() => {
  // 并行加载所有数据
  Promise.allSettled([
    dashboardStore.fetchDashboardData(),
    fetchMarketRankings(),
    fetchFeed(),
    fetchTopPortfolios(),
    fetchHotAssets(),
    fetchAdminStatsData()
  ])
})
</script>

<style lang="scss" scoped>
.dashboard {
  max-width: 1280px;
  margin: 0 auto;
  padding-bottom: 2rem;
  animation: fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

// ============================================================
// 免责声明 - Apple Style 软提示条
// ============================================================
.disclaimer-bar {
  display: flex;
  align-items: center;
  gap: $apple-space-3;
  padding: $apple-space-3 $apple-space-4;
  background: rgba(245, 158, 11, 0.06);
  border: 1px solid rgba(245, 158, 11, 0.15);
  border-radius: $apple-radius-sm;
  margin-bottom: $apple-space-6;
  font-size: $apple-font-caption;
  color: #D97706;
  font-family: $apple-font-family;

  .el-icon {
    flex-shrink: 0;
    color: #D97706;
    font-size: 14px;
  }
}

// ============================================================
// 第一层：市场总览
// ============================================================
.market-section {
  background: $apple-bg-elevated;
  backdrop-filter: $apple-glass-blur;
  -webkit-backdrop-filter: $apple-glass-blur;
  border: 1px solid $apple-border-light;
  border-radius: $apple-radius-xl; // Hero区使用更大的圆角
  padding: $apple-space-6;
  margin-bottom: $apple-space-6;
  box-shadow: $apple-shadow-sm;
}

.market-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;

  @media (max-width: 768px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
}

.market-title-block {
  .market-main-title {
    font-size: $apple-font-h3;
    font-weight: 600;
    color: $apple-text-primary;
    margin: 0 0 $apple-space-2 0;
    letter-spacing: -0.01em;
    font-family: $apple-font-family;
  }
  .market-subtitle {
    font-size: $apple-font-caption;
    color: $apple-text-tertiary;
    margin: 0;
    font-family: $apple-font-family;
  }
}

.market-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.rank-type-btns {
  display: inline-flex;
  padding: 4px;
  border-radius: $apple-radius-segmented;
  background: rgba(0, 0, 0, 0.05);
  gap: 4px;
}

.rank-type-btn {
  padding: 10px 16px;
  border-radius: $apple-radius-segmented-item;
  border: none;
  cursor: pointer;
  font-size: $apple-font-body;
  font-weight: 400;
  color: $apple-text-secondary;
  background: transparent;
  transition: all 0.2s ease;
  font-family: $apple-font-family;
  white-space: nowrap;

  &:hover {
    color: $apple-text-primary;
  }

  &.active {
    background: #fff;
    color: $apple-text-primary;
    font-weight: 500;
    box-shadow: $apple-shadow-sm;
  }
}

.full-ranking-link {
  font-size: $apple-font-body;
  color: $apple-accent;
  text-decoration: none;
  font-weight: 500;
  transition: $transition-colors;
  font-family: $apple-font-family;

  &:hover { color: $apple-accent; }
}

.market-body {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 1.25rem;

  @media (max-width: 1100px) {
    grid-template-columns: 1fr;
  }
}

// Rankings Grid (4 cards)
.rankings-panel {
  min-height: 220px;
}

.loading-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $apple-space-4;
}

.skeleton-card {
  background: $apple-bg-elevated;
  border: 1px solid $apple-border-light;
  border-radius: $apple-radius-md;
  padding: $apple-space-6;
}

.rankings-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $apple-space-4;

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.rank-card {
  background: $apple-bg-elevated;
  backdrop-filter: $apple-glass-blur;
  -webkit-backdrop-filter: $apple-glass-blur;
  border: 1px solid $apple-border-light;
  border-radius: $apple-radius-md;
  padding: $apple-space-6;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  flex-direction: column;
  gap: $apple-space-3;
  box-shadow: $apple-shadow-sm;

  &:hover {
    border-color: rgba(0, 113, 227, 0.2);
    background: rgba(255, 255, 255, 0.9);
    transform: translateY(-2px);
    box-shadow: $apple-shadow-md;
  }
}

.rank-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rank-num {
  font-size: $apple-font-caption;
  font-weight: 600;
  color: $apple-text-tertiary;
  font-family: 'IBM Plex Mono', monospace;
}

.market-tag {
  font-size: 0.625rem !important;
  font-weight: 700 !important;
  padding: 0 0.375rem !important;
  height: 18px !important;
  line-height: 18px !important;
}

.rank-card-middle {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.rank-code {
  font-size: $apple-font-body;
  font-weight: 600;
  color: $apple-text-primary;
  font-family: 'IBM Plex Mono', monospace;
}

.rank-name {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: $apple-font-family;
}

.rank-card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: $apple-space-3;
  border-top: 1px solid $apple-border-light;
}

.rank-price {
  font-size: $apple-font-h3;
  font-weight: 600;
  color: $apple-text-primary;
  font-family: 'IBM Plex Mono', monospace;
}

.rank-pct {
  font-size: $apple-font-body;
  font-weight: 600;
  font-family: 'IBM Plex Mono', monospace;

  &.up { color: #e85d5d; }
  &.down { color: #16a34a; }
  &.flat { color: $apple-text-tertiary; }
}

.rankings-empty {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $apple-space-10 $apple-space-4;
  color: $apple-text-tertiary;
  gap: $apple-space-3;
  text-align: center;
  font-family: $apple-font-family;

  p { margin: 0; font-weight: 600; color: $apple-text-secondary; font-family: $apple-font-family; }
  span { font-size: $apple-font-body; font-family: $apple-font-family; }
}

// Chart Panel - Apple Style
.chart-panel {
  background: $apple-bg-elevated;
  backdrop-filter: $apple-glass-blur;
  -webkit-backdrop-filter: $apple-glass-blur;
  border: 1px solid $apple-border-light;
  border-radius: $apple-radius-md;
  padding: $apple-space-6;
  display: flex;
  flex-direction: column;
  gap: $apple-space-4;
  box-shadow: $apple-shadow-sm;
}

.chart-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-panel-title {
  font-size: $apple-font-body;
  font-weight: 600;
  color: $apple-text-primary;
  font-family: $apple-font-family;
}

.chart-tab-group {
  display: inline-flex;
  padding: 4px;
  border-radius: $apple-radius-segmented;
  background: rgba(0, 0, 0, 0.05);
  gap: 4px;
}

.chart-tab-btn {
  padding: 10px 16px;
  border-radius: $apple-radius-segmented-item;
  border: none;
  cursor: pointer;
  font-size: $apple-font-caption;
  font-weight: 400;
  color: $apple-text-secondary;
  background: transparent;
  transition: all 0.2s ease;
  font-family: $apple-font-family;

  &:hover { color: $apple-text-primary; }
  &.active {
    background: #fff;
    color: $apple-text-primary;
    font-weight: 500;
    box-shadow: $apple-shadow-sm;
  }
}

.chart-area {
  flex: 1;
  min-height: 180px;
}

.echarts-chart {
  width: 100%;
  height: 180px;
}

.chart-skeleton { height: 180px; }

.chart-data-source {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  text-align: right;
  opacity: 0.7;
  font-family: $apple-font-family;
}

// ============================================================
// 主内容区（信息流 + 侧边栏）
// ============================================================
.main-content-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 1.5rem;
  align-items: start;

  @media (max-width: 1100px) {
    grid-template-columns: 1fr;
  }
}

// ============================================================
// 信息流（Feed）
// ============================================================
.feed-section {
  background: transparent;
}

.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $apple-space-6;
  gap: $apple-space-4;
}

.feed-segmented-control {
  display: inline-flex;
  padding: 4px;
  border-radius: $apple-radius-segmented;
  background: rgba(0, 0, 0, 0.05);
  gap: 4px;
  flex: 1;
}

.feed-segmented-item {
  padding: 10px 16px;
  border-radius: $apple-radius-segmented-item;
  color: $apple-text-secondary;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: $apple-font-body;
  font-weight: 400;
  font-family: $apple-font-family;
  transition: all 0.2s ease;
  white-space: nowrap;

  &:hover:not(.disabled) {
    color: $apple-text-primary;
  }

  &.active {
    background: #fff;
    color: $apple-text-primary;
    font-weight: 500;
    box-shadow: $apple-shadow-sm;
  }

  &.disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

.to-community-btn {
  font-size: $apple-font-body;
  color: $apple-accent;
  text-decoration: none;
  font-weight: 500;
  white-space: nowrap;
  transition: $transition-colors;
  font-family: $apple-font-family;
  &:hover { color: $apple-accent; }
}

.login-hint {
  display: flex;
  align-items: center;
  gap: $apple-space-3;
  padding: $apple-space-6;
  background: rgba(0, 113, 227, 0.04);
  border: 1px dashed rgba(0, 113, 227, 0.15);
  border-radius: $apple-radius-md;
  color: $apple-text-secondary;
  font-size: $apple-font-body;
  margin-top: $apple-space-4;
  font-family: $apple-font-family;
}

.feed-loading {
  display: flex;
  flex-direction: column;
  gap: $apple-space-4;
  margin-top: $apple-space-4;
}

.post-skeleton {
  background: $apple-bg-elevated;
  border: 1px solid $apple-border-light;
  border-radius: $apple-radius-md;
  padding: $apple-space-6;
}

.portfolio-feed {
  display: flex;
  flex-direction: column;
  gap: $apple-space-4;
  margin-top: $apple-space-4;
}

.portfolio-card-main {
  border-radius: $apple-radius-md;
  border: 1px solid $apple-border-light;
  padding: $apple-space-6;
  background: $apple-bg-elevated;
  backdrop-filter: $apple-glass-blur;
  -webkit-backdrop-filter: $apple-glass-blur;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: $apple-shadow-sm;

  &:hover {
    border-color: rgba(0, 113, 227, 0.2);
    background: rgba(255, 255, 255, 0.9);
    box-shadow: $apple-shadow-md;
    transform: translateY(-1px);
  }
}

.portfolio-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $apple-space-3;

  .portfolio-title {
    font-size: $apple-font-body;
    font-weight: 600;
    color: $apple-text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-family: $apple-font-family;
  }

  .portfolio-return {
    font-size: $apple-font-body;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;

    &.up { color: #e85d5d; }
    &.down { color: #16a34a; }
  }
}

.portfolio-meta {
  display: flex;
  align-items: center;
  gap: $apple-space-2;
  margin-bottom: $apple-space-2;

  .portfolio-owner {
    font-size: $apple-font-body;
    color: $apple-text-secondary;
    font-family: $apple-font-family;
  }

  .portfolio-risk-tag {
    padding: 2px 10px;
    font-size: $apple-font-caption;
    border-radius: 999px;
    background: rgba(0, 0, 0, 0.04);
    color: $apple-text-secondary;
    font-family: $apple-font-family;
  }
}

.portfolio-desc {
  font-size: $apple-font-body;
  color: $apple-text-secondary;
  margin: $apple-space-2 0 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: $apple-font-family;
}

.posts-feed {
  display: flex;
  flex-direction: column;
  gap: $apple-space-4;
  margin-top: $apple-space-4;
}

.post-card {
  background: $apple-bg-elevated;
  backdrop-filter: $apple-glass-blur;
  -webkit-backdrop-filter: $apple-glass-blur;
  border: 1px solid $apple-border-light;
  border-radius: $apple-radius-md;
  padding: $apple-space-6;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: $apple-shadow-sm;

  &:hover {
    border-color: rgba(0, 113, 227, 0.2);
    background: rgba(255, 255, 255, 0.9);
    box-shadow: $apple-shadow-md;
    transform: translateY(-2px);
  }
}

.post-card-header {
  display: flex;
  align-items: center;
  gap: $apple-space-3;
  margin-bottom: $apple-space-4;
}

.post-avatar {
  background: $gradient-primary !important;
  font-size: $apple-font-body !important;
  font-weight: 600 !important;
  flex-shrink: 0;
}

.post-author-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.post-author-name {
  font-size: $apple-font-body;
  font-weight: 600;
  color: $apple-text-primary;
  font-family: $apple-font-family;
}

.post-date {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  font-family: 'IBM Plex Mono', monospace;
}

.post-header-right {
  flex-shrink: 0;
}

.post-tag {
  font-size: $apple-font-caption !important;
  font-weight: 500 !important;
  padding: 4px 10px !important;
  border-radius: 999px !important;
  background: rgba(0, 0, 0, 0.05) !important;
  border: none !important;
  color: $apple-text-secondary !important;
}

.post-title {
  font-size: $apple-font-h3;
  font-weight: 600;
  color: $apple-text-primary;
  margin: 0 0 $apple-space-3 0;
  line-height: 1.4;
  letter-spacing: -0.01em;
  font-family: $apple-font-family;
}

.post-excerpt {
  font-size: $apple-font-body;
  color: $apple-text-secondary;
  line-height: 1.6;
  margin: 0 0 $apple-space-4 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
  font-family: $apple-font-family;
}

.post-assets {
  display: flex;
  align-items: center;
  gap: $apple-space-3;
  margin-bottom: $apple-space-4;
  flex-wrap: wrap;
}

.assets-label {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  font-family: $apple-font-family;
}

.asset-chip {
  display: inline-flex;
  align-items: center;
  gap: $apple-space-2;
  padding: 4px 10px;
  background: rgba(0, 0, 0, 0.05);
  border: none;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: $apple-font-caption;
  font-family: $apple-font-family;

  &:hover {
    background: rgba(0, 0, 0, 0.08);
  }

  .asset-chip-code {
    font-weight: 600;
    color: $apple-text-primary;
    font-family: 'IBM Plex Mono', monospace;
  }

  .asset-chip-name {
    color: $apple-text-tertiary;
  }
}

.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: $apple-space-4;
  border-top: 1px solid $apple-border-light;
}

.post-interactions {
  display: flex;
  gap: $apple-space-6;
}

.interaction-btn {
  display: flex;
  align-items: center;
  gap: $apple-space-2;
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  cursor: pointer;
  transition: $transition-colors;
  font-family: $apple-font-family;

  &:hover { color: $apple-accent; }
  &.liked { color: #e85d5d; }
}

.favorited-badge {
  display: flex;
  align-items: center;
  gap: $apple-space-2;
  font-size: $apple-font-caption;
  color: $warning-color;
  font-family: $apple-font-family;
}

.feed-empty {
  padding: 2rem 0;
}

.feed-footer {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

.see-more-btn {
  color: $apple-text-tertiary !important;
  font-size: $apple-font-body !important;
  font-weight: 500 !important;
  font-family: $apple-font-family !important;
  &:hover { color: $apple-accent !important; }
}

// ============================================================
// 右侧边栏
// ============================================================
.right-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sidebar-card {
  background: $apple-bg-elevated;
  backdrop-filter: $apple-glass-blur;
  -webkit-backdrop-filter: $apple-glass-blur;
  border: 1px solid $apple-border-light;
  border-radius: $apple-radius-md;
  padding: $apple-space-6;
  box-shadow: $apple-shadow-sm;
}

.sidebar-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $apple-space-4;
}

.sidebar-card-title {
  display: flex;
  align-items: center;
  gap: $apple-space-3;

  .title-emoji { font-size: 1rem; }

  h3 {
    font-size: $apple-font-body;
    font-weight: 600;
    color: $apple-text-primary;
    margin: 0;
    letter-spacing: -0.01em;
    font-family: $apple-font-family;
  }
}

.sidebar-more-link {
  font-size: $apple-font-body;
  color: $apple-accent;
  text-decoration: none;
  font-weight: 500;
  transition: $transition-colors;
  font-family: $apple-font-family;
  &:hover { color: $apple-accent; }
}

.sidebar-skeleton { padding: 0.5rem 0; }

.sidebar-empty {
  padding: 0.75rem 0;
  display: flex;
  justify-content: center;
}

// ---- Portfolio Ranking ----
.portfolio-ranking-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.portfolio-rank-item {
  display: flex;
  align-items: center;
  gap: $apple-space-3;
  padding: $apple-space-4 $apple-space-3;
  border-radius: $apple-radius-sm;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(0, 0, 0, 0.03);
  }
}

.pf-medal {
  font-size: $apple-font-body;
  font-weight: 600;
  color: $apple-text-tertiary;
  flex-shrink: 0;
  width: 28px;
  text-align: center;
  font-family: 'IBM Plex Mono', monospace;
}

.pf-info {
  flex: 1;
  min-width: 0;
}

.pf-title {
  font-size: $apple-font-body;
  font-weight: 600;
  color: $apple-text-primary;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: $apple-font-family;
}

.pf-meta {
  display: flex;
  align-items: center;
  gap: $apple-space-2;
  margin-top: $apple-space-2;
}

.pf-avatar {
  background: $gradient-primary !important;
  font-size: 0.5625rem !important;
  font-weight: 600 !important;
}

.pf-user {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  font-family: $apple-font-family;
}

.pf-risk {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.04);
  border: none;
  border-radius: 999px;
  font-family: $apple-font-family;
}

.pf-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: $apple-space-2;
  flex-shrink: 0;
}

.pf-return {
  font-size: $apple-font-body;
  font-weight: 600;
  font-family: 'IBM Plex Mono', monospace;

  &.up { color: #e85d5d; }
  &.down { color: #16a34a; }
}

.pf-likes {
  display: flex;
  align-items: center;
  gap: $apple-space-2;
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  font-family: $apple-font-family;
}

.sidebar-card-footer {
  display: flex;
  gap: $apple-space-3;
  margin-top: $apple-space-4;
  padding-top: $apple-space-4;
  border-top: 1px solid $apple-border-light;
}

.sidebar-action-btn {
  flex: 1;
  font-size: $apple-font-caption !important;
}

// ---- Hot Assets ----
.hot-assets-list {
  display: flex;
  flex-direction: column;
  gap: $apple-space-2;
}

.hot-asset-item {
  display: flex;
  align-items: center;
  gap: $apple-space-3;
  padding: $apple-space-3;
  border-radius: $apple-radius-sm;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(0, 0, 0, 0.03);
  }
}

.hot-rank-num {
  font-size: $apple-font-body;
  font-weight: 600;
  color: $apple-text-tertiary;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
  font-family: 'IBM Plex Mono', monospace;

  &.hot-top3 { color: $warning-color; }
}

.hot-asset-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.hot-code {
  font-size: $apple-font-body;
  font-weight: 600;
  color: $apple-text-primary;
  font-family: 'IBM Plex Mono', monospace;
}

.hot-name {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: $apple-font-family;
}

.hot-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: $apple-space-2;
  flex-shrink: 0;
}

.hot-pct {
  font-size: $apple-font-body;
  font-weight: 600;
  font-family: 'IBM Plex Mono', monospace;

  &.up { color: #e85d5d; }
  &.down { color: #16a34a; }
  &.flat { color: $apple-text-tertiary; }
}

.hot-market {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  background: rgba(0, 0, 0, 0.04);
  border: none;
  padding: 2px 8px;
  border-radius: 999px;
  font-family: $apple-font-family;
}

.full-ranking-btn {
  color: $apple-text-tertiary !important;
  font-size: $apple-font-body !important;
  margin-top: $apple-space-3;
  width: 100%;
  font-family: $apple-font-family !important;
  &:hover { color: $apple-accent !important; }
}

// ---- Community Stats ----
.community-stats-card {
  .sidebar-card-title { margin-bottom: $apple-space-4; }
}

.community-stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $apple-space-3;
  margin-bottom: $apple-space-4;
}

.cs-stat {
  display: flex;
  align-items: center;
  gap: $apple-space-3;
  padding: $apple-space-3;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid $apple-border-light;
  border-radius: $apple-radius-sm;
}

.cs-icon {
  font-size: 1.125rem;
  flex-shrink: 0;
  color: $apple-text-secondary;
}

.cs-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cs-value {
  font-size: $apple-font-body;
  font-weight: 600;
  color: $apple-text-primary;
  font-family: 'IBM Plex Mono', monospace;
  letter-spacing: -0.02em;
}

.cs-label {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  font-family: $apple-font-family;
}

.admin-value {
  color: $warning-color;
}

.admin-entry {
  display: flex;
  align-items: center;
  gap: $apple-space-3;
  padding: $apple-space-3 $apple-space-4;
  background: rgba(245, 158, 11, 0.06);
  border: 1px solid rgba(245, 158, 11, 0.15);
  border-radius: $apple-radius-sm;
  cursor: pointer;
  font-size: $apple-font-body;
  font-weight: 500;
  color: #D97706;
  margin-bottom: $apple-space-4;
  transition: all 0.2s ease;
  font-family: $apple-font-family;

  &:hover {
    background: rgba(245, 158, 11, 0.1);
    border-color: rgba(245, 158, 11, 0.25);
  }

  span { flex: 1; }
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: $apple-space-2;
}

.quick-action-item {
  padding: $apple-space-3 $apple-space-4;
  border-radius: $apple-radius-sm;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: $apple-font-body;
  color: $apple-text-primary;
  font-family: $apple-font-family;
  border: none;
  background: transparent;
  text-align: left;

  &:hover {
    background: rgba(0, 0, 0, 0.03);
  }
}

// ---- Recommend Card ----
.recommend-card {
  .sidebar-card-title { margin-bottom: 0.875rem; }
}

.recommend-list {
  display: flex;
  flex-direction: column;
  gap: $apple-space-2;
}

.recommend-item {
  display: flex;
  align-items: center;
  gap: $apple-space-3;
  padding: $apple-space-3;
  border-radius: $apple-radius-sm;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(0, 0, 0, 0.03);
  }
}

.rec-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
  color: $apple-text-secondary;
}

.rec-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rec-title {
  font-size: $apple-font-body;
  font-weight: 600;
  color: $apple-text-primary;
  font-family: $apple-font-family;
}

.rec-desc {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  font-family: $apple-font-family;
}

.rec-arrow {
  color: $apple-text-tertiary;
  flex-shrink: 0;
  font-size: $apple-font-body;
}

// ============================================================
// 全局变量
// ============================================================
.up { color: #e85d5d; }
.down { color: #16a34a; }
.flat { color: $apple-text-tertiary; }

// ============================================================
// 动画
// ============================================================
@keyframes fadeInUp {
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


