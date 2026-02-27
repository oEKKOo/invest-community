<template>
  <div class="post-detail">
    <div v-if="postsStore.loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="!postsStore.currentPost" class="not-found">
      <el-result
        icon="warning"
        title="帖子不存在"
        sub-title="该帖子可能已被删除或您没有权限查看"
      >
        <template #extra>
          <el-button type="primary" @click="$router.back()">返回</el-button>
        </template>
      </el-result>
    </div>

    <div v-else class="post-container">
      <article class="post-article">
        <header class="post-header">
          <div class="author-info">
            <el-avatar 
              :src="postsStore.currentPost.authorAvatar || getAvatarUrl(postsStore.currentPost.authorId)" 
              :size="48"
            >
              {{ postsStore.currentPost.authorName[0] }}
            </el-avatar>
            <div class="author-details">
              <h3 class="author-name">{{ postsStore.currentPost.authorName }}</h3>
              <p class="post-meta">{{ formatDate(postsStore.currentPost.createdAt) }}</p>
            </div>
          </div>
          
          <el-tag 
            :type="getStatusType(postsStore.currentPost.status)" 
            size="small"
          >
            {{ getStatusText(postsStore.currentPost.status) }}
          </el-tag>
        </header>

        <h1 class="post-title">{{ postsStore.currentPost.title }}</h1>
        
        <div class="post-content">
          {{ postsStore.currentPost.content }}
        </div>

        <div class="post-tags" v-if="postsStore.currentPost.tags?.length || postsStore.currentPost.assets?.length">
          <el-tag 
            v-for="tag in postsStore.currentPost.tags" 
            :key="tag"
            class="tag-item"
          >
            #{{ tag }}
          </el-tag>
          <!-- 关联标的标签 -->
          <router-link
            v-for="asset in (postsStore.currentPost.assets || [])"
            :key="asset.id"
            :to="{ name: 'AssetDetail', params: { assetId: asset.id } }"
            class="asset-chip-link"
          >
            <el-tag
              size="default"
              :type="getAssetMarketType(asset.market)"
              class="asset-chip-tag"
            >
              📈 {{ asset.code }} · {{ asset.name }}
              <span v-if="asset.market" class="market-suffix">({{ asset.market }})</span>
            </el-tag>
          </router-link>
        </div>

        <div class="post-actions">
          <el-button
            type="text"
            :class="{ liked: postsStore.currentPost.isLiked }"
            @click="handleLike"
            class="action-btn"
          >
            <el-icon><Star /></el-icon>
            <span>{{ postsStore.currentPost.likes }} 点赞</span>
          </el-button>

          <el-button
            type="text"
            :class="{ favorited: postsStore.currentPost.isFavorited }"
            @click="handleFavorite"
            class="action-btn"
          >
            <el-icon><Star /></el-icon>
            <span>收藏</span>
          </el-button>

          <el-button
            type="text"
            @click="showShareDialog = true"
            class="action-btn"
          >
            <el-icon><Share /></el-icon>
            <span>分享</span>
          </el-button>
        </div>
      </article>

      <!-- 评论区域 -->
      <section class="comments-section">
        <h3 class="comments-title">评论 ({{ postsStore.currentPost.comments }})</h3>
        
        <!-- 发表评论 -->
        <div class="comment-form" v-if="authStore.isLoggedIn">
          <el-input
            v-model="newComment"
            type="textarea"
            :rows="3"
            placeholder="写下你的看法..."
            class="comment-input"
          />
          <div class="comment-actions">
            <el-button 
              type="primary" 
              @click="handleAddComment"
              :loading="commenting"
              :disabled="!newComment.trim()"
            >
              发表评论
            </el-button>
          </div>
        </div>

        <div class="comments-list">
          <!-- 这里可以添加评论列表 -->
          <el-empty description="暂无评论" />
        </div>
      </section>
    </div>

    <!-- 分享对话框-->
    <el-dialog v-model="showShareDialog" title="分享帖子" width="400px">
      <div class="share-options">
        <p>复制链接分享给朋友：</p>
        <el-input
          :value="shareUrl"
          readonly
          class="share-url"
        >
          <template #append>
            <el-button @click="copyShareUrl">复制</el-button>
          </template>
        </el-input>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePostsStore } from '../stores/posts'
