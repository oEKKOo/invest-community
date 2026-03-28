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
import { ref, computed, onMounted, onBeforeUnmount, watch, reactive } from 'vue'
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
import { globalSearch, type GlobalSearchResult } from '../../api/search'
import { getNotificationsStreamUrl } from '../../api/notifications'

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

    // 建立通知 SSE 长连接
    try {
      // 尽量使用 window.__VITE_API_BASE_URL__ 全局变量作为后端接口基地址（在 main.ts 里注入或在 index.html/fallback 全局声明）
      // 若未定义，则回退到 /api
      // @ts-ignore
      const base = (window.__VITE_API_BASE_URL__ as string | undefined) || '/api'
      const url =
        (base.startsWith('http') ? base : `${window.location.origin}${base}`) +
        getNotificationsStreamUrl() +
        `?token=${encodeURIComponent(localStorage.getItem('investhub_token') || '')}`

      notificationEventSource = new EventSource(url)
      notificationEventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data && Array.isArray(data.items)) {
            notificationsStore.applyStreamSnapshot(data)
          }
        } catch {
          // 忽略解析错误
        }
      }
      notificationEventSource.addEventListener('close', () => {
        notificationEventSource?.close()
        notificationEventSource = null
      })
    } catch {
      // SSE 建立失败时静默降级为轮询模式
    }
  }
})

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
      await notificationsStore.fetchNotifications({ page: 1, pageSize: 10 })
      // 登录后再尝试建立 SSE 连接
      if (!notificationEventSource) {
        // 尽量使用 window.__VITE_API_BASE_URL__ 全局变量作为后端接口基地址（在 main.ts 里注入或在 index.html/fallback 全局声明）
        // 若未定义，则回退到 /api
        // @ts-ignore
        const base = (window.__VITE_API_BASE_URL__ as string | undefined) || '/api'
        const url =
          (base.startsWith('http') ? base : `${window.location.origin}${base}`) +
          getNotificationsStreamUrl() +
          `?token=${encodeURIComponent(localStorage.getItem('investhub_token') || '')}`

          notificationEventSource = new EventSource(url)
          notificationEventSource.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data)
              if (data && Array.isArray(data.items)) {
                notificationsStore.applyStreamSnapshot(data)
              }
            } catch {
              // 忽略解析错误
            }
          }
          notificationEventSource.addEventListener('close', () => {
            notificationEventSource?.close()
            notificationEventSource = null
          })
      }
    } else {
      notificationsStore.items = []
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

.search-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: $apple-bg-soft;
  backdrop-filter: $apple-glass-blur;
  -webkit-backdrop-filter: $apple-glass-blur;
  border-radius: $apple-radius-md;
  border: 1px solid $apple-border-light;
  box-shadow: $apple-shadow-lg;
  padding: $apple-space-3;
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

.notif-drawer-body {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.notif-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $apple-space-4;

  h3 {
    margin: 0;
    font-size: $apple-font-body;
    font-weight: 600;
    color: $apple-text-primary;
    font-family: $apple-font-family;
  }
}

.notif-list {
  display: flex;
  flex-direction: column;
  gap: $apple-space-3;
  max-height: 100%;
  overflow-y: auto;
}

.notif-item {
  position: relative;
  padding: $apple-space-4;
  border-radius: $apple-radius-sm;
  border: 1px solid $apple-border-light;
  background: $apple-bg-elevated;
  backdrop-filter: $apple-glass-blur;
  -webkit-backdrop-filter: $apple-glass-blur;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: $apple-accent;
    box-shadow: $apple-shadow-sm;
  }

  &.unread {
    background: rgba(0, 113, 227, 0.04);
    border-color: rgba(0, 113, 227, 0.15);
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
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  font-family: $apple-font-family;
}

.notif-title {
  font-size: $apple-font-body;
  font-weight: 600;
  color: $apple-text-primary;
  font-family: $apple-font-family;
}

.notif-content {
  font-size: $apple-font-body;
  color: $apple-text-secondary;
  font-family: $apple-font-family;
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

