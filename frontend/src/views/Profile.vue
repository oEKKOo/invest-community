<template>
  <div class="profile">
    <!-- 用户资料卡片 -->
    <div class="profile-header">
      <div class="profile-card">
        <div class="profile-avatar">
          <el-avatar 
            :src="displayUser?.avatar || authStore.user?.avatar" 
            :size="128"
            class="user-avatar"
          >
            {{ displayUser?.displayName?.[0] || authStore.user?.displayName?.[0] }}
          </el-avatar>
        </div>
        
        <div class="profile-info">
          <div class="profile-main">
            <div class="user-identity">
              <h2 class="user-name">{{ displayUser?.displayName || authStore.user?.displayName }}</h2>
              <el-tag 
                :type="getRoleType(displayUser?.role || authStore.user?.role)"
                class="user-role-tag"
              >
                {{ getRoleText(displayUser?.role || authStore.user?.role) }}
              </el-tag>
            </div>
            <p class="username">@{{ displayUser?.username || authStore.user?.username }}</p>
            <p class="user-bio">{{ displayUser?.bio || authStore.user?.bio || '这个人很懒，还没有填写个人简介' }}</p>
            
            <div class="user-stats">
              <div class="stat-item clickable" @click="openFollowDrawer('followers')">
                <span class="stat-value">{{ displayUser?.followers || authStore.user?.followers || 0 }}</span>
                <span class="stat-label">关注者</span>
              </div>
              <div class="stat-item clickable" @click="openFollowDrawer('following')">
                <span class="stat-value">{{ displayUser?.following || authStore.user?.following || 0 }}</span>
                <span class="stat-label">关注数</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ userPosts.length }}</span>
                <span class="stat-label">帖子</span>
              </div>
            </div>
          </div>
        </div>

        <div class="profile-actions">
          <template v-if="isSelf">
            <el-button 
              type="primary" 
              plain
              @click="showEditProfile = true"
            >
              编辑资料
            </el-button>
          </template>
          <template v-else>
            <el-button 
              :type="isFollowing ? 'default' : 'primary'"
              :plain="isFollowing"
              @click="toggleFollow"
            >
              {{ isFollowing ? '已关注' : '关注' }}
            </el-button>
            <el-button 
              type="danger" 
              plain
              @click="openReportUserDialog"
            >
              <el-icon><Warning /></el-icon>
              举报用户
            </el-button>
          </template>
        </div>
      </div>
    </div>

    <div class="profile-content" :class="{ 'no-sidebar': !isSelf }">
      <!-- 左侧：账户设置+ 点赞收藏概览（仅在自己的主页展示） -->
      <aside v-if="isSelf" class="profile-sidebar">
        <div v-if="isSelf" class="settings-card">
          <h3 class="card-title">账户与安全</h3>
          <ul class="settings-list">
            <li class="setting-item">
              <span class="setting-label">邮箱验证</span>
              <span class="setting-value verified">已验证</span>
            </li>
            <li class="setting-item">
              <span class="setting-label">两步验证</span>
              <el-button type="text" size="small">启用</el-button>
            </li>
            <li class="setting-item">
              <span class="setting-label">账户类型</span>
              <span class="setting-value">专业版</span>
            </li>
          </ul>
        </div>

        <!-- 点赞 & 收藏概览卡片 -->
        <div class="activity-overview-card">
          <h3 class="card-title">我的互动</h3>

          <!-- 点赞概览 -->
          <div
            class="overview-item"
            @click="openDrawer('likes')"
          >
            <div class="overview-icon likes-icon">
              <el-icon><Star /></el-icon>
            </div>
            <div class="overview-info">
              <div class="overview-label">我的点赞</div>
              <div class="overview-meta">
                <template v-if="likesLoading">
                  <el-skeleton-item variant="text" style="width: 60px" />
                </template>
                <template v-else-if="likeRecords.length > 0">
                  <span class="overview-count">{{ likesTotal }} 条记录</span>
                  <!-- 最新3条预览-->
                  <div class="overview-preview">
                    <el-tag
                      v-for="item in likeRecords.slice(0, 3)"
                      :key="item.id"
                      size="small"
                      :type="getLikeTagType(item.targetType)"
                      class="preview-tag"
                    >
                      {{ getLikePreviewText(item) }}
                    </el-tag>
                  </div>
                </template>
                <span v-else class="overview-empty">暂无点赞记录</span>
              </div>
            </div>
            <el-icon class="overview-arrow"><ArrowRight /></el-icon>
          </div>

          <div class="overview-divider" />

          <!-- 收藏概览 -->
          <div
            class="overview-item"
            @click="openDrawer('favorites')"
          >
            <div class="overview-icon favorites-icon">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="overview-info">
              <div class="overview-label">我的收藏</div>
              <div class="overview-meta">
                <template v-if="favoritesLoading">
                  <el-skeleton-item variant="text" style="width: 60px" />
                </template>
                <template v-else-if="favoriteRecords.length > 0">
                  <span class="overview-count">{{ favoritesTotal }} 篇帖子</span>
                  <div class="overview-preview">
                    <el-tag
                      v-for="item in favoriteRecords.slice(0, 3)"
                      :key="item.id"
                      size="small"
                      type="warning"
                      class="preview-tag"
                    >
                      {{ item.title }}
                    </el-tag>
                  </div>
                </template>
                <span v-else class="overview-empty">暂无收藏记录</span>
              </div>
            </div>
            <el-icon class="overview-arrow"><ArrowRight /></el-icon>
          </div>
        </div>

        <div class="invite-card">
          <h4 class="invite-title">邀请好友</h4>
          <p class="invite-subtitle">每成功邀请一位好友，获得3个月高级分析功能</p>
          <el-button 
            type="primary" 
            class="invite-btn"
            @click="copyInviteLink"
          >
            复制邀请链接
          </el-button>
        </div>
      </aside>

      <!-- 右侧：活动记录-->
      <main class="profile-main-content">
        <h3 class="section-title">{{ isSelf ? '最近活动' : 'TA 的最近发帖' }}</h3>
        
        <div v-if="loading" class="loading-container">
          <div v-for="i in 3" :key="i" class="activity-skeleton">
            <el-skeleton :rows="3" animated />
          </div>
        </div>

        <div v-else-if="userPosts.length === 0" class="empty-activity">
          <el-empty 
            description="还没有发布任何内容"
            :image-size="120"
          >
            <el-button 
              type="primary" 
              @click="$router.push('/community')"
            >
              发表第一篇帖子
            </el-button>
          </el-empty>
        </div>

        <div v-else class="activity-list">
          <div 
            v-for="post in userPosts"
            :key="post.id"
            class="activity-card"
            @click="$router.push(`/posts/${post.id}`)"
          >
            <div class="activity-header">
              <el-tag 
                :type="getStatusType(post.status)"
                size="small"
                class="status-tag"
              >
                {{ getStatusText(post.status) }}
              </el-tag>
              <span class="activity-date">{{ formatDate(post.createdAt) }}</span>
            </div>

            <h4 class="activity-title">{{ post.title }}</h4>
            <p class="activity-content">{{ post.content }}</p>

            <div class="activity-stats">
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
      </main>
    </div>

    <!-- 编辑资料对话框-->
    <el-dialog
      v-model="showEditProfile"
      title="编辑个人资料"
      width="500px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="80px"
      >
        <el-form-item label="显示昵称" prop="displayName">
          <el-input
            v-model="editForm.displayName"
            placeholder="请输入显示昵称"
          />
        </el-form-item>

        <el-form-item label="个人简介" prop="bio">
          <el-input
            v-model="editForm.bio"
            type="textarea"
            :rows="4"
            placeholder="简单介绍一下你自己..."
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="头像链接" prop="avatar">
          <el-input
            v-model="editForm.avatar"
            placeholder="请输入头像URL"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditProfile = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleUpdateProfile"
            :loading="updating"
          >
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 点赞 / 收藏详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="drawerType === 'likes' ? '我的点赞记录' : '我的收藏记录'"
      direction="rtl"
      size="480px"
      destroy-on-close
    >
      <!-- 点赞详情 -->
      <template v-if="drawerType === 'likes'">
        <div v-if="likesLoading" class="drawer-loading">
          <el-skeleton :rows="5" animated />
        </div>
        <div v-else-if="allLikeRecords.length === 0" class="drawer-empty">
          <el-empty description="暂无点赞记录" :image-size="100" />
        </div>
        <div v-else class="drawer-list">
          <div
            v-for="item in allLikeRecords"
            :key="item.id"
            class="drawer-item"
            :class="{ clickable: item.target }"
            @click="navigateLikeTarget(item)"
          >
            <div class="drawer-item-left">
              <el-tag
                :type="getLikeTagType(item.targetType)"
                size="small"
                class="type-tag"
              >
                {{ getLikeTypeText(item.targetType) }}
              </el-tag>
              <div class="drawer-item-content">
                <p class="drawer-item-title">{{ getLikeDisplayTitle(item) }}</p>
                <p v-if="item.targetType === 'COMMENT' && item.target?.postTitle" class="drawer-item-sub">
                  来自帖子：{{ item.target.postTitle }}
                </p>
                <p class="drawer-item-author" v-if="item.target?.authorName || item.target?.ownerName">
                  {{ item.target?.authorName || item.target?.ownerName }}
                </p>
              </div>
            </div>
            <div class="drawer-item-right">
              <span class="drawer-item-date">{{ formatDate(item.createdAt) }}</span>
              <el-icon v-if="item.target" class="drawer-item-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
        <!-- 加载更多 -->
        <div v-if="likesHasMore" class="drawer-load-more">
          <el-button
            text
            :loading="likesLoadingMore"
            @click="loadMoreLikes"
          >
            加载更多
          </el-button>
        </div>
      </template>

      <!-- 收藏详情 -->
      <template v-if="drawerType === 'favorites'">
        <div v-if="favoritesLoading" class="drawer-loading">
          <el-skeleton :rows="5" animated />
        </div>
        <div v-else-if="allFavoriteRecords.length === 0" class="drawer-empty">
          <el-empty description="暂无收藏记录" :image-size="100" />
        </div>
        <div v-else class="drawer-list">
          <div
            v-for="item in allFavoriteRecords"
            :key="item.id"
            class="drawer-item clickable"
            @click="$router.push(`/posts/${item.id}`)"
          >
            <div class="drawer-item-left">
              <el-tag type="warning" size="small" class="type-tag">帖子</el-tag>
              <div class="drawer-item-content">
                <p class="drawer-item-title">{{ item.title }}</p>
                <p class="drawer-item-author">{{ item.authorName }}</p>
              </div>
            </div>
            <div class="drawer-item-right">
              <div class="drawer-item-stats">
                <span><el-icon><Star /></el-icon> {{ item.likes }}</span>
                <span><el-icon><ChatLineRound /></el-icon> {{ item.comments }}</span>
              </div>
              <span class="drawer-item-date">{{ formatDate(item.createdAt) }}</span>
              <el-icon class="drawer-item-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
        <!-- 加载更多 -->
        <div v-if="favoritesHasMore" class="drawer-load-more">
          <el-button
            text
            :loading="favoritesLoadingMore"
            @click="loadMoreFavorites"
          >
            加载更多
          </el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 粉丝/关注列表抽屉 -->
    <el-drawer
      v-model="followDrawerVisible"
      :title="followDrawerType === 'followers' ? '关注者' : '关注数'"
      direction="rtl"
      size="480px"
      destroy-on-close
    >
      <div v-if="followListLoading" class="drawer-loading">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="followList.length === 0" class="drawer-empty">
        <el-empty 
          :description="followDrawerType === 'followers' ? '暂无关注者' : '暂无关注'" 
          :image-size="100" 
        />
      </div>
      <div v-else class="follow-list">
        <div
          v-for="item in followList"
          :key="getFollowItemId(item)"
          class="follow-item"
        >
          <div 
            class="follow-item-content clickable"
            @click="navigateToUser(getFollowUser(item))"
          >
            <el-avatar 
              :src="getFollowUser(item).avatar" 
              :size="48"
              class="follow-avatar"
            >
              {{ getFollowUser(item).displayName?.[0] }}
            </el-avatar>
            <div class="follow-info">
              <div class="follow-name-row">
                <span class="follow-name">{{ getFollowUser(item).displayName }}</span>
                <el-tag 
                  v-if="getFollowUser(item).role === 'ADMIN'"
                  type="danger"
                  size="small"
                  class="follow-role-tag"
                >
                  管理员
                </el-tag>
                <el-tag 
                  v-else-if="getFollowUser(item).role === 'MODERATOR'"
                  type="warning"
                  size="small"
                  class="follow-role-tag"
                >
                  版主
                </el-tag>
              </div>
              <p class="follow-username">@{{ getFollowUser(item).username }}</p>
              <p class="follow-stats">
                <span>{{ getFollowUser(item).followers || 0 }} 关注者</span>
                <span class="follow-stats-sep">·</span>
                <span>{{ getFollowUser(item).following || 0 }} 关注</span>
              </p>
            </div>
          </div>
          <!-- 快速取关按钮（仅在自己的主页的关注列表中显示） -->
          <div v-if="isSelf && followDrawerType === 'following'" class="follow-action">
            <el-button
              size="small"
              type="danger"
              plain
              :loading="unfollowingIds.has(getFollowUser(item).id)"
              @click.stop="handleUnfollow(getFollowUser(item))"
            >
              取关
            </el-button>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 举报用户对话框 -->
    <ReportDialog
      v-model="showReportDialog"
      target-type="USER"
      :target-id="reportTargetUserId || 0"
      :target-summary="reportTargetUserSummary"
      @submitted="handleReportSubmitted"
    />
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { usePostsStore } from '../stores/posts'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { PostStatus, LikeRecord, Post } from '../types'
import {
  Star,
  ChatLineRound,
  Collection,
  ArrowRight,
  Warning
} from '@element-plus/icons-vue'
import ReportDialog from '@/components/ReportDialog.vue'
import dayjs from 'dayjs'
import { getMyLikes } from '@/api/likes'
import { getMyFavorites } from '@/api/posts'
import type { User } from '@/types'
import { getUserFollowers, getUserFollowing, unfollowUser, type UserFollowItem } from '@/api/users'
import { updateCurrentUser } from '@/api/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const postsStore = usePostsStore()

