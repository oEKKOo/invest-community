<template>
  <div class="community">
    <div class="community-header">
      <h2 class="page-title">社区论坛</h2>
      <el-button 
        type="primary" 
        size="large"
        @click="showCreatePost = true"
        :icon="Plus"
        class="create-btn"
      >
        发表讨论
      </el-button>
    </div>

    <!-- 过滤标签 -->
    <div class="filter-tabs">
      <el-button
        v-for="status in statusFilters"
        :key="status.value"
        :type="activeFilter === status.value ? 'primary' : ''"
        :plain="activeFilter !== status.value"
        size="small"
        @click="handleFilterChange(status.value)"
        class="filter-tab"
      >
        {{ status.label }}
      </el-button>
    </div>

    <!-- 创建帖子对话框 -->
    <el-dialog
      v-model="showCreatePost"
      title="分享你的投资见解"
      width="600px"
      class="create-post-dialog"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="0"
      >
        <el-form-item prop="title">
          <el-input
            v-model="createForm.title"
            placeholder="给你的讨论起个标题..."
            size="large"
            class="title-input"
          />
        </el-form-item>

        <el-form-item prop="content">
          <el-input
            v-model="createForm.content"
            type="textarea"
            :rows="6"
            placeholder="分享你的投资分析、策略或问题..."
            class="content-input"
          />
        </el-form-item>

        <el-form-item prop="tags">
          <el-input
            v-model="createForm.tagsInput"
            placeholder="添加标签，用逗号分隔（如：股票,ETF,投资策略）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreatePost = false">取消</el-button>
          <el-button @click="handleCreateDraft" :loading="creating">
            保存草稿
          </el-button>
          <el-button 
            type="primary" 
            @click="handleCreatePost" 
            :loading="creating"
          >
            提交审核
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 帖子列表 -->
    <div class="posts-container">
      <div v-if="postsStore.loading" class="loading-container">
        <div v-for="i in 3" :key="i" class="post-skeleton">
          <el-skeleton :rows="4" animated />
        </div>
      </div>

      <div v-else-if="postsStore.posts.length === 0" class="empty-state">
        <el-empty 
          description="暂无帖子"
          :image-size="120"
        >
          <el-button type="primary" @click="showCreatePost = true">
            发表第一篇讨论
          </el-button>
        </el-empty>
      </div>

      <div v-else class="posts-list">
        <div 
          v-for="post in postsStore.posts" 
          :key="post.id"
          class="post-card"
          @click="$router.push(`/posts/${post.id}`)"
        >
          <div class="post-header">
            <div class="author-info">
              <el-avatar 
                :src="post.authorAvatar || getAvatarUrl(post.authorId)" 
                :size="40"
              >
                {{ post.authorName[0] }}
              </el-avatar>
              <div class="author-details">
                <p class="author-name">{{ post.authorName }}</p>
                <p class="post-date">{{ formatDate(post.createdAt) }}</p>
              </div>
            </div>
            <el-tag 
              :type="getStatusType(post.status)" 
              size="small"
              class="status-tag"
            >
              {{ getStatusText(post.status) }}
            </el-tag>
          </div>

          <h3 class="post-title">{{ post.title }}</h3>
          <p class="post-content">{{ post.content }}</p>

          <div class="post-tags" v-if="post.tags?.length">
            <el-tag 
              v-for="tag in post.tags" 
              :key="tag"
              size="small"
              class="post-tag"
            >
              #{{ tag }}
            </el-tag>
          </div>

          <div class="post-actions">
            <el-button
              type="text"
              :class="{ liked: post.isLiked }"
              @click.stop="handleLike(post.id)"
              class="action-btn"
            >
              <el-icon><Star /></el-icon>
              <span>{{ post.likes }}</span>
            </el-button>

            <el-button
              type="text"
              class="action-btn"
            >
              <el-icon><ChatLineRound /></el-icon>
              <span>{{ post.comments }}</span>
            </el-button>

            <el-button
              type="text"
              :class="{ favorited: post.isFavorited }"
              @click.stop="handleFavorite(post.id)"
              class="action-btn"
            >
              <el-icon><Star /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-container" v-if="postsStore.posts.length > 0">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :total="postsStore.pagination.total"
          layout="prev, pager, next, total"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted, computed } from 'vue'
