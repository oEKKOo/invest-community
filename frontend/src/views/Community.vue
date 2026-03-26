<template>
  <div class="community">
    <div class="community-header">
      <div class="header-content">
        <h2 class="page-title">社区论坛</h2>
        <p class="page-subtitle">分享投资观点、策略与市场观察</p>
      </div>
      <el-button 
        type="primary" 
        size="large"
        @click="showCreatePost = true"
        :icon="Plus"
        class="create-btn"
      >
        发布讨论
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
      <el-select
        v-model="selectedBoardId"
        clearable
        filterable
        placeholder="按板块筛选"
        class="board-filter-select"
        :loading="boardsLoading"
        @change="handleBoardFilterChange"
      >
        <el-option
          v-for="board in boardLeafOptions"
          :key="board.id"
          :label="board.name"
          :value="board.id"
        />
      </el-select>
    </div>

    <!-- 创建帖子对话框 -->
    <el-dialog
      v-model="showCreatePost"
      title="分享你的投资见解"
      width="800px"
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

        <el-form-item prop="contentType">
          <el-select v-model="createForm.contentType" style="width: 100%">
            <el-option label="普通帖子" value="NORMAL" />
            <el-option label="长文分析" value="LONGFORM" />
            <el-option label="投票调研" value="POLL" />
            <el-option label="实时讨论" value="LIVE" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="createForm.contentType === 'POLL'">
          <el-input v-model="createForm.poll.question" placeholder="投票问题，例如：你看好下周A股走势吗？" />
          <div style="display:flex; gap:8px; margin-top:8px;">
            <el-input v-for="(opt, idx) in createForm.poll.options" :key="idx" v-model="opt.text" :placeholder="`选项${idx + 1}`" />
          </div>
          <div style="display:flex; gap:8px; margin-top:8px;">
            <el-button size="small" @click="addPollOption">添加选项</el-button>
            <el-button size="small" @click="removePollOption" :disabled="createForm.poll.options.length <= 2">删除选项</el-button>
            <el-switch v-model="createForm.poll.allowMultiple" active-text="允许多选" />
          </div>
        </el-form-item>

        <el-form-item prop="tags">
          <div class="tags-input-wrapper">
            <el-input
              v-model="createForm.tagsInput"
              placeholder="添加标签，用逗号分隔（如：股票,ETF,投资策略）"
              class="tags-input"
              @keyup.enter="handleTagInput"
            />
            <div v-if="createForm.tagsInput" class="tags-preview">
              <el-tag
                v-for="(tag, index) in createForm.tagsInput.split(',').filter(t => t.trim())"
                :key="index"
                size="small"
                closable
                class="tag-preview-item"
                @close="removeTag(index)"
              >
                #{{ tag.trim() }}
              </el-tag>
            </div>
          </div>
        </el-form-item>

        <el-form-item prop="boardIds">
          <div class="asset-select-label">
            <el-icon style="color:#8B5CF6"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7h18M3 12h18M3 17h18"/></svg></el-icon>
            选择板块（支持多选，叶子节点）
          </div>
          <el-select
            v-model="createForm.boardIds"
            multiple
            filterable
            clearable
            placeholder="请选择讨论板块"
            style="width: 100%"
          >
            <el-option
              v-for="board in boardLeafOptions"
              :key="board.id"
              :label="board.name"
              :value="board.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <div class="asset-select-label">
            <el-icon style="color:#3B82F6"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></el-icon>
            关联标的（可选）
          </div>
          <AssetSelect v-model="createForm.assetIds" :max-count="5" />
        </el-form-item>

        <el-form-item>
          <div class="asset-select-label">附件上传（PDF/Excel/图片，需审核）</div>
          <el-upload
            multiple
            :auto-upload="false"
            :show-file-list="true"
            :on-change="handleAttachmentSelect"
          >
            <el-button>选择附件</el-button>
          </el-upload>
          <div v-if="createForm.attachmentIds.length" style="margin-top: 6px; color: #6b7280;">
            已上传附件数：{{ createForm.attachmentIds.length }}
          </div>
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
                class="author-clickable"
                @click.stop="$router.push({ name: 'UserProfile', params: { userId: post.authorId } })"
              >
                {{ post.authorName[0] }}
              </el-avatar>
              <div
                class="author-details author-clickable"
                @click.stop="$router.push({ name: 'UserProfile', params: { userId: post.authorId } })"
              >
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

          <div class="post-tags" v-if="post.tags?.length || post.assets?.length || post.boards?.length">
            <el-tag
              v-for="board in (post.boards || [])"
              :key="`board-${board.id}`"
              size="small"
              type="warning"
              class="post-tag"
            >
              {{ board.name }}
            </el-tag>
            <el-tag 
              v-for="tag in post.tags" 
              :key="tag"
              size="small"
              class="post-tag"
            >
              #{{ tag }}
            </el-tag>
            <!-- 关联标的标签 -->
            <router-link
              v-for="asset in (post.assets || [])"
              :key="asset.id"
              :to="{ name: 'AssetDetail', params: { assetId: asset.id } }"
              class="asset-link-tag"
              @click.stop
            >
              <el-tag size="small" :type="getAssetMarketTagType(asset.market)" class="asset-tag">
                {{ asset.code }}
                <span class="asset-tag-name">{{ asset.name }}</span>
              </el-tag>
            </router-link>
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

            <el-button
              v-if="authStore.isLoggedIn"
              type="text"
              @click.stop="openReportDialog('POST', post.id, post.title)"
              class="action-btn report-btn"
            >
              <el-icon><Warning /></el-icon>
              <span>举报</span>
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

    <!-- 举报对话框 -->
    <ReportDialog
      v-model="showReportDialog"
      :target-type="reportTargetType || 'POST'"
      :target-id="reportTargetId || 0"
      :target-summary="reportTargetSummary"
      @submitted="handleReportSubmitted"
    />
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted, computed } from 'vue'
import { usePostsStore } from '../stores/posts'
import { useAuthStore } from '../stores/auth'
import { PostStatus } from '../types'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import * as postsApi from '@/api/posts'
import {
  Plus,
  Star,
  ChatLineRound,
  StarFilled,
  Warning
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import AssetSelect from '@/components/market/AssetSelect.vue'
import ReportDialog from '@/components/ReportDialog.vue'

const postsStore = usePostsStore()
const authStore = useAuthStore()

// 状态
const showCreatePost = ref(false)
const creating = ref(false)
const activeFilter = ref<string>('ALL')
const currentPage = ref(1)
const pageSize = ref(20)
const selectedBoardId = ref<number | undefined>()
const boardsLoading = ref(false)
const boardTree = ref<any[]>([])
const boardLeafOptions = ref<any[]>([])

// 表单
const createFormRef = ref<FormInstance>()
const createForm = ref({
  title: '',
  content: '',
  tagsInput: '',
  assetIds: [] as number[],
  boardIds: [] as number[],
  contentType: 'NORMAL' as 'NORMAL' | 'LONGFORM' | 'POLL' | 'LIVE',
  attachmentIds: [] as number[],
  poll: {
    question: '',
    allowMultiple: false,
    options: [{ text: '' }, { text: '' }] as Array<{ text: string }>
  }
})

const createRules: FormRules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { min: 5, max: 100, message: '标题长度应在5-100字符之间', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入内容', trigger: 'blur' },
    { min: 10, message: '内容至少10个字', trigger: 'blur' }
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

  if (selectedBoardId.value) {
    params.boardId = selectedBoardId.value
  }

  return params
})