import { useAuthStore } from '../stores/auth'
import { PostStatus } from '../types'
import { ElMessage } from 'element-plus'
import {
  Star,
  Share
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const route = useRoute()
const postsStore = usePostsStore()
const authStore = useAuthStore()

const newComment = ref('')
const commenting = ref(false)
const showShareDialog = ref(false)

const shareUrl = computed(() => {
  return `${window.location.origin}/posts/${route.params.id}`
})

const handleLike = async () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }

  if (!postsStore.currentPost) return

  try {
    await postsStore.toggleLike(postsStore.currentPost.id)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleFavorite = async () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }

  if (!postsStore.currentPost) return

  try {
    await postsStore.toggleFavorite(postsStore.currentPost.id)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleAddComment = async () => {
  if (!newComment.value.trim()) return

  commenting.value = true
  try {
    // TODO: 调用评论API
    ElMessage.success('评论发表成功')
    newComment.value = ''
  } catch (error) {
    ElMessage.error('评论失败')
  } finally {
    commenting.value = false
  }
}

const copyShareUrl = async () => {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    ElMessage.success('链接已复制')
    showShareDialog.value = false
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const getStatusType = (status: PostStatus) => {
  switch (status) {
    case PostStatus.PUBLISHED: return 'success'
    case PostStatus.PENDING_REVIEW: return 'warning'
    case PostStatus.DRAFT: return 'info'
    default: return 'info'
  }
}

const getStatusText = (status: PostStatus) => {
  switch (status) {
    case PostStatus.PUBLISHED: return '已发布'
    case PostStatus.PENDING_REVIEW: return '待审核'
    case PostStatus.DRAFT: return '草稿'
    default: return '未知'
  }
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY年MM月DD日 HH:mm')
}

const getAvatarUrl = (id: number) => {
  return `https://picsum.photos/seed/${id}/48/48`
}

const getAssetMarketType = (market?: string) => {
  const m = market?.toUpperCase()
  if (m === 'SH' || m === 'SZ') return 'danger'
  if (m === 'HK') return 'warning'
  if (m === 'US') return 'primary'
  return 'info'
}

onMounted(async () => {
  const postId = Number(route.params.id)
  if (postId) {
    try {
      await postsStore.fetchPost(postId)
    } catch (error) {
      ElMessage.error('获取帖子详情失败')
    }
  }
})
</script>

<style lang="scss" scoped>
.post-detail {
  max-width: 800px;
  margin: 0 auto;
  animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.loading-container {
  background: #FFFFFF;
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 2rem;
}

.not-found {
  background: #FFFFFF;
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 2rem;
}

.post-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.post-article {
  background: #FFFFFF;
  border: 1px solid $border-default;
  border-radius: $border-radius;
  padding: 2rem;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid $border-subtle;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 0.875rem;
}

.author-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.author-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: $text-primary;
  margin: 0;
}

.post-meta {
  font-size: 0.8rem;
  color: $text-muted;
  margin: 0;
  font-family: 'IBM Plex Mono', monospace;
}

.post-title {
  font-size: 1.625rem;
  font-weight: 700;
  color: $text-primary;
  line-height: 1.35;
  margin: 0 0 1.25rem 0;
  letter-spacing: -0.025em;
}

.post-content {
  font-size: 0.9375rem;
  color: $text-secondary;
  line-height: 1.75;
  margin-bottom: 1.5rem;
  white-space: pre-wrap;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-bottom: 1.5rem;
}

.tag-item {
  background: rgba(124, 58, 237, 0.1) !important;
  border: 1px solid rgba(29, 78, 216, 0.12) !important;
  color: $primary-color !important;
  border-radius: 6px !important;
  font-size: 0.7rem !important;
  font-weight: 600 !important;
}

.asset-chip-link {
  text-decoration: none;

  .asset-chip-tag {
    cursor: pointer;
    font-weight: 600;
    font-size: 0.8rem;

    .market-suffix {
      font-size: 0.7rem;
      opacity: 0.7;
      margin-left: 2px;
    }

    &:hover {
      opacity: 0.8;
    }
  }
}

.post-actions {
  display: flex;
  gap: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid $border-subtle;
}

.action-btn {
  display: flex !important;
  align-items: center !important;
  gap: 0.5rem !important;
  color: $text-muted !important;
  font-size: 0.875rem !important;
  border-radius: 8px !important;
  padding: 0.375rem 0.75rem !important;
  transition: $transition-all !important;
  cursor: pointer;

  &:hover {
    color: $primary-color !important;
    background: rgba(124, 58, 237, 0.1) !important;
  }

  &.liked {
    color: $error-color !important;
    background: rgba(239, 68, 68, 0.08) !important;
  }

  &.favorited {
    color: $warning-color !important;
    background: rgba(245, 158, 11, 0.08) !important;
  }
}

.comments-section {
  background: #FFFFFF;
  border: 1px solid $border-default;
  border-radius: $border-radius;
  padding: 1.75rem;
}

.comments-title {
  font-size: 1rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 1.5rem 0;
  letter-spacing: -0.01em;
}

.comment-form {
  margin-bottom: 2rem;
}

.comment-input {
  margin-bottom: 1rem;

  :deep(.el-textarea__inner) {
    background: rgba(15, 23, 42, 0.03) !important;
    border: 1px solid $border-default !important;
    border-radius: 10px !important;
    color: $text-primary !important;
    font-size: 0.9rem !important;
    line-height: 1.6 !important;

    &:focus {
      border-color: $primary-color !important;
      box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.12) !important;
    }

    &::placeholder {
      color: $text-muted !important;
    }
  }
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
}

.comments-list {
  margin-top: 1.5rem;
}

.share-options {
  text-align: center;

  p {
    margin-bottom: 1rem;
    color: $text-secondary;
  }
}

.share-url {
  :deep(.el-input-group__append) {
    background: $gradient-primary;
    border-color: $primary-color;
    color: white;
    font-weight: 600;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>



