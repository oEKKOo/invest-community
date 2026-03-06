<template>
  <div class="admin-panel">
    <!-- 页面头部 -->
    <div class="admin-header">
      <div class="header-left">
        <div class="admin-icon">
          <el-icon><Setting /></el-icon>
        </div>
        <div>
          <h2 class="page-title">管理控制台</h2>
          <p class="page-subtitle">内容审核与社区治理中心</p>
        </div>
      </div>
    </div>

    <!-- 数据监控入口 -->
    <div class="data-monitor-entry">
      <router-link :to="{ name: 'DataMonitor' }" class="monitor-link-card">
        <div class="monitor-icon">📊</div>
        <div class="monitor-info">
          <h4>市场数据监控</h4>
          <p>查看行情状态、任务日志、手动触发数据同步</p>
        </div>
        <el-icon class="monitor-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg></el-icon>
      </router-link>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card pending">
        <div class="stat-content">
          <p class="stat-label">待审核帖子</p>
          <p class="stat-value">{{ adminStats?.pendingPostsCount || 0 }}</p>
        </div>
        <div class="stat-icon">
          <el-icon><Clock /></el-icon>
        </div>
      </div>

      <div class="stat-card reports">
        <div class="stat-content">
          <p class="stat-label">待处理举报</p>
          <p class="stat-value">{{ adminStats?.openReportsCount || 0 }}</p>
        </div>
        <div class="stat-icon">
          <el-icon><Warning /></el-icon>
        </div>
      </div>

      <div class="stat-card users">
        <div class="stat-content">
          <p class="stat-label">新用户(24h)</p>
          <p class="stat-value">{{ adminStats?.newUsers24h || 0 }}</p>
        </div>
        <div class="stat-icon">
          <el-icon><User /></el-icon>
        </div>
      </div>
    </div>

    <!-- 内容审核区域 -->
    <div class="content-section">
      <div class="section-header">
        <h3 class="section-title">内容审核队列</h3>
        <p class="section-subtitle">审核待发布内容</p>
      </div>

      <div class="review-container">
        <div v-if="loading" class="loading-container">
          <div v-for="i in 3" :key="i" class="review-skeleton">
            <el-skeleton :rows="3" animated />
          </div>
        </div>

        <div v-else-if="pendingPosts.length === 0" class="empty-review">
          <el-icon class="empty-icon"><CircleCheck /></el-icon>
          <p>太棒了！审核队列为空</p>
        </div>

          <div v-else class="reviews-list">
          <div 
            v-for="post in pendingPosts"
            :key="post.id"
            class="review-card"
          >
            <div class="review-content">
              <div class="post-meta">
                <el-avatar 
                  :src="getAvatarUrl(post.authorId)" 
                  :size="32"
                  class="author-clickable"
                  @click.stop="$router.push({ name: 'UserProfile', params: { userId: post.authorId } })"
                >
                  {{ post.authorName[0] }}
                </el-avatar>
                <div
                  class="meta-info author-clickable"
                  @click.stop="$router.push({ name: 'UserProfile', params: { userId: post.authorId } })"
                >
                  <p class="author-name">{{ post.authorName }}</p>
                  <p class="post-date">{{ formatDate(post.createdAt) }}</p>
                </div>
              </div>

              <h4 class="review-title">{{ post.title }}</h4>
              <p class="review-text">{{ post.content }}</p>

              <div class="post-tags" v-if="post.tags?.length">
                <el-tag 
                  v-for="tag in post.tags" 
                  :key="tag"
                  size="small"
                  class="tag-item"
                >
                  #{{ tag }}
                </el-tag>
              </div>
            </div>

            <div class="review-actions">
              <el-button
                type="success"
                @click="handleReview(post.id, 'PUBLISHED')"
                :loading="reviewingIds.includes(post.id)"
                class="approve-btn"
              >
                <el-icon><Check /></el-icon>
                通过
              </el-button>

              <el-button
                type="danger"
                plain
                @click="showRejectDialog(post)"
                :loading="reviewingIds.includes(post.id)"
                class="reject-btn"
              >
                <el-icon><Close /></el-icon>
                驳回
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 驳回原因对话框-->
    <el-dialog
      v-model="showRejectForm"
      title="驳回原因"
      width="400px"
    >
      <el-form :model="rejectForm" label-width="0">
        <el-form-item>
          <el-input
            v-model="rejectForm.reason"
            type="textarea"
            :rows="4"
              placeholder="请说明驳回原因..."
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showRejectForm = false">取消</el-button>
          <el-button 
            type="danger" 
            @click="confirmReject"
            :loading="rejecting"
          >
            确认驳回
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 举报处理中心 -->
    <div class="reports-section">
      <div class="section-header">
        <h3 class="section-title">举报处理中心</h3>
        <p class="section-subtitle">查看并处理用户举报</p>
      </div>
      <div class="reports-container">
        <el-skeleton v-if="loadingReports" :rows="4" animated class="reports-skeleton" />
        <el-empty v-else-if="!pendingReports.length" description="暂无待处理举报" />
        <el-table
          v-else
          :data="pendingReports"
          border
          size="small"
          class="reports-table"
        >
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="targetType" label="目标类型" width="100" />
          <el-table-column prop="targetId" label="目标ID" width="90" />
          <el-table-column prop="reporterName" label="举报人" width="120" />
          <el-table-column prop="reason" label="原因">
            <template #default="{ row }">
              <span class="report-reason">{{ row.reason }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="createdAt" label="时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.createdAt) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button
                size="small"
                type="success"
                @click="handleResolveReport(row, 'VALID')"
              >
                有效
              </el-button>
              <el-button
                size="small"
                @click="handleResolveReport(row, 'INVALID')"
              >
                无效
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as adminApi from '../api/admin'
import type { Post, AdminStats, Report } from '../types'
import {
  Setting,
  Clock,
  Warning,
  User,
  CircleCheck,
  Check,
  Close,
  InfoFilled
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

// 状态
const loading = ref(false)
const pendingPosts = ref<Post[]>([])
const adminStats = ref<AdminStats | null>(null)
const reviewingIds = ref<number[]>([])
const showRejectForm = ref(false)
const rejecting = ref(false)

// 举报处理
const loadingReports = ref(false)
const pendingReports = ref<Report[]>([])

// 驳回表单
const rejectForm = ref({
  postId: 0,
  reason: ''
})

// 方法
const fetchPendingPosts = async () => {
  loading.value = true
  try {
    const response = await adminApi.getPendingPosts()
    pendingPosts.value = response.items
  } catch (error) {
    ElMessage.error('获取待审核帖子失败')
  } finally {
    loading.value = false
  }
}

const fetchAdminStats = async () => {
  try {
    adminStats.value = await adminApi.getAdminStats()
  } catch (error) {
    ElMessage.error('获取统计数据失败')
  }
}

const fetchPendingReports = async () => {
  loadingReports.value = true
  try {
    const res = await adminApi.getPendingReports()
    pendingReports.value = res.items
  } catch (error) {
    ElMessage.error('获取待处理举报失败')
  } finally {
    loadingReports.value = false
  }
}

const handleReview = async (postId: number, status: string) => {
  reviewingIds.value.push(postId)
  
  try {
    await adminApi.reviewPost(postId, { status })
    
    // 从列表中移除已审核的帖子
    pendingPosts.value = pendingPosts.value.filter(p => p.id !== postId)
    
    ElMessage.success(status === 'PUBLISHED' ? '帖子已通过审核' : '帖子已驳回')
    
    // 更新统计数据
    fetchAdminStats()
  } catch (error) {
    ElMessage.error('审核操作失败')
  } finally {
    reviewingIds.value = reviewingIds.value.filter(id => id !== postId)
  }
}

const showRejectDialog = (post: Post) => {
  rejectForm.value = {
    postId: post.id,
    reason: ''
  }
  showRejectForm.value = true
}

const confirmReject = async () => {
  if (!rejectForm.value.reason.trim()) {
    ElMessage.warning('请填写驳回原因')
    return
  }

  rejecting.value = true
  
  try {
    await adminApi.reviewPost(rejectForm.value.postId, {
      status: 'REJECTED' as any,
      rejectReason: rejectForm.value.reason
    })

    // 从列表中移除
    pendingPosts.value = pendingPosts.value.filter(p => p.id !== rejectForm.value.postId)
    
    ElMessage.success('帖子已驳回')
    showRejectForm.value = false
    
    // 更新统计数据
    fetchAdminStats()
  } catch (error) {
    ElMessage.error('驳回操作失败')
  } finally {
    rejecting.value = false
  }
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const getAvatarUrl = (id: number) => {
  return `https://picsum.photos/seed/${id}/40/40`
}

onMounted(() => {
  fetchPendingPosts()
  fetchAdminStats()
  fetchPendingReports()
})

const handleResolveReport = async (report: Report, result: 'VALID' | 'INVALID') => {
  try {
    await adminApi.handleReport(report.id, {
      status: 'RESOLVED',
      result,
      handleResult: result === 'VALID' ? '举报成立，已记录处理结果' : '举报不成立'
    })
    pendingReports.value = pendingReports.value.filter(r => r.id !== report.id)
    ElMessage.success('举报已处理')
    fetchAdminStats()
  } catch (error) {
    ElMessage.error('处理举报失败')
  }
}
</script>

<style lang="scss" scoped>
.admin-panel {
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.3s ease-out;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.admin-icon {
  width: 3rem;
  height: 3rem;
  background: #fef2f2;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #dc2626;
  font-size: 1.5rem;
}

.page-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
}

.page-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}

.data-monitor-entry {
  margin-bottom: 0.25rem;

  .monitor-link-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.25rem;
    background: rgba(29, 78, 216, 0.06);
    border: 1px solid rgba(29, 78, 216, 0.12);
    border-radius: 12px;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;

    &:hover {
      background: rgba(124, 58, 237, 0.14);
      border-color: rgba(29, 78, 216, 0.22);
    }

    .monitor-icon {
      font-size: 1.5rem;
      flex-shrink: 0;
    }

    .monitor-info {
      flex: 1;

      h4 {
        font-size: 0.9rem;
        font-weight: 600;
        color: #3B82F6;
        margin: 0 0 3px;
      }

      p {
        font-size: 0.78rem;
        color: #6B7A99;
        margin: 0;
      }
    }

    .monitor-arrow {
      color: #6B7A99;
      flex-shrink: 0;
    }
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;

  &.pending {
    border-left: 4px solid #f59e0b;
  }

  &.reports {
    border-left: 4px solid #ef4444;
  }

  &.users {
    border-left: 4px solid #2563eb;
  }
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 0.5rem 0;
}

.stat-value {
  font-size: 1.875rem;
  font-weight: black;
  margin: 0;

  .pending & {
    color: #f59e0b;
  }

  .reports & {
    color: #ef4444;
  }

  .users & {
    color: #2563eb;
  }
}

.stat-icon {
  font-size: 2rem;
  opacity: 0.6;

  .pending & {
    color: #f59e0b;
  }

  .reports & {
    color: #ef4444;
  }

  .users & {
    color: #2563eb;
  }
}

.content-section {
  background: white;
  border-radius: 1rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 2rem;
}

.section-header {
  padding: 1.5rem;
  border-bottom: 1px solid #f3f4f6;
}

.section-title {
  font-size: 1.125rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
}

.section-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}

.review-container {
  min-height: 300px;
}

.loading-container {
  padding: 1.5rem;
}

.review-skeleton {
  padding: 1.5rem;
  border-bottom: 1px solid #f3f4f6;

  &:last-child {
    border-bottom: none;
  }
}

.empty-review {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #6b7280;
}

.empty-icon {
  font-size: 4rem;
  color: #10b981;
  margin-bottom: 1rem;
}

.reviews-list {
  border-top: 1px solid #f3f4f6;
}

.reviews-list > * + * {
  border-top: 1px solid #f3f4f6;
}

.review-card {
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem;
  transition: background-color 0.2s ease-in-out;

  &:hover {
    background: #f9fafb;
  }

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
  }
}

.review-content {
  flex: 1;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.meta-info {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.author-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.post-date {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0;
}

.review-title {
  font-size: 1.125rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
}

.review-text {
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
  margin: 0 0 0.75rem 0;
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
}

.tag-item {
  background: #f3f4f6;
  border: none;
  color: #6b7280;
  font-size: 0.75rem;
}

.review-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-self: flex-start;

  @media (max-width: 768px) {
    flex-direction: row;
    justify-content: flex-end;
  }
}

.approve-btn,
.reject-btn {
  min-width: 80px;
}

.dialog-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.alerts-section {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.alert-card {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: #fef2f2;
  border-radius: 0.75rem;
  border: 1px solid #fecaca;
}

.alert-icon {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  background: #fee2e2;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #dc2626;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #991b1b;
  margin: 0 0 0.25rem 0;
}

.alert-description {
  font-size: 0.75rem;
  color: #7f1d1d;
  line-height: 1.4;
  margin: 0 0 0.5rem 0;
}

.alert-actions {
  display: flex;
  gap: 1rem;
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

