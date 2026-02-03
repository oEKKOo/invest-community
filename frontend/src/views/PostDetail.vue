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

        <div class="post-tags" v-if="postsStore.currentPost.tags?.length">
          <el-tag 
            v-for="tag in postsStore.currentPost.tags" 
            :key="tag"
            class="tag-item"
          >
            #{{ tag }}
          </el-tag>
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

    <!-- 分享对话框 -->
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
  animation: fadeIn 0.3s ease-out;
}

.loading-container {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.not-found {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.post-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.post-article {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.author-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.author-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.post-meta {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}

.post-title {
  font-size: 1.75rem;
  font-weight: bold;
  color: #1f2937;
  line-height: 1.3;
  margin: 0 0 1.5rem 0;
}

.post-content {
  font-size: 1rem;
  color: #374151;
  line-height: 1.7;
  margin-bottom: 2rem;
  white-space: pre-wrap;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 2rem;
}

.tag-item {
  background: #f3f4f6;
  border: none;
  color: #6b7280;
}

.post-actions {
  display: flex;
  gap: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #f3f4f6;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6b7280;
  font-size: 0.875rem;
  transition: color 0.2s ease-in-out;

  &:hover {
    color: #2563eb;
  }

  &.liked {
    color: #ef4444;
  }

  &.favorited {
    color: #f59e0b;
  }
}

.comments-section {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.comments-title {
  font-size: 1.125rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0 0 1.5rem 0;
}

.comment-form {
  margin-bottom: 2rem;
}

.comment-input {
  margin-bottom: 1rem;

  :deep(.el-textarea__inner) {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    font-size: 0.875rem;
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
    color: #6b7280;
  }
}

.share-url {
  :deep(.el-input-group__append) {
    background: #2563eb;
    border-color: #2563eb;
    color: white;
  }
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