// ──────────── 基础状态────────────
const loading = ref(false)
const showEditProfile = ref(false)
const updating = ref(false)

const editFormRef = ref<FormInstance>()
const editForm = ref({ displayName: '', bio: '', avatar: '' })

const editRules: FormRules = {
  displayName: [
    { required: true, message: '请输入显示昵称', trigger: 'blur' },
    { min: 2, max: 50, message: '昵称长度应在2-50字符之间', trigger: 'blur' }
  ],
  bio: [{ max: 200, message: '个人简介不能超过200字符', trigger: 'blur' }]
}

// ──────────── 点赞记录 ────────────
const likeRecords = ref<LikeRecord[]>([])    // 概览用（前几条）
const allLikeRecords = ref<LikeRecord[]>([]) // 抽屉完整列表
const likesTotal = ref(0)
const likesLoading = ref(false)
const likesLoadingMore = ref(false)
const likesPage = ref(1)
const LIKES_PAGE_SIZE = 20
const likesHasMore = computed(() => allLikeRecords.value.length < likesTotal.value)

const fetchLikesPreview = async () => {
  likesLoading.value = true
  try {
    const res = await getMyLikes({ page: 1, pageSize: 5 })
    likeRecords.value = res.items
    likesTotal.value = res.total
  } catch {
    // 静默失败，不影响页面
  } finally {
    likesLoading.value = false
  }
}

