<template>
  <div class="main-layout">
    <!-- 侧边栏-->
    <aside class="sidebar">
      <!-- 背景装饰 -->
      <div class="sidebar-glow"></div>

      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 17L9 11L13 15L21 7" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M17 7H21V11" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="logo-text-group">
            <h1 class="logo-text">InvestHub</h1>
            <span class="logo-tagline">投资社区</span>
          </div>
        </div>
      </div>

      <nav class="nav-menu">
        <router-link
          v-for="item in menuItems"
          :key="item.name"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.name === item.name }"
        >
          <div class="nav-icon-wrap">
            <el-icon class="nav-icon">
              <component :is="item.icon" />
            </el-icon>
          </div>
          <span class="nav-text">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- 免责声明 -->
      <div class="sidebar-disclaimer">
        <p>数据来源：Tushare，仅供参考，不构成投资建议</p>
      </div>

      <div class="sidebar-footer">
        <div class="user-info" v-if="authStore.user">
          <el-avatar 
            :src="authStore.user?.avatar || ''" 
            :size="38"
            class="user-avatar"
          >
            {{ authStore.user?.displayName?.[0] || 'U' }}
          </el-avatar>
          <div class="user-details">
            <p class="user-name">
              {{ authStore.user?.displayName || 'Unknown User' }}
              <span v-if="authStore.user?.vBadge" class="v-badge">V</span>
            </p>
            <p class="user-username">@{{ authStore.user?.username || 'unknown' }}</p>
          </div>
          <button 
            @click="handleLogout"
            class="logout-btn"
            title="退出登录"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="16 17 21 12 16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- 主内容区-->
    <main class="main-content">
      <!-- 顶部导航-->
      <header class="main-header">
        <div class="header-left">
          <div class="page-breadcrumb">
            <span class="breadcrumb-dot"></span>
            <span class="breadcrumb-text">{{ currentPageLabel }}</span>
          </div>
        </div>
        <div class="search-bar">
          <div class="search-inner-wrap">
            <div class="search-inner" @keyup.enter="handleSearchEnter">
              <svg class="search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
                <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <input
                v-model="searchQuery"
                placeholder="搜索讨论、资产、组合..."  
                class="search-input"
                @focus="handleSearchFocus"
                @blur="handleSearchBlur"
                @input="onSearchInput"
              />
            </div>

            <MainLayoutSearchDropdown
              v-if="showSearchDropdown"
              :search-query="searchQuery"
              :search-loading="searchLoading"
              :hot-keywords="hotKeywords"
              :search-results="searchResults"
              @primary-search="handleSearchEnter"
              @hot-keyword="useHotKeyword"
              @go-post="goPost"
              @go-asset="goAsset"
              @go-portfolio="goPortfolio"
            />
          </div>
        </div>
        <div class="header-actions">
          <button 
            class="notification-btn"
            @click="toggleNotifications"
            title="通知"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M13.73 21a2 2 0 01-3.46 0" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="notif-badge" v-if="unreadCountComputed">{{ unreadCountComputed }}</span>
          </button>
          <div class="header-avatar" v-if="authStore.user">
            <el-avatar 
              :src="authStore.user?.avatar || ''" 
              :size="34"
            >
              {{ authStore.user?.displayName?.[0] || 'U' }}
            </el-avatar>
          </div>
        </div>
      </header>

      <!-- 通知抽屉（异步分包，首次打开时再挂载） -->
      <MainLayoutNotificationDrawer
        v-if="notificationDrawerVisible"
        v-model="notificationDrawerVisible"
        :items="notificationsStore.items"
        :loading="notificationsStore.loading"
        @mark-all-read="handleMarkAllRead"
        @notification-click="handleNotificationClick"
      />

      <!-- 页面内容 -->
      <div class="page-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount, watch, reactive, defineAsyncComponent } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useNotificationsStore } from '../../stores/notifications'
import { ElMessage } from 'element-plus'
import {
  House,
  UserFilled,
  TrendCharts,
  Setting,
  User,
  DataLine,
  Coin,
  ChatDotRound
} from '@element-plus/icons-vue'
import { preloadAssetDetailCharts } from '../../utils/preload'
import type { GlobalSearchResult } from '../../api/search'
import type { Notification } from '../../types'

const MainLayoutSearchDropdown = defineAsyncComponent(() => import('./MainLayoutSearchDropdown.vue'))
const MainLayoutNotificationDrawer = defineAsyncComponent(() => import('./MainLayoutNotificationDrawer.vue'))

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()

const searchQuery = ref('')
const searchFocused = ref(false)
const searchLoading = ref(false)
const hotKeywords = ref<string[]>(['AAPL', '平安银行', '科技ETF', '价值投资'])

