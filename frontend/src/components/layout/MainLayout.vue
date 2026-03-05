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
          <div class="nav-indicator" v-if="route.name === item.name"></div>
        </router-link>
      </nav>

      <!-- 免责声明 -->
      <div class="sidebar-disclaimer">
        <p>数据来源：Finnhub Finance，仅供参考，不构成投资建议</p>
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
            <p class="user-name">{{ authStore.user?.displayName || 'Unknown User' }}</p>
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

            <div
              v-if="showSearchDropdown"
              class="search-dropdown"
            >
              <div class="search-dropdown-section search-primary-action" @mousedown.prevent="handleSearchEnter">
                <span class="primary-label">搜索</span>
                <span class="primary-keyword">“{{ searchQuery }}”</span>
              </div>

              <div v-if="searchLoading" class="search-dropdown-loading">
                正在为你查找相关内容...
              </div>

              <template v-else>
                <div
                  v-if="hotKeywords.length && !searchQuery.trim()"
                  class="search-dropdown-section"
                >
                  <div class="section-title">热门搜索</div>
                  <div class="hot-list">
                    <button
                      v-for="word in hotKeywords"
                      :key="word"
                      class="hot-item"
                      @mousedown.prevent="useHotKeyword(word)"
                    >
                      {{ word }}
                    </button>
                  </div>
                </div>

                <div
                  v-if="searchResults.posts.items.length"
                  class="search-dropdown-section"
                >
                  <div class="section-title">
                    帖子
                    <span class="count">共 {{ searchResults.posts.total }} 条</span>
                  </div>
                  <ul class="suggest-list">
                    <li
                      v-for="post in searchResults.posts.items"
                      :key="post.id"
                      class="suggest-item"
                      @mousedown.prevent="goPost(post.id)"
                    >
                      <div class="suggest-main">
                        <span class="suggest-title">{{ post.title }}</span>
                        <span class="suggest-meta">{{ post.authorName }}</span>
                      </div>
                    </li>
                  </ul>
                </div>

                <div
                  v-if="searchResults.assets.items.length"
                  class="search-dropdown-section"
                >
                  <div class="section-title">
                    资产
                    <span class="count">共 {{ searchResults.assets.total }} 条</span>
                  </div>
                  <ul class="suggest-list">
                    <li
                      v-for="asset in searchResults.assets.items"
                      :key="asset.id"
                      class="suggest-item"
                      @mousedown.prevent="goAsset(asset.id)"
                    >
                      <div class="suggest-main">
                        <span class="suggest-title">{{ asset.code }}</span>
                        <span class="suggest-meta">{{ asset.name }}</span>
                      </div>
                    </li>
                  </ul>
                </div>

                <div
                  v-if="searchResults.portfolios.items.length"
                  class="search-dropdown-section"
                >
                  <div class="section-title">
                    组合
                    <span class="count">共 {{ searchResults.portfolios.total }} 条</span>
                  </div>
                  <ul class="suggest-list">
                    <li
                      v-for="p in searchResults.portfolios.items"
                      :key="p.id"
                      class="suggest-item"
                      @mousedown.prevent="goPortfolio(p.id)"
                    >
                      <div class="suggest-main">
                        <span class="suggest-title">{{ p.title }}</span>
                        <span class="suggest-meta">{{ p.userName }}</span>
                      </div>
                    </li>
                  </ul>
                </div>
              </template>
            </div>
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

      <!-- 通知抽屉 -->
      <el-drawer
        v-model="notificationDrawerVisible"
        title="通知中心"
        size="360px"
        direction="rtl"
      >
        <div class="notif-drawer-body">
          <div class="notif-drawer-header">
            <h3>最新通知</h3>
            <el-button
              v-if="notificationsStore.items.length"
              type="text"
              size="small"
              @click="handleMarkAllRead"
            >
              全部标记已读
            </el-button>
          </div>

          <el-skeleton v-if="notificationsStore.loading" :rows="4" animated />

          <el-empty
            v-else-if="!notificationsStore.items.length"
            description="暂时没有通知"
          />

          <div v-else class="notif-list">
            <div
              v-for="item in notificationsStore.items"
              :key="item.id"
              class="notif-item"
              :class="{ unread: !item.is_read }"
              @click="handleNotificationClick(item)"
            >
              <div class="notif-main">
                <div class="notif-title-row">
                  <span class="notif-tag" :class="`type-${item.notification_type.toLowerCase()}`">
                    {{ getNotificationTypeLabel(item.notification_type) }}
                  </span>
                  <span class="notif-time">{{ formatTime(item.created_at) }}</span>
                </div>
                <div class="notif-title">{{ item.title }}</div>
                <div class="notif-content">{{ item.content }}</div>
              </div>
              <div class="notif-status-dot" v-if="!item.is_read"></div>
            </div>
          </div>
        </div>
      </el-drawer>

      <!-- 页面内容 -->
      <div class="page-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, reactive } from 'vue'
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
  Coin
} from '@element-plus/icons-vue'
import { globalSearch, type GlobalSearchResult } from '../../api/search'

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