const fetchAllLikes = async (reset = false) => {
  if (reset) {
    likesPage.value = 1
    allLikeRecords.value = []
    likesLoading.value = true
  } else {
    likesLoadingMore.value = true
  }
  try {
    const res = await getMyLikes({ page: likesPage.value, pageSize: LIKES_PAGE_SIZE })
    likesTotal.value = res.total
    allLikeRecords.value = reset ? res.items : [...allLikeRecords.value, ...res.items]
  } catch {
    ElMessage.error('获取点赞记录失败')
  } finally {
    likesLoading.value = false
    likesLoadingMore.value = false
  }
}

const loadMoreLikes = async () => {
  likesPage.value++
  await fetchAllLikes(false)
}

// ──────────── 收藏记录 ────────────
const favoriteRecords = ref<Post[]>([])    // 概览前几条
const allFavoriteRecords = ref<Post[]>([]) // 抽屉完整列表
const favoritesTotal = ref(0)
const favoritesLoading = ref(false)
const favoritesLoadingMore = ref(false)
const favoritesPage = ref(1)
const FAVS_PAGE_SIZE = 20
const favoritesHasMore = computed(() => allFavoriteRecords.value.length < favoritesTotal.value)

const fetchFavoritesPreview = async () => {
  favoritesLoading.value = true
  try {
    const res = await getMyFavorites({ page: 1, pageSize: 5 })
    favoriteRecords.value = res.items
    favoritesTotal.value = res.total
  } catch {
    // 静默失败
  } finally {
    favoritesLoading.value = false
  }
}

