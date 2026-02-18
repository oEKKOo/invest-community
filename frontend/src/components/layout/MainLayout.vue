<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
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

    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 顶部导航栏 -->
      <header class="main-header">
        <div class="header-left">
          <div class="page-breadcrumb">
            <span class="breadcrumb-dot"></span>
            <span class="breadcrumb-text">{{ currentPageLabel }}</span>
          </div>
        </div>
        <div class="search-bar">
          <div class="search-inner">
            <svg class="search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
              <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <input
              v-model="searchQuery"
              placeholder="搜索讨论、基金、组合..."
              class="search-input"
            />
          </div>
        </div>
        <div class="header-actions">
          <button 
            class="notification-btn"
            @click="showNotifications"
            title="通知"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M13.73 21a2 2 0 01-3.46 0" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="notif-badge" v-if="unreadCount">{{ unreadCount }}</span>
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

      <!-- 页面内容 -->
      <div class="page-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { ElMessage } from 'element-plus'
import {
  House,
  UserFilled,
  TrendCharts,
  Setting,
  User
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const searchQuery = ref('')
const unreadCount = ref(0)

const menuItems = computed(() => [
  { name: 'Dashboard', path: '/', label: '市场总览', icon: House },
  { name: 'Community', path: '/community', label: '社区论坛', icon: UserFilled },
  { name: 'Portfolios', path: '/portfolios', label: '投资组合', icon: TrendCharts },
  ...(authStore.isAdmin ? [{ name: 'AdminPanel', path: '/admin', label: '管理后台', icon: Setting }] : []),
  { name: 'Profile', path: '/profile', label: '我的主页', icon: User }
])

const currentPageLabel = computed(() => {
  const item = menuItems.value.find(m => m.name === route.name)
  return item?.label || 'InvestHub'
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

const showNotifications = () => {
  console.log('Show notifications')
}
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
  background: rgba(10, 14, 26, 0.95);
  border-right: 1px solid $border-subtle;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  overflow-y: auto;
  z-index: 10;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);

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
  height: 200px;
  background: radial-gradient(ellipse at 50% 0%, rgba(124, 58, 237, 0.15) 0%, transparent 70%);
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
  box-shadow: $shadow-purple;
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
  color: $primary-light;
  font-weight: 500;
  letter-spacing: 0.05em;
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
  padding: 0.75rem 1rem;
  border-radius: 10px;
  color: $text-muted;
  text-decoration: none;
  transition: $transition-all;
  position: relative;
  cursor: pointer;

  &:hover {
    background: rgba(255, 255, 255, 0.06);
    color: $text-secondary;

    .nav-icon-wrap {
      background: rgba(124, 58, 237, 0.15);
    }
  }

  &.active {
    background: rgba(124, 58, 237, 0.12);
    color: $primary-light;
    border: 1px solid rgba(124, 58, 237, 0.2);

    .nav-icon-wrap {
      background: rgba(124, 58, 237, 0.25);
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
  box-shadow: $glow-purple;
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
  background: $glass-bg;
  border: 1px solid $border-subtle;
  transition: $transition-all;

  &:hover {
    background: $glass-bg-hover;
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
  padding: 0.25rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: $transition-colors;
  flex-shrink: 0;

  &:hover {
    color: $error-color;
    background: rgba(239, 68, 68, 0.1);
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
  background: rgba(10, 14, 26, 0.8);
  border-bottom: 1px solid $border-subtle;
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  position: sticky;
  top: 0;
  z-index: 5;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
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
  background: $primary-light;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(167, 139, 250, 0.8);
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

.search-inner {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid $border-subtle;
  border-radius: 10px;
  padding: 0.5rem 1rem;
  transition: $transition-all;

  &:focus-within {
    border-color: $primary-color;
    background: rgba(255, 255, 255, 0.07);
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15);
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
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.875rem;

  &::placeholder {
    color: $text-muted;
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
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid $border-subtle;
  color: $text-secondary;
  cursor: pointer;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: $transition-all;

  &:hover {
    background: rgba(255, 255, 255, 0.08);
    color: $text-primary;
    border-color: $border-default;
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
}

.header-avatar {
  :deep(.el-avatar) {
    cursor: pointer;
    border: 2px solid $border-default;
    transition: $transition-all;

    &:hover {
      border-color: $primary-light;
    }
  }
}

.page-content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}
</style>