// 方法
const handleFilterChange = (filter: string) => {
  activeFilter.value = filter
  currentPage.value = 1
  fetchPosts()
}

const handleBoardFilterChange = () => {
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

const collectBoardLeaves = (nodes: any[] = [], result: any[] = []) => {
  for (const node of nodes) {
    const children = node.children || []
    if (!children.length) {
      result.push(node)
    } else {
      collectBoardLeaves(children, result)
    }
  }
  return result
}

const fetchBoards = async () => {
  boardsLoading.value = true
  try {
    const res = await postsApi.getBoards()
    boardTree.value = res.items || []
    boardLeafOptions.value = collectBoardLeaves(boardTree.value, [])
  } catch (error) {
    ElMessage.error('获取板块列表失败')
  } finally {
    boardsLoading.value = false
  }
}

const addPollOption = () => {
  createForm.value.poll.options.push({ text: '' })
}

const removePollOption = () => {
  if (createForm.value.poll.options.length > 2) {
    createForm.value.poll.options.pop()
  }
}

const handleAttachmentSelect = async (uploadFile: any) => {
  if (!uploadFile?.raw) return
  try {
    const attachment = await postsApi.uploadContentAttachment(uploadFile.raw as File)
    createForm.value.attachmentIds.push(attachment.id)
    ElMessage.success(`附件 ${attachment.original_name || uploadFile.name} 上传成功`)
  } catch (e) {
    ElMessage.error('附件上传失败')
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
      status: PostStatus.PENDING_REVIEW,
      assetIds: createForm.value.assetIds.length > 0 ? createForm.value.assetIds : undefined,
      boardIds: createForm.value.boardIds.length > 0 ? createForm.value.boardIds : undefined,
      contentType: createForm.value.contentType,
      formatType: createForm.value.contentType === 'LONGFORM' ? 'RICH_TEXT' : 'PLAIN',
      poll: createForm.value.contentType === 'POLL'
        ? { question: createForm.value.poll.question, allowMultiple: createForm.value.poll.allowMultiple, options: createForm.value.poll.options }
        : undefined,
      attachmentIds: createForm.value.attachmentIds.length ? createForm.value.attachmentIds : undefined
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
      status: PostStatus.DRAFT,
      assetIds: createForm.value.assetIds.length > 0 ? createForm.value.assetIds : undefined,
      boardIds: createForm.value.boardIds.length > 0 ? createForm.value.boardIds : undefined,
      contentType: createForm.value.contentType,
      formatType: createForm.value.contentType === 'LONGFORM' ? 'RICH_TEXT' : 'PLAIN',
      poll: createForm.value.contentType === 'POLL'
        ? { question: createForm.value.poll.question, allowMultiple: createForm.value.poll.allowMultiple, options: createForm.value.poll.options }
        : undefined,
      attachmentIds: createForm.value.attachmentIds.length ? createForm.value.attachmentIds : undefined
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
    tagsInput: '',
    assetIds: [],
    boardIds: [],
    contentType: 'NORMAL',
    attachmentIds: [],
    poll: {
      question: '',
      allowMultiple: false,
      options: [{ text: '' }, { text: '' }]
    }
  }
  createFormRef.value?.clearValidate()
}

const handleTagInput = () => {
  // 标签输入处理（可选，用于实时预览）
}

const removeTag = (index: number) => {
  const tags = createForm.value.tagsInput.split(',').filter(t => t.trim())
  tags.splice(index, 1)
  createForm.value.tagsInput = tags.join(',')
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

// 举报
const showReportDialog = ref(false)
const reportTargetType = ref<'POST' | 'COMMENT' | null>(null)
const reportTargetId = ref<number | null>(null)
const reportTargetSummary = ref('')

const openReportDialog = (targetType: 'POST' | 'COMMENT', targetId: number, summary: string) => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  reportTargetType.value = targetType
  reportTargetId.value = targetId
  reportTargetSummary.value = summary || '帖子'
  showReportDialog.value = true
}

const handleReportSubmitted = () => {
  // 举报提交成功后的回调
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

const getAssetMarketTagType = (market?: string) => {
  const m = market?.toUpperCase()
  if (m === 'SH' || m === 'SZ') return 'danger'
  if (m === 'HK') return 'warning'
  if (m === 'US') return 'primary'
  return 'info'
}

onMounted(() => {
  fetchBoards()
  fetchPosts()
})
</script>

<style lang="scss" scoped>
.community {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 1rem;
  animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.community-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  gap: 1.5rem;

  @media (max-width: 640px) {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: $apple-text-primary;
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.025em;
  line-height: 1.2;
}

.page-subtitle {
  font-size: 0.9375rem;
  color: $apple-text-secondary;
  margin: 0;
  line-height: 1.5;
  font-weight: 400;
}

.create-btn {
  background: $gradient-primary !important;
  border: none !important;
  box-shadow: $shadow-purple !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  transition: $transition-all !important;

  &:hover {
    box-shadow: 0 8px 24px rgba(29, 78, 216, 0.3) !important;
    transform: translateY(-1px);
  }
}

.filter-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-wrap: wrap;
}

.board-filter-select {
  min-width: 220px;
}

.filter-tab {
  border-radius: 10px !important;
  font-weight: 500 !important;
  font-size: 0.8125rem !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  color: $apple-text-secondary !important;
  background: transparent !important;
  transition: all 0.2s ease !important;
  padding: 0.5rem 1rem !important;

  &:hover:not(.el-button--primary) {
    border-color: $apple-accent !important;
    color: $apple-accent !important;
    background: rgba(0, 113, 227, 0.06) !important;
  }

  &.el-button--primary {
    background: rgba(0, 113, 227, 0.1) !important;
    border-color: rgba(0, 113, 227, 0.2) !important;
    color: $apple-accent !important;
  }
}

.create-post-dialog {
  :deep(.el-dialog) {
    background: rgba(255, 255, 255, 0.95) !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08) !important;
  }

  :deep(.el-dialog__header) {
    padding: 2rem 2.5rem 1.5rem;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
  }

  :deep(.el-dialog__title) {
    color: $apple-text-primary !important;
    font-weight: 700 !important;
    font-size: 1.25rem !important;
    letter-spacing: -0.015em;
  }

  :deep(.el-dialog__body) {
    padding: 2rem 2.5rem;
  }

  :deep(.el-dialog__footer) {
    padding: 1.5rem 2.5rem 2rem;
    border-top: 1px solid rgba(0, 0, 0, 0.06) !important;
  }
}

.title-input {
  :deep(.el-input__wrapper) {
    background: rgba(245, 245, 247, 0.8) !important;
    border: 1px solid rgba(0, 0, 0, 0.06) !important;
    border-radius: 14px !important;
    box-shadow: none !important;
    padding: 0.875rem 1.25rem !important;
    transition: all 0.2s ease !important;

    &.is-focus {
      border-color: $apple-accent !important;
      box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.1) !important;
      background: rgba(255, 255, 255, 0.95) !important;
    }
  }

  :deep(.el-input__inner) {
    font-size: 1.125rem !important;
    font-weight: 600 !important;
    color: $apple-text-primary !important;
    font-family: $apple-font-family !important;

    &::placeholder {
      color: $apple-text-tertiary !important;
      font-weight: 400 !important;
    }
  }
}