const fetchAllFavorites = async (reset = false) => {
  if (reset) {
    favoritesPage.value = 1
    allFavoriteRecords.value = []
    favoritesLoading.value = true
  } else {
    favoritesLoadingMore.value = true
  }
  try {
    const res = await getMyFavorites({ page: favoritesPage.value, pageSize: FAVS_PAGE_SIZE })
    favoritesTotal.value = res.total
    allFavoriteRecords.value = reset ? res.items : [...allFavoriteRecords.value, ...res.items]
  } catch {
    ElMessage.error('获取收藏记录失败')
  } finally {
    favoritesLoading.value = false
    favoritesLoadingMore.value = false
  }
}

const loadMoreFavorites = async () => {
  favoritesPage.value++
  await fetchAllFavorites(false)
}

// ──────────── 关注 / 粉丝相关（他人主页）────────────
const displayUser = ref<User | null>(null)
const isSelf = computed(() => {
  const paramId = route.params.userId
  if (!paramId) return true
  return Number(paramId) === authStore.user?.id
})

const targetUserId = computed<number | null>(() => {
  const paramId = route.params.userId
  if (paramId) {
    return Number(paramId)
  }
  return authStore.user?.id ?? null
})

const isFollowing = ref(false)

const fetchDisplayUser = async () => {
  // 未传 userId 时显示当前登录用户
  if (!route.params.userId) {
    displayUser.value = authStore.user
    return
  }

  try {
    const userId = Number(route.params.userId)
    const res = await fetch(`/api/users/${userId}/`, {
      headers: {
        Authorization: authStore.token ? `Bearer ${authStore.token}` : ''
      }
    })
    const data = await res.json()
    if (data.code === 0) {
      const d = data.data
      displayUser.value = {
        id: d.id,
        username: d.username,
        displayName: d.display_name,
        avatar: d.avatar_url,
        role: (d.role || 'USER') as User['role'],
        bio: d.bio,
        followers: d.followers_count,
        following: d.following_count,
        created_at: d.created_at
      }
    }
  } catch {
    // 忽略错误，保持空状态
  }
}