const searchResults = reactive<GlobalSearchResult>({
  posts: { items: [], total: 0 },
  assets: { items: [], total: 0 },
  portfolios: { items: [], total: 0 }
})

let searchTimer: ReturnType<typeof setTimeout> | null = null
const notificationDrawerVisible = ref(false)
let notificationEventSource: EventSource | null = null
let notificationsBootstrapped = false
let searchApiLoader: Promise<typeof import('../../api/search')> | null = null
const notificationsStreamPath = '/notifications/stream/'

const loadSearchApi = async () => {
  if (!searchApiLoader) {
    searchApiLoader = import('../../api/search')
  }
  return searchApiLoader
}

const bootstrapNotifications = async () => {
  if (notificationsBootstrapped || !authStore.isLoggedIn) return
  notificationsBootstrapped = true
  try {
    const base = import.meta.env.VITE_API_BASE_URL || '/api'
    const url =
      (base.startsWith('http') ? base : `${window.location.origin}${base}`) +
      notificationsStreamPath +
      `?token=${encodeURIComponent(localStorage.getItem('investhub_token') || '')}`

    notificationEventSource = new EventSource(url)
    notificationEventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data && Array.isArray(data.items)) {
          notificationsStore.applyStreamSnapshot({
            unreadCount: typeof data.unreadCount === 'number' ? data.unreadCount : 0,
            items: data.items
          })
        }
      } catch {
        // ignore
      }
    }
    notificationEventSource.addEventListener('close', () => {
      notificationEventSource?.close()
      notificationEventSource = null
    })
  } catch {
    // SSE 建立失败静默降级
  }
}

const menuItems = computed(() => [
  { name: 'Dashboard', path: '/', label: '市场总览', icon: House },
  { name: 'MarketList', path: '/market', label: '行情列表', icon: DataLine },
  { name: 'Community', path: '/community', label: '社区论坛', icon: UserFilled },
  { name: 'Groups', path: '/groups', label: '群组', icon: ChatDotRound },
  { name: 'Portfolios', path: '/portfolios', label: '投资组合', icon: TrendCharts },
  ...(authStore.isLoggedIn ? [{ name: 'MyHoldings', path: '/holdings', label: '我的持仓', icon: Coin }] : []),
  ...(authStore.isAdmin ? [{ name: 'AdminPanel', path: '/admin', label: '管理后台', icon: Setting }] : []),
  { name: 'Profile', path: '/profile', label: '我的主页', icon: User }
])

const extraPageLabels: Record<string, string> = {
  AssetDetail: '个股详情',
  MarketRankings: '涨跌幅榜',
  PostDetail: '帖子详情',
  PortfolioDetail: '组合详情',
  DataMonitor: '数据监控'
}

const currentPageLabel = computed(() => {
  const item = menuItems.value.find(m => m.name === route.name)
  if (item) return item.label
  return extraPageLabels[route.name as string] || 'InvestHub'
})

const showSearchDropdown = computed(() => {
  const hasResults =
    searchResults.posts.items.length ||
    searchResults.assets.items.length ||
    searchResults.portfolios.items.length

  return searchFocused.value && (searchQuery.value.trim().length > 0 || hasResults || hotKeywords.value.length > 0)
})

const handleLogout = async () => {
  try {
    await authStore.logout()
    router.push('/login')
    ElMessage.success('已退出登录')
  } catch (error) {
    ElMessage.error('退出登录失败')
  }
}

const unreadCountComputed = computed(() => notificationsStore.unreadCount)

const toggleNotifications = async () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录查看通知')
    return
  }
  notificationDrawerVisible.value = !notificationDrawerVisible.value
  if (notificationDrawerVisible.value) {
    if (!notificationsStore.items.length) {
      await notificationsStore.fetchNotifications({ page: 1, pageSize: 20 })
    }
    await bootstrapNotifications()
  }
}

