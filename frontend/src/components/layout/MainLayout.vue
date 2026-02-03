<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">IH</div>
          <h1 class="logo-text">InvestHub</h1>
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
          <el-icon class="nav-icon">
            <component :is="item.icon" />
          </el-icon>
          <span class="nav-text">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info" v-if="authStore.user">
          <el-avatar 
            :src="authStore.user?.avatar || ''" 
            :size="40"
            class="user-avatar"
          >
            {{ authStore.user?.displayName?.[0] || 'U' }}
          </el-avatar>
          <div class="user-details">
            <p class="user-name">{{ authStore.user?.displayName || 'Unknown User' }}</p>
            <p class="user-username">@{{ authStore.user?.username || 'unknown' }}</p>
          </div>
          <el-button 
            type="text" 
            @click="handleLogout"
            class="logout-btn"
          >
            <el-icon><SwitchButton /></el-icon>
          </el-button>
        </div>
      </div>
    </aside>

    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 顶部导航栏 -->
      <header class="main-header">
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="Search discussions, funds, portfolios..."
            class="search-input"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="header-actions">
          <el-button 
            type="text" 
            class="notification-btn"
            @click="showNotifications"
          >
            <el-badge :value="unreadCount" :hidden="!unreadCount">
              <el-icon><Bell /></el-icon>
            </el-badge>
          </el-button>
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
  User,
  Search,
  Bell,
  SwitchButton
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const searchQuery = ref('')
const unreadCount = ref(0) // TODO: 连接到通知store

const menuItems = computed(() => [
  { name: 'Dashboard', path: '/', label: 'Dashboard', icon: House },
  { name: 'Community', path: '/community', label: 'Community', icon: UserFilled },
  { name: 'Portfolios', path: '/portfolios', label: 'Portfolios', icon: TrendCharts },
  ...(authStore.isAdmin ? [{ name: 'AdminPanel', path: '/admin', label: 'Admin Panel', icon: Setting }] : []),
  { name: 'Profile', path: '/profile', label: 'My Profile', icon: User }
])

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
  // TODO: 显示通知弹窗
  console.log('Show notifications')
}
</script>

<style lang="scss" scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background-color: #f9fafb;
}

.sidebar {
  width: 256px;
  background: white;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  overflow-y: auto;
  z-index: 10;

  @media (max-width: 768px) {
    width: 64px;
    
    .logo-text,
    .nav-text {
      display: none;
    }
    
    .sidebar-footer {
      display: none;
    }
  }
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid #f3f4f6;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logo-icon {
  width: 2rem;
  height: 2rem;
  background: #2563eb;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 0.875rem;
}

.logo-text {
  font-size: 1.25rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0;
}

.nav-menu {
  flex: 1;
  padding: 1rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  margin-bottom: 0.25rem;
  border-radius: 0.5rem;
  color: #6b7280;
  text-decoration: none;
  transition: all 0.2s ease-in-out;

  &:hover {
    background: #f3f4f6;
    color: #374151;
  }

  &.active {
    background: #eff6ff;
    color: #2563eb;
  }
}

.nav-icon {
  font-size: 1.25rem;
}

.nav-text {
  font-weight: 500;
  font-size: 0.875rem;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid #f3f4f6;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-details {
  flex: 1;
  overflow: hidden;
}

.user-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-username {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  color: #6b7280;
  
  &:hover {
    color: #ef4444;
  }
}

.main-content {
  flex: 1;
  margin-left: 256px;
  display: flex;
  flex-direction: column;

  @media (max-width: 768px) {
    margin-left: 64px;
  }
}

.main-header {
  height: 64px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 5;
}

.search-bar {
  flex: 1;
  max-width: 400px;
}

.search-input {
  :deep(.el-input__wrapper) {
    background: #f3f4f6;
    border: none;
    border-radius: 0.5rem;
    transition: all 0.2s ease-in-out;

    &:hover,
    &.is-focus {
      background: white;
      box-shadow: 0 0 0 2px #2563eb;
    }
  }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.notification-btn {
  color: #6b7280;
  font-size: 1.25rem;
  
  &:hover {
    color: #374151;
  }
}

.page-content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}
</style>