const toggleFollow = async () => {
  if (!displayUser.value || !authStore.isLoggedIn) return
  const userId = displayUser.value.id
  const method = isFollowing.value ? 'DELETE' : 'POST'
  try {
    const res = await fetch(`/api/users/${userId}/follow/`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: authStore.token ? `Bearer ${authStore.token}` : ''
      }
    })
    const data = await res.json()
    if (data.code === 0) {
      isFollowing.value = !isFollowing.value
      if (displayUser.value) {
        displayUser.value.followers += isFollowing.value ? 1 : -1
      }
      ElMessage.success(isFollowing.value ? '关注成功' : '已取消关注')
    } else {
      ElMessage.error(data.message || '操作失败')
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

// ──────────── 抽屉 ────────────
const drawerVisible = ref(false)
const drawerType = ref<'likes' | 'favorites'>('likes')

const openDrawer = async (type: 'likes' | 'favorites') => {
  drawerType.value = type
  drawerVisible.value = true
  if (type === 'likes') {
    await fetchAllLikes(true)
  } else {
    await fetchAllFavorites(true)
  }
}

// ──────────── 粉丝/关注列表抽屉 ────────────
const followDrawerVisible = ref(false)
const followDrawerType = ref<'followers' | 'following'>('followers')
const followList = ref<UserFollowItem[]>([])
const followListLoading = ref(false)
const unfollowingIds = ref<Set<number>>(new Set())

const openFollowDrawer = async (type: 'followers' | 'following') => {
  followDrawerType.value = type
  followDrawerVisible.value = true
  await fetchFollowList(type)
}

const fetchFollowList = async (type: 'followers' | 'following') => {
  const targetUserId = displayUser.value?.id || authStore.user?.id
  if (!targetUserId) return

  followListLoading.value = true
  try {
    const data = type === 'followers' 
      ? await getUserFollowers(targetUserId)
      : await getUserFollowing(targetUserId)
    
    // 转换后端数据格式到前端格式
    followList.value = data.map((item: any) => {
      const user = type === 'followers' ? item.follower : item.followee
      const transformedUser = user ? {
        id: user.id,
        username: user.username,
        displayName: user.display_name || user.username,
        avatar: user.avatar_url || '',
        role: (user.role || 'USER') as 'USER' | 'MODERATOR' | 'ADMIN',
        bio: user.bio || '',
        followers: user.followers_count || 0,
        following: user.following_count || 0,
        created_at: user.created_at
      } : null
      
      return {
        ...item,
        follower: type === 'followers' ? transformedUser : item.follower,
        followee: type === 'following' ? transformedUser : item.followee
      }
    })
  } catch (error) {
    ElMessage.error(type === 'followers' ? '获取关注者列表失败' : '获取关注列表失败')
    followList.value = []
  } finally {
    followListLoading.value = false
  }
}

// 获取关注项中的用户（粉丝列表返回 follower，关注列表返回 followee）
const getFollowUser = (item: UserFollowItem): User => {
  return followDrawerType.value === 'followers' ? item.follower : item.followee
}

// 获取关注项的唯一ID
const getFollowItemId = (item: UserFollowItem): number => {
  const user = getFollowUser(item)
  return user.id
}

// 导航到用户主页
const navigateToUser = (user: User) => {
  // 统一使用 UserProfile 路由，支持查看他人主页
  router.push({ name: 'UserProfile', params: { userId: user.id } })
}

// 快速取关
const handleUnfollow = async (user: User) => {
  if (unfollowingIds.value.has(user.id)) return
  
  try {
    unfollowingIds.value.add(user.id)
    await unfollowUser(user.id)
    
    // 从列表中移除
    followList.value = followList.value.filter(item => getFollowUser(item).id !== user.id)
    
    // 更新关注数
    if (displayUser.value) {
      displayUser.value.following = Math.max(0, (displayUser.value.following || 0) - 1)
    } else if (authStore.user) {
      authStore.user.following = Math.max(0, (authStore.user.following || 0) - 1)
    }
    
    ElMessage.success('已取消关注')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.message || '取关失败')
  } finally {
    unfollowingIds.value.delete(user.id)
  }
}