const menuItems = computed(() => [
  { name: 'Dashboard', path: '/', label: '市场总览', icon: House },
  { name: 'MarketList', path: '/market', label: '行情列表', icon: DataLine },
  { name: 'Community', path: '/community', label: '社区论坛', icon: UserFilled },
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
    await notificationsStore.fetchNotifications({ page: 1, pageSize: 20 })
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

const handleNotificationClick = async (item: any) => {
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
      router.push({ name: 'Profile', params: { userId: item.related_object_id } })
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const getNotificationTypeLabel = (type: string) => {
  switch (type) {
    case 'LIKE':
      return '点赞'
    case 'COMMENT':
      return '评论'
    case 'FOLLOW':
      return '关注'
    case 'REVIEW_RESULT':
      return '审核'
    case 'SYSTEM':
      return '系统'
    default:
      return '通知'
  }
}

const formatTime = (iso: string) => {
  const d = new Date(iso)
  return `${d.getMonth() + 1}-${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d
    .getMinutes()
    .toString()
    .padStart(2, '0')}`
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
  router.push({ name: 'AssetDetail', params: { assetId: id } })
}

const goPortfolio = (id: number) => {
  router.push({ name: 'PortfolioDetail', params: { id } })
}

onMounted(async () => {
  if (authStore.isLoggedIn) {
    try {
      await notificationsStore.fetchNotifications({ page: 1, pageSize: 10 })
    } catch {
      // 忽略通知加载错误，不影响主功能
    }
  }
})

watch(
  () => authStore.isLoggedIn,
  async (loggedIn) => {
    if (loggedIn) {
      await notificationsStore.fetchNotifications({ page: 1, pageSize: 10 })
    } else {
      notificationsStore.items = []
    }
  }
)
</script>

<style lang="scss" scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: $bg-dark;
}

// ============================================
// Sidebar
// ============================================
.sidebar {
  width: 260px;
  background: #FFFFFF;
  border-right: 1px solid $border-subtle;
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
  padding: 1.5rem 1.25rem 1rem;
  border-bottom: 1px solid $border-subtle;
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
  color: $text-primary;
  margin: 0;
  letter-spacing: -0.02em;
}

.logo-tagline {
  font-size: 0.65rem;
  color: $primary-color;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
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
  border-radius: 10px;
  color: $text-muted;
  text-decoration: none;
  transition: $transition-all;
  position: relative;
  cursor: pointer;

  &:hover {
    background: $bg-surface;
    color: $text-secondary;

    .nav-icon-wrap {
      background: rgba(29, 78, 216, 0.08);
      color: $primary-color;
    }
  }

  &.active {
    background: rgba(29, 78, 216, 0.08);
    color: $primary-color;
    border: 1px solid rgba(29, 78, 216, 0.15);

    .nav-icon-wrap {
      background: rgba(29, 78, 216, 0.12);
      color: $primary-color;
    }

    .nav-text {
      font-weight: 600;
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
}

.nav-indicator {
  position: absolute;
  right: -0.75rem;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: $gradient-primary;
  border-radius: 2px 0 0 2px;
  box-shadow: $glow-blue;
}

.sidebar-footer {
  padding: 1rem 0.75rem;
  border-top: 1px solid $border-subtle;
  position: relative;
  z-index: 1;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: 10px;
  background: $bg-surface;
  border: 1px solid $border-subtle;
  transition: $transition-all;

  &:hover {
    background: $bg-dark;
    border-color: $border-default;
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
  color: $text-primary;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-username {
  font-size: 0.7rem;
  color: $text-muted;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  background: none;
  border: none;
  color: $text-muted;
  cursor: pointer;
  padding: 0.375rem;
  border-radius: 6px;
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
  margin-left: 260px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;

  @media (max-width: 768px) {
    margin-left: 64px;
  }
}

.main-header {
  height: 64px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid $border-subtle;
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  position: sticky;
  top: 0;
  z-index: 5;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
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
  width: 7px;
  height: 7px;
  background: $primary-color;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(29, 78, 216, 0.5);
}

.breadcrumb-text {
  font-size: 0.875rem;
  font-weight: 600;
  color: $text-primary;
  letter-spacing: 0.01em;
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
  gap: 0.625rem;
  background: $bg-surface;
  border: 1px solid $border-default;
  border-radius: 10px;
  padding: 0.5rem 1rem;
  transition: $transition-all;
  box-shadow: $shadow-sm;

  &:focus-within {
    border-color: $primary-color;
    background: #FFFFFF;
    box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.12);
  }
}

.search-icon {
  color: $text-muted;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: $text-primary;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;

  &::placeholder {
    color: $text-muted;
  }
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid $border-subtle;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
  padding: 0.4rem 0.5rem;
  z-index: 20;
}

.search-dropdown-section {
  padding: 0.35rem 0.25rem;

  & + & {
    border-top: 1px solid #f3f4f6;
  }
}

.search-primary-action {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    background: #f3f4ff;
  }
}

.primary-label {
  font-size: 0.78rem;
  color: #6b7280;
}

.primary-keyword {
  font-size: 0.8rem;
  color: #111827;
  font-weight: 500;
}

.search-dropdown-loading {
  padding: 0.4rem 0.6rem;
  font-size: 0.78rem;
  color: #9ca3af;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.78rem;
  color: #6b7280;
  margin-bottom: 0.25rem;

  .count {
    font-size: 0.72rem;
    color: #9ca3af;
  }
}

.hot-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.hot-item {
  border-radius: 999px;
  border: none;
  padding: 0.12rem 0.6rem;
  font-size: 0.78rem;
  background: #f3f4f6;
  color: #4b5563;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    background: #e5e7eb;
  }
}

.suggest-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.suggest-item {
  padding: 0.3rem 0.4rem;
  border-radius: 6px;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    background: #f3f4ff;
  }
}

.suggest-main {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}

.suggest-title {
  font-size: 0.8rem;
  color: #111827;
  font-weight: 500;
}

.suggest-meta {
  font-size: 0.72rem;
  color: #9ca3af;
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
  border: 1px solid $border-default;
  color: $text-secondary;
  cursor: pointer;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: $transition-all;
  box-shadow: $shadow-sm;

  &:hover {
    background: $bg-surface;
    color: $primary-color;
    border-color: $primary-color;
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
    border: 2px solid $border-default;
    transition: $transition-all;
    box-shadow: $shadow-sm;

    &:hover {
      border-color: $primary-color;
      box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.12);
    }
  }
}

.page-content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

.notif-drawer-body {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.notif-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;

  h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: $text-primary;
  }
}