.content-input {
  :deep(.el-textarea__inner) {
    background: rgba(245, 245, 247, 0.8) !important;
    border: 1px solid rgba(0, 0, 0, 0.06) !important;
    border-radius: 14px !important;
    resize: none !important;
    font-size: 1rem !important;
    line-height: 1.75 !important;
    color: $apple-text-primary !important;
    padding: 1.25rem 1.5rem !important;
    font-family: $apple-font-family !important;
    min-height: 200px !important;
    transition: all 0.2s ease !important;

    &:focus {
      border-color: $apple-accent !important;
      box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.1) !important;
      background: rgba(255, 255, 255, 0.95) !important;
    }

    &::placeholder {
      color: $apple-text-tertiary !important;
      font-weight: 400 !important;
    }
  }
}

.dialog-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;

  :deep(.el-button) {
    border-radius: 10px !important;
    font-weight: 500 !important;
    padding: 0.625rem 1.5rem !important;
    transition: all 0.2s ease !important;
  }

  :deep(.el-button--default) {
    color: $apple-text-secondary !important;
    border-color: rgba(0, 0, 0, 0.1) !important;
    background: transparent !important;

    &:hover {
      border-color: $apple-accent !important;
      color: $apple-accent !important;
      background: rgba(0, 113, 227, 0.06) !important;
    }
  }

  :deep(.el-button--primary) {
    background: $apple-accent !important;
    border-color: $apple-accent !important;

    &:hover {
      background: rgba(0, 113, 227, 0.9) !important;
    }
  }
}