import { usePostsStore } from '../stores/posts'
import { useAuthStore } from '../stores/auth'
import { PostStatus } from '../types'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  Star,
  ChatLineRound,
  StarFilled
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const postsStore = usePostsStore()
const authStore = useAuthStore()

// 状态
const showCreatePost = ref(false)
const creating = ref(false)
const activeFilter = ref<string>('ALL')
const currentPage = ref(1)
const pageSize = ref(20)

// 表单
const createFormRef = ref<FormInstance>()
const createForm = ref({
  title: '',
  content: '',
  tagsInput: ''
})

const createRules: FormRules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { min: 5, max: 100, message: '标题长度应在5-100字符之间', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入内容', trigger: 'blur' },
    { min: 10, message: '内容至少10个字符', trigger: 'blur' }
  ]
}

// 过滤选项
const statusFilters = [
  { label: '全部', value: 'ALL' },
  { label: '已发布', value: PostStatus.PUBLISHED },
  { label: '待审核', value: PostStatus.PENDING_REVIEW },
  { label: '草稿', value: PostStatus.DRAFT }
]

// 计算属性
const filteredParams = computed(() => {
  const params: any = {
    page: currentPage.value,
    pageSize: pageSize.value,
    sort: 'new'
  }

  if (activeFilter.value !== 'ALL') {
    params.status = activeFilter.value
  }

  return params
})

// 方法
const handleFilterChange = (filter: string) => {
  activeFilter.value = filter
  currentPage.value = 1
  fetchPosts()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchPosts()
}

const fetchPosts = async () => {
  try {
    await postsStore.fetchPosts(filteredParams.value)
  } catch (error) {
    ElMessage.error('获取帖子列表失败')
  }
}

const handleCreatePost = async () => {
  if (!createFormRef.value) return

  try {
    await createFormRef.value.validate()
    creating.value = true

    const tags = createForm.value.tagsInput
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0)

    await postsStore.createPost({
      title: createForm.value.title,
      content: createForm.value.content,
      tags,
      status: PostStatus.PENDING_REVIEW
    })

    ElMessage.success('帖子已提交审核')
    showCreatePost.value = false
    resetCreateForm()
    fetchPosts()
  } catch (error: any) {
    if (error.fields) return // 表单验证错误
    ElMessage.error('发布失败，请稍后重试')
  } finally {
    creating.value = false
  }
}

const handleCreateDraft = async () => {
  if (!createFormRef.value) return

  try {
    await createFormRef.value.validate()
    creating.value = true

    const tags = createForm.value.tagsInput
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0)

    await postsStore.createPost({
      title: createForm.value.title,
      content: createForm.value.content,
      tags,
      status: PostStatus.DRAFT
    })

    ElMessage.success('草稿已保存')
    showCreatePost.value = false
    resetCreateForm()
    fetchPosts()
  } catch (error: any) {
    if (error.fields) return
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    creating.value = false
  }
}

const resetCreateForm = () => {
  createForm.value = {
    title: '',
    content: '',
    tagsInput: ''
  }
  createFormRef.value?.clearValidate()
}

const handleLike = async (postId: number) => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }

  try {
    await postsStore.toggleLike(postId)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleFavorite = async (postId: number) => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }

  try {
    await postsStore.toggleFavorite(postId)
  } catch (error) {
    ElMessage.error('操作失败')
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
    case PostStatus.REJECTED: return '已驳回'
    case PostStatus.TAKEN_DOWN: return '已下架'
    default: return '未知'
  }
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const getAvatarUrl = (id: number) => {
  return `https://picsum.photos/seed/${id}/40/40`
}

onMounted(() => {
  fetchPosts()
})
</script>

<style lang="scss" scoped>
.community {
  max-width: 1000px;
  margin: 0 auto;
  animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.community-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;

  @media (max-width: 640px) {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0;
  letter-spacing: -0.025em;
}

.create-btn {
  background: $gradient-primary !important;
  border: none !important;
  box-shadow: $shadow-purple !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  transition: $transition-all !important;

  &:hover {
    box-shadow: 0 8px 24px rgba(124, 58, 237, 0.5) !important;
    transform: translateY(-1px);
  }
}

.filter-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid $border-subtle;
  flex-wrap: wrap;
}