.notif-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 100%;
  overflow-y: auto;
}

.notif-item {
  position: relative;
  padding: 0.75rem 0.75rem;
  border-radius: 8px;
  border: 1px solid $border-subtle;
  background: #fff;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    border-color: $primary-color;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
  }

  &.unread {
    background: rgba(37, 99, 235, 0.04);
    border-color: rgba(37, 99, 235, 0.18);
  }
}

.notif-main {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.notif-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.15rem;
}

.notif-tag {
  font-size: 0.675rem;
  padding: 2px 6px;
  border-radius: 999px;
  font-weight: 600;
}

.notif-tag.type-like {
  background: rgba(249, 115, 22, 0.08);
  color: #ea580c;
}

.notif-tag.type-comment {
  background: rgba(59, 130, 246, 0.08);
  color: #2563eb;
}

.notif-tag.type-follow {
  background: rgba(16, 185, 129, 0.08);
  color: #059669;
}

.notif-tag.type-review_result {
  background: rgba(234, 179, 8, 0.08);
  color: #ca8a04;
}

.notif-tag.type-system {
  background: rgba(148, 163, 184, 0.12);
  color: #4b5563;
}

.notif-time {
  font-size: 0.7rem;
  color: $text-muted;
}

.notif-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: $text-primary;
}

.notif-content {
  font-size: 0.8rem;
  color: $text-secondary;
}

.notif-status-dot {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: $accent-color;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.25);
}

.sidebar-disclaimer {
  padding: 0.625rem 1rem;
  border-top: 1px solid $border-subtle;

  p {
    font-size: 0.6rem;
    color: $text-muted;
    line-height: 1.5;
    margin: 0;
    font-style: italic;
  }

  @media (max-width: 768px) {
    display: none;
  }
}
</style>