.tags-input-wrapper {
  width: 100%;
}

.tags-input {
  margin-bottom: 0.75rem;

  :deep(.el-input__wrapper) {
    background: rgba(245, 245, 247, 0.8) !important;
    border: 1px solid rgba(0, 0, 0, 0.06) !important;
    border-radius: 14px !important;
    transition: all 0.2s ease !important;

    &.is-focus {
      border-color: $apple-accent !important;
      box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.1) !important;
      background: rgba(255, 255, 255, 0.95) !important;
    }
  }

  :deep(.el-input__inner) {
    font-size: 0.9375rem !important;
    color: $apple-text-primary !important;
    font-family: $apple-font-family !important;

    &::placeholder {
      color: $apple-text-tertiary !important;
    }
  }
}

.tags-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.tag-preview-item {
  background: rgba(100, 116, 139, 0.1) !important;
  border: 1px solid rgba(100, 116, 139, 0.15) !important;
  color: rgba(100, 116, 139, 0.9) !important;
  border-radius: 10px !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  padding: 0.25rem 0.625rem !important;
  font-family: $apple-font-family !important;
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
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 1.5rem;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px dashed rgba(0, 0, 0, 0.1);
  border-radius: 16px;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.post-card {
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 1.5rem 1.75rem;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);

  &:hover {
    border-color: rgba(0, 113, 227, 0.15);
    background: rgba(255, 255, 255, 0.92);
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    transform: translateY(-2px);
  }
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
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
  font-size: 0.8125rem;
  font-weight: 600;
  color: $apple-text-primary;
  margin: 0;
  line-height: 1.4;
}