// ──────────── 用户帖子 ────────────
const userPosts = computed(() => {
  if (!targetUserId.value) return []
  return postsStore.posts.filter(post => post.authorId === targetUserId.value)
})

const fetchUserPosts = async () => {
  const uid = targetUserId.value
  if (!uid) return
  loading.value = true
  try {
    await postsStore.fetchPosts({ authorId: uid, sort: 'new' })
  } catch {
    ElMessage.error('获取用户帖子失败')
  } finally {
    loading.value = false
  }
}

// ──────────── 编辑资料 ────────────
const handleUpdateProfile = async () => {
  if (!editFormRef.value) return
  try {
    await editFormRef.value.validate()
    updating.value = true

    await updateCurrentUser({
      displayName: editForm.value.displayName,
      bio: editForm.value.bio,
      avatar: editForm.value.avatar
    })

    // 重新拉取当前用户信息，刷新本地用户态
    await authStore.fetchCurrentUser()
    if (!route.params.userId) {
      displayUser.value = authStore.user
    }

    ElMessage.success('资料更新成功')
    showEditProfile.value = false
  } catch (error: any) {
    if (error?.fields) return
    ElMessage.error(error?.response?.data?.message || '更新失败，请稍后重试')
  } finally {
    updating.value = false
  }
}

