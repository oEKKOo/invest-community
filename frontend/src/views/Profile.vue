<template>
  <div class="profile">
    <!-- Hero 区 - 顶部视觉区域 -->
    <div class="profile-hero">
      <div class="hero-content">
        <div class="hero-avatar">
          <el-avatar 
            :src="displayUser?.avatar || authStore.user?.avatar" 
            :size="120"
            class="user-avatar"
          >
            {{ displayUser?.displayName?.[0] || authStore.user?.displayName?.[0] }}
          </el-avatar>
        </div>
        
        <div class="hero-info">
          <div class="hero-identity">
            <h1 class="hero-name">{{ displayUser?.displayName || authStore.user?.displayName }}</h1>
            <el-tag 
              :type="getRoleType(displayUser?.role || authStore.user?.role)"
              class="hero-role-tag"
              size="large"
            >
              {{ getRoleText(displayUser?.role || authStore.user?.role) }}
            </el-tag>
          </div>
          <p class="hero-username">@{{ displayUser?.username || authStore.user?.username }}</p>
          <p class="hero-bio">{{ displayUser?.bio || authStore.user?.bio || '这个人很懒，还没有填写个人简介' }}</p>
          
          <!-- 核心指标 -->
          <div class="hero-stats">
            <div class="hero-stat-item clickable" @click="openFollowDrawer('followers')">
              <span class="hero-stat-value">{{ displayUser?.followers || authStore.user?.followers || 0 }}</span>
              <span class="hero-stat-label">关注者</span>
            </div>
            <div class="hero-stat-item clickable" @click="openFollowDrawer('following')">
              <span class="hero-stat-value">{{ displayUser?.following || authStore.user?.following || 0 }}</span>
              <span class="hero-stat-label">关注</span>
            </div>
            <div class="hero-stat-item">
              <span class="hero-stat-value">{{ userPostsCount }}</span>
              <span class="hero-stat-label">帖子</span>
            </div>
            <div class="hero-stat-item">
              <span class="hero-stat-value">{{ userPortfoliosCount }}</span>
              <span class="hero-stat-label">组合</span>
            </div>
            <div class="hero-stat-item">
              <span class="hero-stat-value">{{ totalLikes }}</span>
              <span class="hero-stat-label">获赞</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="hero-actions">
            <template v-if="isSelf">
              <el-button 
                type="primary" 
                @click="showEditProfile = true"
                size="large"
              >
                编辑资料
              </el-button>
              <el-button 
                plain
                @click="copyInviteLink"
                size="large"
              >
                复制邀请链接
              </el-button>
            </template>
            <template v-else>
              <el-button 
                :type="isFollowing ? 'default' : 'primary'"
                :plain="isFollowing"
                @click="toggleFollow"
                size="large"
              >
                {{ isFollowing ? '已关注' : '关注' }}
              </el-button>
              <el-button 
                type="danger" 
                plain
                @click="openReportUserDialog"
                size="large"
              >
                <el-icon><Warning /></el-icon>
                举报用户
              </el-button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- 主体内容区 -->
    <div class="profile-content-wrapper">
      <div class="profile-content" :class="{ 'no-sidebar': !isSelf }">
        <!-- 左侧：辅助信息区（仅自己主页） -->
        <aside v-if="isSelf" class="profile-sidebar">
          

        

          <!-- 我的互动 -->
          <div class="sidebar-card">
            <h3 class="card-title">我的互动</h3>
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
                  <template v-else>
                    <span class="overview-count">{{ likesTotal }} 条记录</span>
                  </template>
                </div>
              </div>
              <el-icon class="overview-arrow"><ArrowRight /></el-icon>
            </div>

            <div class="overview-divider" />

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
                  <template v-else>
                    <span class="overview-count">{{ favoritesTotal }} 篇帖子</span>
                  </template>
                </div>
              </div>
              <el-icon class="overview-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </aside>

        <!-- 右侧：主内容区 -->
        <main class="profile-main-content">
          <!-- Tab 导航 -->
          <el-tabs v-model="activeTab" class="profile-tabs" @tab-change="handleTabChange">
            <el-tab-pane label="总览" name="overview">
              <div class="tab-content">
                <!-- 总览页内容 -->
                <div v-if="overviewLoading" class="loading-container">
                  <el-skeleton :rows="5" animated />
                </div>
                <div v-else class="overview-content">
                  <!-- 代表作品 -->
                  <div class="overview-section">
                    <h3 class="section-title">代表作品</h3>
                    <div class="featured-grid">
                      <!-- 代表帖子 -->
                      <div v-if="featuredPost" class="featured-card" @click="$router.push(`/posts/${featuredPost.id}`)">
                        <div class="featured-badge">代表帖子</div>
                        <h4 class="featured-title">{{ featuredPost.title }}</h4>
                        <p class="featured-content">{{ featuredPost.content?.slice(0, 100) }}...</p>
                        <div class="featured-stats">
                          <span><el-icon><Star /></el-icon> {{ featuredPost.likes }}</span>
                          <span><el-icon><ChatLineRound /></el-icon> {{ featuredPost.comments }}</span>
                        </div>
                      </div>
                      <div v-else class="featured-card empty">
                        <el-empty description="暂无代表帖子" :image-size="60" />
                      </div>

                      <!-- 代表组合 -->
                      <div v-if="featuredPortfolio" class="featured-card" @click="$router.push(`/portfolios/${featuredPortfolio.id}`)">
                        <div class="featured-badge">代表组合</div>
                        <h4 class="featured-title">{{ featuredPortfolio.title }}</h4>
                        <p class="featured-content">{{ featuredPortfolio.description?.slice(0, 100) }}...</p>
                        <div class="featured-stats">
                          <span><el-icon><Star /></el-icon> {{ featuredPortfolio.likes }}</span>
                          <el-tag :type="getRiskLevelType(featuredPortfolio.riskLevel)" size="small">
                            {{ featuredPortfolio.riskLevel }} 风险
                          </el-tag>
                        </div>
                      </div>
                      <div v-else class="featured-card empty">
                        <el-empty description="暂无代表组合" :image-size="60" />
                      </div>
                    </div>
                  </div>

                  <!-- 最近动态 -->
                  <div class="overview-section">
                    <h3 class="section-title">最近动态</h3>
                    <div class="activity-timeline">
                      <div v-if="recentActivities.length === 0" class="empty-timeline">
                        <el-empty description="暂无动态" :image-size="80" />
                      </div>
                      <div v-else>
                        <div
                          v-for="activity in recentActivities"
                          :key="activity.id"
                          class="timeline-item"
                          @click="handleActivityClick(activity)"
                        >
                          <div class="timeline-icon" :class="activity.type">
                            <el-icon v-if="activity.type === 'post'"><Edit /></el-icon>
                            <el-icon v-else-if="activity.type === 'portfolio'"><FolderOpened /></el-icon>
                            <el-icon v-else><Star /></el-icon>
                          </div>
                          <div class="timeline-content">
                            <p class="timeline-text">{{ activity.text }}</p>
                            <span class="timeline-time">{{ formatDate(activity.createdAt) }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 社区影响力 -->
                  <div class="overview-section">
                    <h3 class="section-title">社区影响力</h3>
                    <div class="influence-grid">
                      <div class="influence-card">
                        <div class="influence-value">{{ totalLikes }}</div>
                        <div class="influence-label">总获赞</div>
                      </div>
                      <div class="influence-card">
                        <div class="influence-value">{{ totalComments }}</div>
                        <div class="influence-label">总评论</div>
                      </div>
                      <div class="influence-card">
                        <div class="influence-value">{{ avgEngagement }}</div>
                        <div class="influence-label">平均互动</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane :label="`帖子 (${userPostsCount})`" name="posts">
              <div class="tab-content">
                <div v-if="loading" class="loading-container">
                  <div v-for="i in 3" :key="i" class="activity-skeleton">
                    <el-skeleton :rows="3" animated />
                  </div>
                </div>
                <div v-else-if="userPosts.length === 0" class="empty-state">
                  <el-empty 
                    description="还没有发布任何内容"
                    :image-size="120"
                  >
                    <el-button 
                      v-if="isSelf"
                      type="primary" 
                      @click="$router.push('/community')"
                    >
                      发表第一篇帖子
                    </el-button>
                  </el-empty>
                </div>
                <div v-else class="posts-list">
                  <div 
                    v-for="post in userPosts"
                    :key="post.id"
                    class="post-card"
                    @click="$router.push(`/posts/${post.id}`)"
                  >
                    <div class="post-header">
                      <el-tag 
                        :type="getStatusType(post.status)"
                        size="small"
                        class="status-tag"
                      >
                        {{ getStatusText(post.status) }}
                      </el-tag>
                      <span class="post-date">{{ formatDate(post.createdAt) }}</span>
                    </div>
                    <h4 class="post-title">{{ post.title }}</h4>
                    <p class="post-content">{{ post.content?.slice(0, 150) }}...</p>
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
            </el-tab-pane>

            <el-tab-pane :label="`投资组合 (${userPortfoliosCount})`" name="portfolios">
              <div class="tab-content">
                <div v-if="portfoliosLoading" class="loading-container">
                  <div v-for="i in 3" :key="i" class="portfolio-skeleton">
                    <el-skeleton :rows="4" animated />
                  </div>
                </div>
                <div v-else-if="userPortfolios.length === 0" class="empty-state">
                  <el-empty 
                    description="还没有创建任何投资组合"
                    :image-size="120"
                  >
                    <el-button 
                      v-if="isSelf"
                      type="primary" 
                      @click="$router.push('/portfolios')"
                    >
                      创建第一个组合
                    </el-button>
                  </el-empty>
                </div>
                <div v-else class="portfolios-grid">
                  <div
                    v-for="portfolio in userPortfolios"
                    :key="portfolio.id"
                    class="portfolio-card"
                    @click="$router.push(`/portfolios/${portfolio.id}`)"
                  >
                    <div class="portfolio-header">
                      <h3 class="portfolio-title">{{ portfolio.title }}</h3>
                      <el-tag
                        :type="getRiskLevelType(portfolio.riskLevel)"
                        size="small"
                        class="risk-tag"
                      >
                        {{ portfolio.riskLevel }} 风险
                      </el-tag>
                    </div>
                    <p class="portfolio-description">{{ portfolio.description }}</p>
                    <div class="portfolio-footer">
                      <div class="portfolio-stats">
                        <span><el-icon><Star /></el-icon> {{ portfolio.likes }}</span>
                      </div>
                      <span class="portfolio-date">{{ formatDate(portfolio.createdAt) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane v-if="isSelf" label="收藏" name="favorites">
              <div class="tab-content">
                <div v-if="favoritesLoading" class="loading-container">
                  <el-skeleton :rows="5" animated />
                </div>
                <div v-else-if="allFavoriteRecords.length === 0" class="empty-state">
                  <el-empty description="暂无收藏记录" :image-size="120" />
                </div>
                <div v-else class="favorites-list">
                  <div
                    v-for="item in allFavoriteRecords"
                    :key="item.id"
                    class="favorite-card"
                    @click="$router.push(`/posts/${item.id}`)"
                  >
                    <h4 class="favorite-title">{{ item.title }}</h4>
                    <p class="favorite-author">{{ item.authorName }}</p>
                    <div class="favorite-stats">
                      <span><el-icon><Star /></el-icon> {{ item.likes }}</span>
                      <span><el-icon><ChatLineRound /></el-icon> {{ item.comments }}</span>
                      <span class="favorite-date">{{ formatDate(item.createdAt) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane v-if="isSelf" label="点赞记录" name="likes">
              <div class="tab-content">
                <div v-if="likesLoading" class="loading-container">
                  <el-skeleton :rows="5" animated />
                </div>
                <div v-else-if="allLikeRecords.length === 0" class="empty-state">
                  <el-empty description="暂无点赞记录" :image-size="120" />
                </div>
                <div v-else class="likes-list">
                  <div
                    v-for="item in allLikeRecords"
                    :key="item.id"
                    class="like-card"
                    :class="{ clickable: item.target }"
                    @click="navigateLikeTarget(item)"
                  >
                    <el-tag
                      :type="getLikeTagType(item.targetType)"
                      size="small"
                      class="like-type-tag"
                    >
                      {{ getLikeTypeText(item.targetType) }}
                    </el-tag>
                    <div class="like-content">
                      <p class="like-title">{{ getLikeDisplayTitle(item) }}</p>
                      <span class="like-date">{{ formatDate(item.createdAt) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </main>
      </div>
    </div>

    <!-- 编辑资料对话框 -->
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
            placeholder="请输入头像URL（需为可访问的网络图片地址）"
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
import { usePortfoliosStore } from '../stores/portfolios'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { PostStatus, LikeRecord, Post, Portfolio } from '../types'
import {
  Star,
  ChatLineRound,
  Collection,
  ArrowRight,
  Warning,
  Edit,
  Plus,
  FolderOpened
} from '@element-plus/icons-vue'
import ReportDialog from '@/components/ReportDialog.vue'
import dayjs from 'dayjs'
import { getMyLikes } from '@/api/likes'
import { getMyFavorites } from '@/api/posts'
import type { User } from '@/types'
import { getUserFollowers, getUserFollowing, unfollowUser, type UserFollowItem } from '@/api/users'
import { updateCurrentUser } from '@/api/auth'
import { getPortfolios } from '@/api/portfolios'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const postsStore = usePostsStore()
const portfoliosStore = usePortfoliosStore()

// ──────────── 基础状态 ────────────
const loading = ref(false)
const showEditProfile = ref(false)
const updating = ref(false)
const activeTab = ref('overview')
const overviewLoading = ref(false)
const portfoliosLoading = ref(false)

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
const likeRecords = ref<LikeRecord[]>([])
const allLikeRecords = ref<LikeRecord[]>([])
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
    // 静默失败
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
const favoriteRecords = ref<Post[]>([])
const allFavoriteRecords = ref<Post[]>([])
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

// ──────────── 关注 / 粉丝相关 ────────────
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
    // 忽略错误
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

const getFollowUser = (item: UserFollowItem): User => {
  return followDrawerType.value === 'followers' ? item.follower : item.followee
}

const getFollowItemId = (item: UserFollowItem): number => {
  const user = getFollowUser(item)
  return user.id
}

const navigateToUser = (user: User) => {
  router.push({ name: 'UserProfile', params: { userId: user.id } })
}

const handleUnfollow = async (user: User) => {
  if (unfollowingIds.value.has(user.id)) return
  
  try {
    unfollowingIds.value.add(user.id)
    await unfollowUser(user.id)
    
    followList.value = followList.value.filter(item => getFollowUser(item).id !== user.id)
    
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

const userPostsCount = computed(() => userPosts.value.length)

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

// ──────────── 用户投资组合 ────────────
const userPortfolios = ref<Portfolio[]>([])

const userPortfoliosCount = computed(() => userPortfolios.value.length)

const fetchUserPortfolios = async () => {
  const uid = targetUserId.value
  if (!uid) return
  portfoliosLoading.value = true
  try {
    const res = await getPortfolios({ userId: uid, pageSize: 50 })
    userPortfolios.value = res.items
  } catch {
    ElMessage.error('获取投资组合失败')
  } finally {
    portfoliosLoading.value = false
  }
}

// ──────────── 总览页数据 ────────────
const featuredPost = computed(() => {
  // 选择点赞数最多的帖子作为代表帖子
  if (userPosts.value.length === 0) return null
  return userPosts.value.reduce((max, post) => 
    post.likes > (max?.likes || 0) ? post : max
  )
})

const featuredPortfolio = computed(() => {
  // 选择点赞数最多的组合作为代表组合
  if (userPortfolios.value.length === 0) return null
  return userPortfolios.value.reduce((max, p) => 
    p.likes > (max?.likes || 0) ? p : max
  )
})

const recentActivities = computed(() => {
  const activities: Array<{
    id: number
    type: 'post' | 'portfolio' | 'like'
    text: string
    createdAt: string
    targetId?: number
  }> = []
  
  // 最近帖子
  userPosts.value.slice(0, 3).forEach(post => {
    activities.push({
      id: post.id,
      type: 'post',
      text: `发布了帖子：${post.title}`,
      createdAt: post.createdAt,
      targetId: post.id
    })
  })
  
  // 最近组合
  userPortfolios.value.slice(0, 3).forEach(portfolio => {
    activities.push({
      id: portfolio.id,
      type: 'portfolio',
      text: `创建了投资组合：${portfolio.title}`,
      createdAt: portfolio.createdAt,
      targetId: portfolio.id
    })
  })
  
  // 按时间排序
  return activities.sort((a, b) => 
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  ).slice(0, 10)
})

const totalLikes = computed(() => {
  const postLikes = userPosts.value.reduce((sum, p) => sum + (p.likes || 0), 0)
  const portfolioLikes = userPortfolios.value.reduce((sum, p) => sum + (p.likes || 0), 0)
  return postLikes + portfolioLikes
})

const totalComments = computed(() => {
  return userPosts.value.reduce((sum, p) => sum + (p.comments || 0), 0)
})

const avgEngagement = computed(() => {
  const total = userPostsCount.value + userPortfoliosCount.value
  if (total === 0) return '0'
  const avg = (totalLikes.value + totalComments.value) / total
  return avg.toFixed(1)
})

const handleActivityClick = (activity: any) => {
  if (activity.type === 'post' && activity.targetId) {
    router.push(`/posts/${activity.targetId}`)
  } else if (activity.type === 'portfolio' && activity.targetId) {
    router.push(`/portfolios/${activity.targetId}`)
  }
}

const fetchOverviewData = async () => {
  overviewLoading.value = true
  try {
    await Promise.all([
      fetchUserPosts(),
      fetchUserPortfolios()
    ])
  } finally {
    overviewLoading.value = false
  }
}

// ──────────── Tab 切换 ────────────
const handleTabChange = async (tabName: string) => {
  if (tabName === 'overview') {
    await fetchOverviewData()
  } else if (tabName === 'posts') {
    await fetchUserPosts()
  } else if (tabName === 'portfolios') {
    await fetchUserPortfolios()
  } else if (tabName === 'favorites' && isSelf.value) {
    await fetchAllFavorites(true)
  } else if (tabName === 'likes' && isSelf.value) {
    await fetchAllLikes(true)
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

const getRiskLevelType = (riskLevel: string) => {
  switch (riskLevel) {
    case 'High': return 'danger'
    case 'Medium': return 'warning'
    case 'Low': return 'success'
    default: return 'info'
  }
}

const formatDate = (dateStr: string) => dayjs(dateStr).format('YYYY-MM-DD')

const formatJoinDate = (dateStr?: string) => {
  if (!dateStr) return '未知'
  return dayjs(dateStr).format('YYYY年MM月')
}

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
  if (activeTab.value === 'overview') {
    await fetchOverviewData()
  } else if (activeTab.value === 'posts') {
    await fetchUserPosts()
  } else if (activeTab.value === 'portfolios') {
    await fetchUserPortfolios()
  }
}

onMounted(() => {
  initProfilePage()
  if (isSelf.value) {
    fetchLikesPreview()
    fetchFavoritesPreview()
  }
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
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.3s ease-out;
}

// ──────────── Hero 区 ────────────
.profile-hero {
  position: relative;
  margin-bottom: 2rem;
  border-radius: $border-radius-lg;
  overflow: hidden;
  background: $bg-card;
  border: 1px solid $border-subtle;
  box-shadow: $shadow;
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: 2rem;
  display: flex;
  gap: 2rem;
  align-items: flex-start;

  @media (max-width: 768px) {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}

.hero-avatar {
  flex-shrink: 0;
}

.user-avatar {
  border: 4px solid white;
  box-shadow: $shadow-md;
}

.hero-info {
  flex: 1;
  min-width: 0;
}

.hero-identity {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;

  @media (max-width: 768px) {
    justify-content: center;
  }
}

.hero-name {
  font-size: 2rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0;
  letter-spacing: -0.02em;
}

.hero-role-tag {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.hero-username {
  font-size: 1rem;
  color: $text-secondary;
  font-weight: 500;
  margin: 0 0 0.75rem 0;
}

.hero-bio {
  font-size: 0.9375rem;
  color: $text-secondary;
  line-height: 1.6;
  margin: 0 0 1.5rem 0;
  max-width: 600px;
}

.hero-stats {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;

  @media (max-width: 768px) {
    justify-content: center;
  }
}

.hero-stat-item {
  text-align: center;
  cursor: default;
  
  &.clickable {
    cursor: pointer;
    transition: $transition-all;
    
    &:hover {
      transform: translateY(-2px);
      .hero-stat-value {
        color: $primary-color;
      }
    }
  }
}

.hero-stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: $text-primary;
  font-family: 'IBM Plex Mono', monospace;
}

.hero-stat-label {
  display: block;
  font-size: 0.75rem;
  color: $text-muted;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.25rem;
}

.hero-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;

  @media (max-width: 768px) {
    justify-content: center;
    width: 100%;
  }
}

// ──────────── 主体内容区 ────────────
.profile-content-wrapper {
  margin-bottom: 2rem;
}

.profile-content {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 2rem;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }

  &.no-sidebar {
    grid-template-columns: 1fr;
  }
}

.profile-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.sidebar-card {
  background: $bg-card;
  border-radius: $border-radius;
  padding: 1.5rem;
  border: 1px solid $border-subtle;
  box-shadow: $shadow-sm;
}

.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 1rem 0;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.quick-action-btn {
  width: 100%;
  justify-content: flex-start;
}

.info-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  font-size: 0.875rem;

  &:not(:last-child) {
    border-bottom: 1px solid $border-subtle;
  }
}

.info-label {
  color: $text-secondary;
}

.info-value {
  font-weight: 600;
  color: $text-primary;

  &.verified {
    color: $success-color;
  }
}

.overview-item {
  display: flex;
  align-items: flex-start;
  gap: 0.875rem;
  padding: 0.75rem 0;
  cursor: pointer;
  border-radius: 0.5rem;
  transition: background 0.15s;

  &:hover {
    background: $bg-dark;
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
  color: $text-primary;
  margin-bottom: 0.25rem;
}

.overview-count {
  font-size: 0.75rem;
  color: $text-muted;
  display: block;
}

.overview-arrow {
  color: $text-muted;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.overview-divider {
  height: 1px;
  background: $border-subtle;
  margin: 0.25rem 0;
}

// ──────────── 主内容区 ────────────
.profile-main-content {
  background: $bg-card;
  border-radius: $border-radius;
  border: 1px solid $border-subtle;
  box-shadow: $shadow-sm;
  overflow: hidden;
}

.profile-tabs {
  :deep(.el-tabs__header) {
    margin: 0;
    padding: 0 1.5rem;
    border-bottom: 1px solid $border-subtle;
  }

  :deep(.el-tabs__item) {
    font-weight: 600;
    color: $text-secondary;
    
    &.is-active {
      color: $primary-color;
    }
  }
}

.tab-content {
  padding: 1.5rem;
  min-height: 400px;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 1rem 0;
}

// ──────────── 总览页 ────────────
.overview-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.overview-section {
  &:not(:last-child) {
    padding-bottom: 2rem;
    border-bottom: 1px solid $border-subtle;
  }
}

.featured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.featured-card {
  background: $bg-dark;
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 1.25rem;
  cursor: pointer;
  transition: $transition-all;
  position: relative;

  &:hover {
    box-shadow: $shadow;
    transform: translateY(-2px);
  }

  &.empty {
    cursor: default;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 150px;
  }
}

.featured-badge {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  font-size: 0.625rem;
  font-weight: 700;
  color: $primary-color;
  background: rgba(29, 78, 216, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.featured-title {
  font-size: 1rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
}

.featured-content {
  font-size: 0.875rem;
  color: $text-secondary;
  line-height: 1.5;
  margin: 0 0 0.75rem 0;
}

.featured-stats {
  display: flex;
  gap: 1rem;
  align-items: center;
  font-size: 0.75rem;
  color: $text-muted;
}

.activity-timeline {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.empty-timeline {
  padding: 2rem 0;
}

.timeline-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: $border-radius;
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: $bg-dark;
  }
}

.timeline-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.875rem;

  &.post {
    background: rgba(29, 78, 216, 0.1);
    color: $primary-color;
  }

  &.portfolio {
    background: rgba(22, 163, 74, 0.1);
    color: $success-color;
  }

  &.like {
    background: rgba(217, 119, 6, 0.1);
    color: $warning-color;
  }
}

.timeline-content {
  flex: 1;
  min-width: 0;
}

.timeline-text {
  font-size: 0.875rem;
  color: $text-primary;
  margin: 0 0 0.25rem 0;
}

.timeline-time {
  font-size: 0.75rem;
  color: $text-muted;
}

.influence-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.influence-card {
  background: $bg-dark;
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 1.25rem;
  text-align: center;
}

.influence-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: $primary-color;
  font-family: 'IBM Plex Mono', monospace;
  margin-bottom: 0.5rem;
}

.influence-label {
  font-size: 0.75rem;
  color: $text-muted;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

// ──────────── 帖子列表 ────────────
.posts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.post-card {
  background: $bg-dark;
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 1.25rem;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    box-shadow: $shadow;
    transform: translateY(-2px);
  }
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.status-tag {
  font-size: 0.625rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.post-date {
  font-size: 0.75rem;
  color: $text-muted;
}

.post-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
}

.post-content {
  font-size: 0.875rem;
  color: $text-secondary;
  line-height: 1.6;
  margin: 0 0 0.75rem 0;
}

.post-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: $text-muted;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

// ──────────── 投资组合列表 ────────────
.portfolios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.portfolio-card {
  background: $bg-dark;
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 1.25rem;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    box-shadow: $shadow;
    transform: translateY(-2px);
  }
}

.portfolio-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.portfolio-title {
  font-size: 1rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0;
  flex: 1;
  line-height: 1.4;
}

.risk-tag {
  font-size: 0.7rem !important;
  font-weight: 700 !important;
  margin-left: 0.75rem !important;
}

.portfolio-description {
  font-size: 0.875rem;
  color: $text-secondary;
  line-height: 1.5;
  margin: 0 0 0.75rem 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.portfolio-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.75rem;
  border-top: 1px solid $border-subtle;
}

.portfolio-stats {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: $text-muted;
}

.portfolio-date {
  font-size: 0.75rem;
  color: $text-muted;
}

// ──────────── 收藏/点赞列表 ────────────
.favorites-list,
.likes-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.favorite-card,
.like-card {
  background: $bg-dark;
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 1rem;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    box-shadow: $shadow-sm;
  }

  &.clickable:hover {
    background: $bg-card-hover;
  }
}

.favorite-title {
  font-size: 1rem;
  font-weight: 600;
  color: $text-primary;
  margin: 0 0 0.5rem 0;
}

.favorite-author {
  font-size: 0.875rem;
  color: $text-secondary;
  margin: 0 0 0.5rem 0;
}

.favorite-stats {
  display: flex;
  gap: 1rem;
  align-items: center;
  font-size: 0.75rem;
  color: $text-muted;
}

.favorite-date {
  margin-left: auto;
}

.like-card {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.like-type-tag {
  flex-shrink: 0;
}

.like-content {
  flex: 1;
  min-width: 0;
}

.like-title {
  font-size: 0.875rem;
  color: $text-primary;
  margin: 0 0 0.25rem 0;
}

.like-date {
  font-size: 0.75rem;
  color: $text-muted;
}

// ──────────── 通用样式 ────────────
.loading-container {
  padding: 1rem 0;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.activity-skeleton,
.portfolio-skeleton {
  padding: 1rem;
  border-bottom: 1px solid $border-subtle;

  &:last-child {
    border-bottom: none;
  }
}

.clickable {
  cursor: pointer;
}

// ──────────── 抽屉样式 ────────────
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
  border-bottom: 1px solid $border-subtle;
  gap: 0.75rem;
  transition: background 0.15s;
  border-radius: 0.5rem;

  &.clickable {
    cursor: pointer;
    &:hover {
      background: $bg-dark;
      padding-left: 0.5rem;
      padding-right: 0.5rem;
    }
  }

  &:last-child {
    border-bottom: none;
  }
}

.drawer-item-left {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  flex: 1;
  min-width: 0;
}

.type-tag {
  flex-shrink: 0;
}

.drawer-item-content {
  flex: 1;
  min-width: 0;
}

.drawer-item-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: $text-primary;
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
  color: $text-muted;
  margin: 0 0 0.125rem;
}

.drawer-item-author {
  font-size: 0.75rem;
  color: $text-muted;
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
  color: $text-muted;
  align-items: center;
}

.drawer-item-date {
  font-size: 0.625rem;
  color: $text-muted;
}

.drawer-item-arrow {
  color: $text-muted;
  font-size: 0.875rem;
}

.drawer-load-more {
  padding: 1rem 0;
  text-align: center;
}

// ──────────── 粉丝/关注列表 ────────────
.follow-list {
  padding: 0;
}

.follow-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid $border-subtle;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: $bg-dark;
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
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.follow-role-tag {
  flex-shrink: 0;
}

.follow-username {
  font-size: 0.875rem;
  color: $text-secondary;
  margin: 0 0 0.25rem 0;
}

.follow-stats {
  font-size: 0.75rem;
  color: $text-muted;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.follow-stats-sep {
  color: $text-muted;
}

.follow-action {
  flex-shrink: 0;
  margin-left: 1rem;
}

.dialog-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