.post-date {
  font-size: 0.75rem;
  color: $apple-text-tertiary;
  margin: 0;
  font-family: 'IBM Plex Mono', monospace;
  line-height: 1.4;
}

.status-tag {
  font-size: 0.6875rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.02em !important;
  padding: 0.25rem 0.625rem !important;
  border-radius: 10px !important;
  border: none !important;
  
  // 已发布：浅绿色
  &.el-tag--success {
    background: rgba(22, 163, 74, 0.12) !important;
    color: rgba(22, 163, 74, 0.9) !important;
  }
  
  // 审核中：浅橙色
  &.el-tag--warning {
    background: rgba(217, 119, 6, 0.12) !important;
    color: rgba(217, 119, 6, 0.9) !important;
  }
  
  // 草稿：浅灰蓝色
  &.el-tag--info {
    background: rgba(100, 116, 139, 0.12) !important;
    color: rgba(100, 116, 139, 0.9) !important;
  }
}

.post-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: $apple-text-primary;
  margin: 0 0 0.75rem 0;
  line-height: 1.4;
  letter-spacing: -0.015em;
  transition: color 0.2s ease;

  &:hover {
    color: $apple-accent;
  }
}

.post-content {
  font-size: 0.9375rem;
  color: $apple-text-secondary;
  line-height: 1.75;
  margin: 0 0 1rem 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  overflow: hidden;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

// Topic Tag (内容标签) - 浅灰蓝胶囊
.post-tag {
  background: rgba(100, 116, 139, 0.1) !important;
  border: 1px solid rgba(100, 116, 139, 0.15) !important;
  color: rgba(100, 116, 139, 0.9) !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  border-radius: 10px !important;
  padding: 0.25rem 0.625rem !important;
  font-family: $apple-font-family !important;
}

// Asset Tag (关联标的) - 淡红/淡蓝/淡灰金融风
.asset-link-tag {
  text-decoration: none;

  .asset-tag {
    cursor: pointer;
    border-radius: 10px !important;
    padding: 0.25rem 0.625rem !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    border: none !important;
    font-family: $apple-font-family !important;

    .asset-tag-name {
      font-size: 0.6875rem;
      opacity: 0.85;
      margin-left: 4px;
    }

    // 股票市场 - 淡红
    &.el-tag--danger {
      background: rgba(232, 93, 93, 0.12) !important;
      color: rgba(232, 93, 93, 0.95) !important;
    }

    // 港股 - 淡橙
    &.el-tag--warning {
      background: rgba(217, 119, 6, 0.12) !important;
      color: rgba(217, 119, 6, 0.95) !important;
    }

    // 美股 - 淡蓝
    &.el-tag--primary {
      background: rgba(0, 113, 227, 0.12) !important;
      color: rgba(0, 113, 227, 0.95) !important;
    }

    // 其他 - 淡灰
    &.el-tag--info {
      background: rgba(100, 116, 139, 0.12) !important;
      color: rgba(100, 116, 139, 0.95) !important;
    }

    &:hover {
      opacity: 0.85;
      transform: translateY(-1px);
    }
  }
}

.asset-select-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  color: $apple-text-secondary;
  margin-bottom: 0.75rem;
  width: 100%;
  font-weight: 500;
}

.post-actions {
  display: flex;
  gap: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  align-items: center;
}

.action-btn {
  display: flex !important;
  align-items: center !important;
  gap: 0.375rem !important;
  color: $apple-text-tertiary !important;
  font-size: 0.8125rem !important;
  padding: 0.375rem 0.5rem !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
  cursor: pointer;
  background: transparent !important;
  border: none !important;
  font-weight: 500 !important;

  :deep(.el-icon) {
    font-size: 1rem;
  }

  span {
    font-size: 0.8125rem;
  }

  &:hover {
    color: $apple-accent !important;
    background: rgba(0, 113, 227, 0.08) !important;
  }

  &.liked {
    color: rgba(232, 93, 93, 0.9) !important;
    
    &:hover {
      background: rgba(232, 93, 93, 0.1) !important;
    }
  }

  &.favorited {
    color: rgba(217, 119, 6, 0.9) !important;
    
    &:hover {
      background: rgba(217, 119, 6, 0.1) !important;
    }
  }

  &.report-btn {
    margin-left: auto;
    opacity: 0.6;
    
    &:hover {
      opacity: 1;
      color: $apple-text-secondary !important;
      background: rgba(0, 0, 0, 0.04) !important;
    }
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