const handleMarkAllRead = async () => {
  try {
    await notificationsStore.markAllRead()
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleNotificationClick = async (item: Notification) => {
  try {
    if (!item.is_read) {
      await notificationsStore.markRead(item.id)
    }

    // 根据关联对象类型跳转到对应页面
    if (item.related_object_type === 'POST' && item.related_object_id) {
      router.push({ name: 'PostDetail', params: { id: item.related_object_id } })
    } else if (item.related_object_type === 'PORTFOLIO' && item.related_object_id) {
      router.push({ name: 'PortfolioDetail', params: { id: item.related_object_id } })
    } else if (item.related_object_type === 'USER' && item.related_object_id) {
      router.push({ name: 'UserProfile', params: { userId: item.related_object_id } })
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const resetSearchResults = () => {
  searchResults.posts = { items: [], total: 0 }
  searchResults.assets = { items: [], total: 0 }
  searchResults.portfolios = { items: [], total: 0 }
}

const fetchSearchSuggestions = async () => {
  const q = searchQuery.value.trim()
  if (!q) {
    resetSearchResults()
    return
  }
  searchLoading.value = true
  try {
    const { globalSearch } = await loadSearchApi()
    const data = await globalSearch({ q, type: 'all' })
    searchResults.posts = {
      items: data.posts.items.slice(0, 3),
      total: data.posts.total
    }
    searchResults.assets = {
      items: data.assets.items.slice(0, 5),
      total: data.assets.total
    }
    searchResults.portfolios = {
      items: data.portfolios.items.slice(0, 3),
      total: data.portfolios.total
    }
  } catch (e) {
    resetSearchResults()
  } finally {
    searchLoading.value = false
  }
}

const handleSearchFocus = () => {
  searchFocused.value = true
  if (searchQuery.value.trim()) {
    fetchSearchSuggestions()
  }
}

const handleSearchBlur = () => {
  // 延迟收起，保证点击下拉项时事件能触发
  setTimeout(() => {
    searchFocused.value = false
  }, 150)
}

const onSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  const q = searchQuery.value.trim()
  if (!q) {
    resetSearchResults()
    return
  }
  searchTimer = setTimeout(() => {
    fetchSearchSuggestions()
  }, 300)
}

const handleSearchEnter = () => {
  const q = searchQuery.value.trim()
  if (!q) return
  router.push({
    name: 'Search',
    query: {
      q,
      type: 'all'
    }
  })
}

const useHotKeyword = (word: string) => {
  searchQuery.value = word
  handleSearchEnter()
}

const goPost = (id: number) => {
  router.push({ name: 'PostDetail', params: { id } })
}

const goAsset = (id: number) => {
  preloadAssetDetailCharts()
  router.push({ name: 'AssetDetail', params: { assetId: String(id) } })
}

const goPortfolio = (id: number) => {
  router.push({ name: 'PortfolioDetail', params: { id } })
}

onBeforeUnmount(() => {
  if (notificationEventSource) {
    notificationEventSource.close()
    notificationEventSource = null
  }
})

watch(
  () => authStore.isLoggedIn,
  async (loggedIn) => {
    if (loggedIn) {
      notificationsBootstrapped = false
    } else {
      notificationsStore.items = []
      notificationsBootstrapped = false
      if (notificationEventSource) {
        notificationEventSource.close()
        notificationEventSource = null
      }
    }
  }
)
</script>

<style lang="scss" scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: $apple-bg-page;
}

// ============================================
// Sidebar - Apple Style
// ============================================
.sidebar {
  width: $apple-sidebar-width;
  background: $apple-sidebar-bg;
  backdrop-filter: $apple-glass-blur;
  -webkit-backdrop-filter: $apple-glass-blur;
  border-right: 1px solid $apple-border-light;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  overflow-y: auto;
  z-index: 10;

  @media (max-width: 768px) {
    width: 64px;

    .logo-text-group,
    .nav-text,
    .user-details,
    .sidebar-footer .user-details {
      display: none;
    }
  }
}

.sidebar-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 160px;
  background: radial-gradient(ellipse at 50% 0%, rgba(29, 78, 216, 0.06) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.sidebar-header {
  padding: $apple-space-6 $apple-space-5 $apple-space-4;
  border-bottom: 1px solid $apple-border-light;
  position: relative;
  z-index: 1;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-icon {
  width: 42px;
  height: 42px;
  background: $gradient-primary;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow-blue;
  flex-shrink: 0;
}

.logo-text-group {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.logo-text {
  font-size: 1.1rem;
  font-weight: 700;
  color: $apple-text-primary;
  margin: 0;
  letter-spacing: -0.02em;
  font-family: $apple-font-family;
}

.logo-tagline {
  font-size: 0.65rem;
  color: $apple-accent;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-family: $apple-font-family;
}

.nav-menu {
  flex: 1;
  padding: 1rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  position: relative;
  z-index: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.7rem 1rem;
  border-radius: $apple-radius-sm;
  color: $apple-text-tertiary;
  text-decoration: none;
  transition: all 0.2s ease;
  position: relative;
  cursor: pointer;
  font-family: $apple-font-family;

  &:hover {
    background: $apple-sidebar-active-bg;
    color: $apple-text-secondary;

    .nav-icon-wrap {
      background: transparent;
      color: $apple-text-secondary;
    }
  }

  &.active {
    background: $apple-sidebar-active-bg;
    color: $apple-text-primary;

    .nav-icon-wrap {
      background: transparent;
      color: $apple-accent;
    }

    .nav-text {
      font-weight: 600;
      color: $apple-text-primary;
    }

    // 左侧细蓝线指示器 - Apple/Linear风格
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 20px;
      background: $apple-accent;
      border-radius: 0 2px 2px 0;
    }
  }
}

.nav-icon-wrap {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  transition: $transition-all;
  flex-shrink: 0;
}

.nav-icon {
  font-size: 1.1rem;
}

.nav-text {
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  font-family: $apple-font-family;
}

// 移除右侧指示器，改用左侧小蓝点（在 .nav-item.active::before 中实现）

.sidebar-footer {
  padding: $apple-space-4 $apple-space-3;
  border-top: 1px solid $apple-border-light;
  position: relative;
  z-index: 1;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: $apple-radius-sm;
  background: transparent;
  border: none;
  transition: all 0.2s ease;

  &:hover {
    background: $apple-sidebar-active-bg;
  }
}

.user-avatar {
  flex-shrink: 0;
  background: $gradient-primary !important;
  font-weight: 700 !important;
}

.user-details {
  flex: 1;
  overflow: hidden;
  min-width: 0;
}

.user-name {
  font-size: 0.8125rem;
  font-weight: 600;
  color: $apple-text-primary;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: $apple-font-family;
}

.v-badge {
  display: inline-flex;
  width: 16px;
  height: 16px;
  margin-left: 6px;
  border-radius: 50%;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #fff;
  background: #f59e0b;
}

.user-username {
  font-size: 0.7rem;
  color: $apple-text-tertiary;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: $apple-font-family;
}

.logout-btn {
  background: none;
  border: none;
  color: $apple-text-tertiary;
  cursor: pointer;
  padding: $apple-space-3;
  border-radius: $apple-radius-sm;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: $transition-colors;
  flex-shrink: 0;

  &:hover {
    color: $error-color;
    background: rgba(220, 38, 38, 0.08);
  }
}

// ============================================
// Main Content
// ============================================
.main-content {
  flex: 1;
  margin-left: $apple-sidebar-width;
  display: flex;
  flex-direction: column;
  min-height: 100vh;

  @media (max-width: 768px) {
    margin-left: 64px;
  }
}

.main-header {
  height: 72px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  position: sticky;
  top: 0;
  z-index: 5;
}

.header-left {
  flex-shrink: 0;
}

.page-breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.breadcrumb-dot {
  width: 6px;
  height: 6px;
  background: $apple-accent;
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(0, 113, 227, 0.3);
  opacity: 0.8;
}

.breadcrumb-text {
  font-size: $apple-font-body;
  font-weight: 500;
  color: $apple-text-primary;
  letter-spacing: 0.01em;
  font-family: $apple-font-family;
}

.search-bar {
  flex: 1;
  max-width: 420px;
}

.search-inner-wrap {
  position: relative;
}

.search-inner {
  display: flex;
  align-items: center;
  gap: $apple-space-3;
  background: rgba(245, 245, 247, 0.9);
  border: 1px solid $apple-input-border;
  border-radius: 14px;
  padding: $apple-space-3 $apple-space-4;
  transition: all 0.2s ease;
  box-shadow: $apple-shadow-sm;
  font-family: $apple-font-family;

  &:focus-within {
    border-color: $apple-accent;
    background: #FFFFFF;
    box-shadow: 0 0 0 3px $apple-accent-soft;
  }
}

.search-icon {
  color: $apple-text-tertiary;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: $apple-text-primary;
  font-family: $apple-font-family;
  font-size: $apple-font-body;

  &::placeholder {
    color: $apple-text-tertiary;
  }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.notification-btn {
  position: relative;
  background: #FFFFFF;
  border: 1px solid $apple-input-border;
  color: $apple-text-secondary;
  cursor: pointer;
  width: 38px;
  height: 38px;
  border-radius: $apple-input-radius;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: $apple-shadow-sm;

  &:hover {
    background: rgba(0, 0, 0, 0.03);
    color: $apple-accent;
    border-color: $apple-accent;
  }
}

.notif-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: $accent-color;
  color: white;
  font-size: 0.625rem;
  font-weight: 700;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(22, 163, 74, 0.3);
}

.header-avatar {
  :deep(.el-avatar) {
    cursor: pointer;
    border: 2px solid $apple-input-border;
    transition: all 0.2s ease;
    box-shadow: $apple-shadow-sm;

    &:hover {
      border-color: $apple-accent;
      box-shadow: 0 0 0 3px $apple-accent-soft;
    }
  }
}

.page-content {
  flex: 1;
  padding: $apple-space-6;
  overflow-y: auto;
  background: $apple-bg-page;
}

.sidebar-disclaimer {
  padding: $apple-space-3 $apple-space-4;
  border-top: 1px solid $apple-border-light;

  p {
    font-size: $apple-font-mini;
    color: $apple-text-tertiary;
    line-height: 1.5;
    margin: 0;
    font-style: italic;
    font-family: $apple-font-family;
  }

  @media (max-width: 768px) {
    display: none;
  }
}
</style>