const copyInviteLink = async () => {
  try {
    const inviteLink = `${window.location.origin}?ref=${authStore.user?.username}`
    await navigator.clipboard.writeText(inviteLink)
    ElMessage.success('邀请链接已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

// ──────────── 辅助函数 ────────────
const getRoleType = (role?: string) => {
  if (role === 'ADMIN') return 'danger'
  if (role === 'MODERATOR') return 'warning'
  return 'info'
}
const getRoleText = (role?: string) => {
  if (role === 'ADMIN') return '管理员'
  if (role === 'MODERATOR') return '版主'
  return '用户'
}
const getStatusType = (status: PostStatus) => {
  if (status === 'PUBLISHED') return 'success'
  if (status === 'PENDING_REVIEW') return 'warning'
  if (status === 'DRAFT') return 'info'
  return 'info'
}
const getStatusText = (status: PostStatus) => {
  const map: Record<string, string> = {
    PUBLISHED: '已发布', PENDING_REVIEW: '待审核',
    DRAFT: '草稿', REJECTED: '已驳回', TAKEN_DOWN: '已下架'
  }
  return map[status] || '未知'
}
const formatDate = (dateStr: string) => dayjs(dateStr).format('YYYY-MM-DD')

const getLikeTagType = (targetType: string) => {
  if (targetType === 'POST') return 'primary'
  if (targetType === 'COMMENT') return 'success'
  if (targetType === 'PORTFOLIO') return 'warning'
  return 'info'
}
const getLikeTypeText = (targetType: string) => {
  if (targetType === 'POST') return '帖子'
  if (targetType === 'COMMENT') return '评论'
  if (targetType === 'PORTFOLIO') return '组合'
  return '未知'
}
const getLikePreviewText = (item: LikeRecord) => {
  if (!item.target) return `#${item.targetId}`
  if (item.targetType === 'COMMENT') return item.target.body?.slice(0, 10) + '...' || `评论#${item.targetId}`
  return (item.target.title || `#${item.targetId}`).slice(0, 12)
}
const getLikeDisplayTitle = (item: LikeRecord) => {
  if (!item.target) return `已删除的内容 #${item.targetId}`
  if (item.targetType === 'COMMENT') return item.target.body || `评论 #${item.targetId}`
  return item.target.title || `#${item.targetId}`
}
const navigateLikeTarget = (item: LikeRecord) => {
  if (!item.target) return
  if (item.targetType === 'POST') router.push(`/posts/${item.targetId}`)
  else if (item.targetType === 'COMMENT') router.push(`/posts/${item.target.postId}`)
  else if (item.targetType === 'PORTFOLIO') router.push(`/portfolios/${item.targetId}`)
}

// ──────────── 举报用户 ────────────
const showReportDialog = ref(false)
const reportTargetUserId = ref<number | null>(null)
const reportTargetUserSummary = ref('')

const openReportUserDialog = () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  if (!displayUser.value) return
  reportTargetUserId.value = displayUser.value.id
  reportTargetUserSummary.value = `${displayUser.value.displayName || displayUser.value.username} (@${displayUser.value.username})`
  showReportDialog.value = true
}

const handleReportSubmitted = () => {
  // 举报提交成功后的回调
}

// ──────────── 生命周期 ────────────
const initProfilePage = async () => {
  await fetchDisplayUser()
  await fetchUserPosts()
}

onMounted(() => {
  initProfilePage()
  fetchLikesPreview()
  fetchFavoritesPreview()
})

watch(
  () => route.params.userId,
  () => {
    initProfilePage()
  }
)

watch(showEditProfile, (val) => {
  if (val && authStore.user) {
    editForm.value = {
      displayName: authStore.user.displayName || '',
      bio: authStore.user.bio || '',
      avatar: authStore.user.avatar || ''
    }
  }
})
</script>

<style lang="scss" scoped>
.profile {
  max-width: 1000px;
  margin: 0 auto;
  animation: fadeIn 0.3s ease-out;
}

.profile-header {
  margin-bottom: 2rem;
}

.profile-card {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: flex-start;
  gap: 2rem;

  @media (max-width: 768px) {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}

.profile-avatar { flex-shrink: 0; }

.user-avatar {
  border: 4px solid white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.profile-info { flex: 1; }

.user-identity {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;

  @media (max-width: 768px) { justify-content: center; }
}

.user-name {
  font-size: 1.875rem;
  font-weight: black;
  color: #1f2937;
  margin: 0;
}

.user-role-tag {
  font-size: 0.75rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.username {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
  margin: 0 0 1rem 0;
}

.user-bio {
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.6;
  margin: 0 0 1.5rem 0;
  max-width: 600px;
}

.user-stats {
  display: flex;
  gap: 2rem;

  @media (max-width: 768px) { justify-content: center; }
}

.stat-item {
  text-align: center;
  cursor: default;
  
  &.clickable {
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:hover {
      transform: translateY(-2px);
      .stat-value {
        color: var(--el-color-primary);
      }
    }
  }
}

.stat-value {
  display: block;
  font-size: 1.25rem;
  font-weight: black;
  color: #1f2937;
}

.stat-label {
  display: block;
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.profile-actions { flex-shrink: 0; }

.profile-content {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 2rem;

  @media (max-width: 768px) { grid-template-columns: 1fr; }
}

.profile-content.no-sidebar {
  grid-template-columns: 1fr;
}

.profile-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.settings-card,
.activity-overview-card {
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

.settings-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  font-size: 0.875rem;

  &:not(:last-child) {
    border-bottom: 1px solid #f3f4f6;
  }
}

.setting-label { color: #6b7280; }

.setting-value {
  font-weight: 600;
  color: #1f2937;

  &.verified { color: #059669; }
}

/* ── 点赞/收藏概览卡片 ── */
.overview-item {
  display: flex;
  align-items: flex-start;
  gap: 0.875rem;
  padding: 0.75rem 0;
  cursor: pointer;
  border-radius: 0.5rem;
  transition: background 0.15s;

  &:hover {
    background: #f9fafb;
    margin: 0 -0.5rem;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
  }
}

.overview-icon {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 1rem;

  &.likes-icon {
    background: #fef3c7;
    color: #d97706;
  }

  &.favorites-icon {
    background: #dbeafe;
    color: #2563eb;
  }
}

.overview-info {
  flex: 1;
  min-width: 0;
}

.overview-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.overview-count {
  font-size: 0.75rem;
  color: #6b7280;
  display: block;
  margin-bottom: 0.375rem;
}

.overview-empty {
  font-size: 0.75rem;
  color: #d1d5db;
}

.overview-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.preview-tag {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.625rem !important;
}

.overview-arrow {
  color: #d1d5db;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.overview-divider {
  height: 1px;
  background: #f3f4f6;
  margin: 0.25rem 0;
}

/* ── 邀请卡片── */
.invite-card {
  background: linear-gradient(135deg, #2563eb, #1D4ED8);
  border-radius: 1rem;
  padding: 1.5rem;
  color: white;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.invite-title {
  font-size: 1rem;
  font-weight: bold;
  margin: 0 0 0.5rem 0;
}

.invite-subtitle {
  font-size: 0.75rem;
  opacity: 0.8;
  line-height: 1.4;
  margin: 0 0 1rem 0;
}

.invite-btn {
  width: 100%;
  background: rgba(15, 23, 42, 0.10);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;

  &:hover {
    background: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.4);
  }
}

/* ── 右侧活动 ── */
.profile-main-content {
  background: white;
  border-radius: 1rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.section-title {
  font-size: 1.25rem;
  font-weight: bold;
  color: #1f2937;
  padding: 1.5rem 1.5rem 0;
  margin: 0;
}

.loading-container { padding: 1.5rem; }

.activity-skeleton {
  padding: 1.5rem;
  border-bottom: 1px solid #f3f4f6;

  &:last-child { border-bottom: none; }
}

.empty-activity {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.activity-list { padding: 0 1.5rem 1.5rem; }

.activity-card {
  padding: 1.25rem;
  border-radius: 0.75rem;
  border: 1px solid #f3f4f6;
  margin-top: 1rem;
  cursor: pointer;
  transition: all 0.2s ease-in-out;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.status-tag {
  font-size: 0.625rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.activity-date {
  font-size: 0.625rem;
  color: #9ca3af;
  font-weight: bold;
}

.activity-title {
  font-size: 1rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
  line-height: 1.4;
}

.activity-content {
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
  margin: 0 0 0.75rem 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  overflow: hidden;
}

.activity-stats {
  display: flex;
  gap: 1rem;
}

/* ── 抽屉内容 ── */
.drawer-loading,
.drawer-empty {
  padding: 2rem 0;
}

.drawer-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.drawer-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem 0;
  border-bottom: 1px solid #f3f4f6;
  gap: 0.75rem;
  transition: background 0.15s;
  border-radius: 0.5rem;

  &.clickable {
    cursor: pointer;
    &:hover {
      background: #f9fafb;
      padding-left: 0.5rem;
      padding-right: 0.5rem;
    }
  }

  &:last-child { border-bottom: none; }
}

.drawer-item-left {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  flex: 1;
  min-width: 0;
}

.type-tag { flex-shrink: 0; }

.drawer-item-content {
  flex: 1;
  min-width: 0;
}

.drawer-item-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
  margin: 0 0 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
}

.drawer-item-sub {
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0 0 0.125rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.drawer-item-author {
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0;
}

.drawer-item-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
  flex-shrink: 0;
}

.drawer-item-stats {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #9ca3af;
  align-items: center;

  span {
    display: flex;
    align-items: center;
    gap: 0.2rem;
  }
}

.drawer-item-date {
  font-size: 0.625rem;
  color: #d1d5db;
}

.drawer-item-arrow {
  color: #d1d5db;
  font-size: 0.875rem;
}

.drawer-load-more {
  padding: 1rem 0;
  text-align: center;
}

.dialog-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

/* 粉丝/关注列表样式 */
.follow-list {
  padding: 0;
}

.follow-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: #f9fafb;
  }

  &:last-child {
    border-bottom: none;
  }
}

.follow-item-content {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 1rem;
}

.follow-avatar {
  flex-shrink: 0;
}

.follow-info {
  flex: 1;
  min-width: 0;
}

.follow-name-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.follow-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.follow-role-tag {
  flex-shrink: 0;
}

.follow-username {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.follow-stats {
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.follow-stats-sep {
  color: #d1d5db;
}

.follow-action {
  flex-shrink: 0;
  margin-left: 1rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>