.filter-tab {
  border-radius: 8px !important;
  font-weight: 500 !important;
  font-size: 0.8125rem !important;
  border-color: $border-default !important;
  color: $text-muted !important;
  background: transparent !important;
  transition: $transition-all !important;

  &:hover:not(.el-button--primary) {
    border-color: $primary-color !important;
    color: $primary-light !important;
    background: rgba(124, 58, 237, 0.08) !important;
  }

  &.el-button--primary {
    background: rgba(124, 58, 237, 0.2) !important;
    border-color: rgba(124, 58, 237, 0.4) !important;
    color: $primary-light !important;
  }
}

.create-post-dialog {
  :deep(.el-dialog) {
    background: $bg-card !important;
    border: 1px solid $border-strong !important;
    border-radius: $border-radius-xl !important;
  }

  :deep(.el-dialog__header) {
    padding: 1.5rem 1.5rem 1rem;
    border-bottom: 1px solid $border-default !important;
  }

  :deep(.el-dialog__title) {
    color: $text-primary !important;
    font-weight: 700 !important;
    font-size: 1.0625rem !important;
  }

  :deep(.el-dialog__body) {
    padding: 1.5rem;
  }
}

.title-input {
  :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid $border-default !important;
    border-radius: 10px !important;
    box-shadow: none !important;

    &.is-focus {
      border-color: $primary-color !important;
      box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.2) !important;
    }
  }

  :deep(.el-input__inner) {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: $text-primary !important;

    &::placeholder {
      color: $text-muted !important;
      font-weight: 400 !important;
    }
  }
}

.content-input {
  :deep(.el-textarea__inner) {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid $border-default !important;
    border-radius: 10px !important;
    resize: none !important;
    font-size: 0.9rem !important;
    line-height: 1.6 !important;
    color: $text-primary !important;

    &:focus {
      border-color: $primary-color !important;
      box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.2) !important;
    }

    &::placeholder {
      color: $text-muted !important;
    }
  }
}

.dialog-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

// ============================================
// Posts
// ============================================
.posts-container {
  min-height: 400px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.post-skeleton {
  background: linear-gradient(145deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 1.5rem;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  background: linear-gradient(145deg, rgba(255,255,255,0.03) 0%, transparent 100%);
  border: 1px dashed $border-default;
  border-radius: $border-radius;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.post-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 1.375rem 1.5rem;
  cursor: pointer;
  transition: $transition-all;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: $gradient-primary;
    border-radius: 3px 0 0 3px;
    opacity: 0;
    transition: opacity 0.25s ease;
  }

  &:hover {
    border-color: rgba(124, 58, 237, 0.25);
    background: linear-gradient(145deg, rgba(124, 58, 237, 0.06) 0%, rgba(255,255,255,0.02) 100%);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    transform: translateY(-2px);

    &::before {
      opacity: 1;
    }
  }
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.875rem;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.author-details {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.author-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: $text-primary;
  margin: 0;
}

.post-date {
  font-size: 0.725rem;
  color: $text-muted;
  margin: 0;
  font-family: 'IBM Plex Mono', monospace;
}

.status-tag {
  font-size: 0.7rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.04em !important;
}

.post-title {
  font-size: 1.0625rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 0.625rem 0;
  line-height: 1.45;
  letter-spacing: -0.01em;
  transition: $transition-colors;

  &:hover {
    color: $primary-light;
  }
}

.post-content {
  font-size: 0.875rem;
  color: $text-secondary;
  line-height: 1.65;
  margin: 0 0 0.875rem 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-bottom: 0.875rem;
}

.post-tag {
  background: rgba(124, 58, 237, 0.1) !important;
  border: 1px solid rgba(124, 58, 237, 0.2) !important;
  color: $primary-light !important;
  font-size: 0.7rem !important;
  font-weight: 600 !important;
  border-radius: 6px !important;
  padding: 0 0.5rem !important;
}

.post-actions {
  display: flex;
  gap: 1.25rem;
  padding-top: 0.75rem;
  border-top: 1px solid $border-subtle;
}

.action-btn {
  display: flex !important;
  align-items: center !important;
  gap: 0.375rem !important;
  color: $text-muted !important;
  font-size: 0.8125rem !important;
  padding: 0.25rem 0.5rem !important;
  border-radius: 6px !important;
  transition: $transition-all !important;
  cursor: pointer;

  &:hover {
    color: $primary-light !important;
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

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>