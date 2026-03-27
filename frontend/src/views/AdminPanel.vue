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
      <router-link :to="{ name: 'ModerationQueue' }" class="monitor-link-card">
        <div class="monitor-icon">🛡️</div>
        <div class="monitor-info">
          <h4>可疑内容队列</h4>
          <p>查看自动审核命中与人工决策队列</p>
        </div>
      </router-link>
      <router-link :to="{ name: 'UserRiskCenter' }" class="monitor-link-card">
        <div class="monitor-icon">👥</div>
        <div class="monitor-info">
          <h4>用户风险中心</h4>
          <p>监控用户行为风险、警告与积分调整</p>
        </div>
      </router-link>
      <router-link :to="{ name: 'AnalyticsCenter' }" class="monitor-link-card">
        <div class="monitor-icon">📈</div>
        <div class="monitor-info">
          <h4>运营数据分析</h4>
          <p>查看活跃度、话题热度与参与度报告</p>
        </div>
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
        <el-form-item label="审核标签">
          <div class="review-tags">
            <el-tag
              v-for="tag in REVIEW_TAG_OPTIONS"
              :key="tag"
              size="small"
              :type="rejectForm.tag === tag ? 'danger' : 'info'"
              class="tag-item clickable"
              @click="selectReviewTag(tag)"
            >
              {{ tag }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="原因模板">
          <div class="reason-templates">
            <el-tag
              v-for="tpl in REJECT_REASON_TEMPLATES"
              :key="tpl"
              size="small"
              class="tag-item clickable"
              @click="applyReasonTemplate(tpl)"
            >
              {{ tpl }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="补充说明">
          <el-input
            v-model="rejectForm.reason"
            type="textarea"
            :rows="4"
            placeholder="可补充具体问题说明，例如“请删除收益截图中的账号信息”等"
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

    <!-- 用户治理操作对话框 -->
    <el-dialog
      v-model="moderationDialogVisible"
      :title="
        moderationAction === 'MUTE'
          ? '禁言用户'
          : moderationAction === 'BAN'
          ? '封禁用户'
          : moderationAction === 'UNMUTE'
          ? '解除禁言'
          : '解除封禁'
      "
      width="420px"
    >
      <p v-if="moderationTargetUser" class="moderation-dialog-text">
        对 <strong>{{ moderationTargetUser.displayName || moderationTargetUser.username }}</strong>
        执行
        <strong>
          {{
            moderationAction === 'MUTE'
              ? '禁言 7 天'
              : moderationAction === 'BAN'
              ? '封禁'
              : moderationAction === 'UNMUTE'
              ? '解除禁言'
              : '解除封禁'
          }}
        </strong>
        操作。
      </p>
      <el-input
        v-model="moderationReason"
        type="textarea"
        :rows="3"
        placeholder="可填写该操作的原因说明，方便后续追溯（选填）"
      />
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="moderationDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmModeration">确认</el-button>
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

    <!-- 用户治理中心 -->
    <div class="moderation-section">
      <div class="section-header">
        <h3 class="section-title">用户治理中心</h3>
        <p class="section-subtitle">查看并管理被禁言/封禁的用户</p>
      </div>
      <div class="moderation-container">
        <el-skeleton v-if="loadingModeration" :rows="4" animated class="reports-skeleton" />
        <el-empty v-else-if="!moderatedUsers.length" description="当前暂无被禁言或封禁的用户" />
        <el-table
          v-else
          :data="moderatedUsers"
          border
          size="small"
          class="reports-table"
        >
          <el-table-column prop="id" label="用户ID" width="80" />
          <el-table-column prop="username" label="用户名" width="150" />
          <el-table-column prop="displayName" label="昵称" width="150" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="muteUntil" label="禁言截止" width="180">
            <template #default="{ row }">
              {{ row.muteUntil ? formatDate(row.muteUntil) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="最近操作" min-width="220">
            <template #default="{ row }">
              <div class="moderation-last">
                <div v-if="row.lastAction">
                  {{ row.lastAction }} · {{ row.lastOperator || '系统' }}
                </div>
                <div class="moderation-reason" v-if="row.lastReason">
                  {{ row.lastReason }}
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="260" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'MUTED'"
                size="small"
                type="primary"
                @click="openModerationAction(row, 'UNMUTE')"
              >
                解除禁言
              </el-button>
              <el-button
                v-if="row.status === 'BANNED'"
                size="small"
                type="primary"
                @click="openModerationAction(row, 'UNBAN')"
              >
                解除封禁
              </el-button>
              <el-button
                size="small"
                type="danger"
                plain
                @click="openModerationAction(row, 'BAN')"
              >
                封禁
              </el-button>
              <el-button
                size="small"
                type="warning"
                plain
                @click="openModerationAction(row, 'MUTE')"
              >
                禁言7天
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 板块管理 -->
    <div class="moderation-section">
      <div class="section-header">
        <h3 class="section-title">板块管理</h3>
        <p class="section-subtitle">动态新增、编辑、删除与查询板块</p>
      </div>
      <div class="moderation-container">
        <div class="dialog-footer" style="margin-bottom: 12px; justify-content: space-between;">
          <el-input
            v-model="boardKeyword"
            placeholder="搜索板块名称"
            clearable
            style="max-width: 240px"
          />
          <el-button type="primary" @click="openBoardDialog()">
            新增板块
          </el-button>
        </div>
        <el-skeleton v-if="loadingBoards" :rows="4" animated class="reports-skeleton" />
        <el-empty v-else-if="!filteredBoards.length" description="暂无板块数据" />
        <el-table
          v-else
          :data="filteredBoards"
          border
          size="small"
          class="reports-table"
        >
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="名称" min-width="180" />
          <el-table-column prop="board_type" label="类型" width="150" />
          <el-table-column label="父板块" width="150">
            <template #default="{ row }">
              {{ getBoardName(row.parentId) || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openBoardDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="handleDeleteBoard(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <el-dialog v-model="boardDialogVisible" :title="boardForm.id ? '编辑板块' : '新增板块'" width="520px">
      <el-form :model="boardForm" label-width="92px">
        <el-form-item label="名称">
          <el-input v-model="boardForm.name" />
        </el-form-item>
        <el-form-item label="Slug">
          <el-input v-model="boardForm.slug" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="boardForm.board_type" style="width: 100%">
            <el-option label="市场讨论区" value="MARKET" />
            <el-option label="主题专区" value="THEME" />
            <el-option label="公司研究专区" value="COMPANY_RESEARCH" />
            <el-option label="问答求助区" value="QA" />
          </el-select>
        </el-form-item>
        <el-form-item label="父板块">
          <el-select v-model="boardForm.parent" clearable style="width: 100%">
            <el-option v-for="board in boards" :key="board.id" :label="board.name" :value="board.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="boardForm.sort_order" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="boardForm.status" style="width: 100%">
            <el-option label="启用" value="ACTIVE" />
            <el-option label="停用" value="INACTIVE" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="boardForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="boardDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitBoardForm">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <div class="moderation-section">
      <div class="section-header">
        <h3 class="section-title">附件审核</h3>
        <p class="section-subtitle">审核帖子附件（PDF/Excel/图片）</p>
      </div>
      <div class="moderation-container">
        <el-skeleton v-if="loadingAttachments" :rows="4" animated class="reports-skeleton" />
        <el-empty v-else-if="!attachmentItems.length" description="暂无待审核附件" />
        <el-table v-else :data="attachmentItems" border size="small" class="reports-table">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="original_name" label="文件名" min-width="180" />
          <el-table-column prop="mime_type" label="类型" width="140" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column label="操作" width="280">
            <template #default="{ row }">
              <el-button size="small" @click="openAttachment(row)">查看</el-button>
              <el-button size="small" type="success" @click="reviewAttachment(row.id, 'APPROVED')">通过</el-button>
              <el-button size="small" type="danger" plain @click="reviewAttachment(row.id, 'REJECTED')">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 告警中心（从静态改为真实数据） -->
    <div class="alerts-section">
      <div class="section-header">
        <h3 class="section-title">告警中心</h3>
        <p class="section-subtitle">高风险内容与异常行为告警</p>
      </div>
      <div class="alerts-list">
        <el-skeleton v-if="loadingAlerts" :rows="3" animated />
        <el-empty v-else-if="!alerts.length" description="暂无告警" />
        <div
          v-else
          v-for="alert in alerts"
          :key="alert.id"
          class="alert-card"
        >
          <div class="alert-icon">
            <el-icon><InfoFilled /></el-icon>
          </div>
          <div class="alert-content">
            <h4 class="alert-title">
              [{{ alert.severity }}] {{ alert.title }}
            </h4>
            <p class="alert-description">
              {{ alert.description }}
            </p>
            <p class="alert-description">
              状态：{{ alert.status }} · 创建于 {{ formatDate(alert.created_at) }}
              <span v-if="alert.handled_by_name">
                · 处理人：{{ alert.handled_by_name }}
              </span>
            </p>
            <p v-if="alert.handle_result" class="alert-description">
              处理备注：{{ alert.handle_result }}
            </p>
            <div class="alert-actions">
              <el-button
                size="small"
                type="success"
                @click="handleAlertAction(alert, 'RESOLVED')"
                v-if="alert.status === 'OPEN'"
              >
                标记已处理
              </el-button>
              <el-button
                size="small"
                type="info"
                @click="handleAlertAction(alert, 'IGNORED')"
                v-if="alert.status === 'OPEN'"
              >
                忽略
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import * as adminApi from '../api/admin'
import type { Post, AdminStats, Report, Alert, ModeratedUser, Board } from '../types'
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

// 告警中心
const loadingAlerts = ref(false)
const alerts = ref<Alert[]>([])

// 驳回表单 & 审核标签
const REVIEW_TAG_OPTIONS = ['涉嫌广告', '高风险荐股', '收益截图存疑', '违规引流', '其他']
const REJECT_REASON_TEMPLATES = [
  '内容涉嫌广告推广，与社区主题不符',
  '内容存在高风险荐股/保证收益等表述',
  '收益截图或业绩展示缺乏真实性依据',
  '存在违规引流或导流至外部平台',
  '内容与社区规范不符，请根据规范修改后再次提交'
]

const rejectForm = ref({
  postId: 0,
  tag: '',
  reason: ''
})

// 用户治理
const loadingModeration = ref(false)
const moderatedUsers = ref<ModeratedUser[]>([])
const moderationDialogVisible = ref(false)
const moderationTargetUser = ref<ModeratedUser | null>(null)
const moderationAction = ref<'MUTE' | 'BAN' | 'UNMUTE' | 'UNBAN' | null>(null)
const moderationReason = ref('')
const loadingAttachments = ref(false)
const attachmentItems = ref<any[]>([])
const loadingBoards = ref(false)
const boards = ref<Board[]>([])
const boardKeyword = ref('')
const boardDialogVisible = ref(false)
const boardForm = ref<any>({
  id: null,
  name: '',
  slug: '',
  board_type: 'MARKET',
  parent: null,
  sort_order: 0,
  status: 'ACTIVE',
  description: ''
})

const filteredBoards = computed(() => {
  const keyword = boardKeyword.value.trim().toLowerCase()
  if (!keyword) return boards.value
  return boards.value.filter(b => b.name.toLowerCase().includes(keyword))
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

const fetchModeratedUsers = async () => {
  loadingModeration.value = true
  try {
    const res = await adminApi.getModeratedUsers()
    moderatedUsers.value = res.items || []
  } catch (error) {
    ElMessage.error('获取用户治理数据失败')
  } finally {
    loadingModeration.value = false
  }
}

const fetchAlerts = async () => {
  loadingAlerts.value = true
  try {
    const res = await adminApi.getAlerts({ status: 'OPEN' })
    alerts.value = res.items || []
  } catch (error) {
    ElMessage.error('获取告警数据失败')
  } finally {
    loadingAlerts.value = false
  }
}

const fetchBoards = async () => {
  loadingBoards.value = true
  try {
    const res = await adminApi.getAdminBoards()
    boards.value = res.items || []
  } catch (error: any) {
    ElMessage.error(error?.message || '获取板块列表失败')
  } finally {
    loadingBoards.value = false
  }
}

const fetchAttachments = async () => {
  loadingAttachments.value = true
  try {
    const res = await adminApi.getAdminAttachments({ status: 'PENDING', page: 1, pageSize: 50 })
    attachmentItems.value = res.items || []
  } catch (error: any) {
    ElMessage.error(error?.message || '获取附件审核列表失败')
  } finally {
    loadingAttachments.value = false
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
    tag: '',
    reason: ''
  }
  showRejectForm.value = true
}

const confirmReject = async () => {
  if (!rejectForm.value.tag && !rejectForm.value.reason.trim()) {
    ElMessage.warning('请先选择一个审核标签或填写驳回原因')
    return
  }

  const mergedReason = rejectForm.value.tag
    ? `[${rejectForm.value.tag}] ${rejectForm.value.reason}`
    : rejectForm.value.reason

  rejecting.value = true
  
  try {
    await adminApi.reviewPost(rejectForm.value.postId, {
      status: 'REJECTED' as any,
      rejectReason: mergedReason
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
  fetchModeratedUsers()
  fetchBoards()
  fetchAttachments()
  fetchAlerts()
})

const openAttachment = (row: any) => {
  if (!row.fileUrl) {
    ElMessage.warning('附件地址不可用')
    return
  }
  window.open(row.fileUrl, '_blank')
}

const reviewAttachment = async (attachmentId: number, status: 'APPROVED' | 'REJECTED') => {
  try {
    await adminApi.reviewAttachment(attachmentId, {
      status,
      rejectReason: status === 'REJECTED' ? '内容不符合规范，请重新上传' : undefined
    })
    ElMessage.success(status === 'APPROVED' ? '已通过附件审核' : '已驳回附件')
    fetchAttachments()
  } catch (error: any) {
    ElMessage.error(error?.message || '附件审核失败')
  }
}

const getBoardName = (boardId?: number | null) => {
  if (!boardId) return ''
  const board = boards.value.find(b => b.id === boardId)
  return board?.name || ''
}

const openBoardDialog = (board?: Board) => {
  if (!board) {
    boardForm.value = {
      id: null,
      name: '',
      slug: '',
      board_type: 'MARKET',
      parent: null,
      sort_order: 0,
      status: 'ACTIVE',
      description: ''
    }
  } else {
    boardForm.value = {
      id: board.id,
      name: board.name,
      slug: board.slug,
      board_type: board.board_type,
      parent: board.parentId || null,
      sort_order: board.sort_order || 0,
      status: board.status || 'ACTIVE',
      description: board.description || ''
    }
  }
  boardDialogVisible.value = true
}

const submitBoardForm = async () => {
  if (!boardForm.value.name || !boardForm.value.slug) {
    ElMessage.warning('请填写板块名称和 Slug')
    return
  }
  const payload: any = {
    name: boardForm.value.name,
    slug: boardForm.value.slug,
    board_type: boardForm.value.board_type,
    parent: boardForm.value.parent,
    sort_order: boardForm.value.sort_order,
    status: boardForm.value.status,
    description: boardForm.value.description
  }
  try {
    if (boardForm.value.id) {
      await adminApi.updateBoard(boardForm.value.id, payload)
      ElMessage.success('板块更新成功')
    } else {
      await adminApi.createBoard(payload)
      ElMessage.success('板块创建成功')
    }
    boardDialogVisible.value = false
    fetchBoards()
  } catch (error: any) {
    ElMessage.error(error?.message || '保存板块失败')
  }
}

const handleDeleteBoard = async (boardId: number) => {
  try {
    await adminApi.deleteBoard(boardId)
    ElMessage.success('板块删除成功')
    fetchBoards()
  } catch (error: any) {
    ElMessage.error(error?.message || '删除板块失败')
  }
}

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

const handleAlertAction = async (alert: Alert, status: 'RESOLVED' | 'IGNORED') => {
  try {
    await adminApi.handleAlert(alert.id, {
      status,
      handleResult: status === 'RESOLVED' ? '已确认并完成处理' : '已忽略本次告警'
    })
    alerts.value = alerts.value.filter(a => a.id !== alert.id)
    ElMessage.success('告警状态已更新')
  } catch (error) {
    ElMessage.error('更新告警状态失败')
  }
}

const selectReviewTag = (tag: string) => {
  rejectForm.value.tag = tag
}

const applyReasonTemplate = (tpl: string) => {
  rejectForm.value.reason = tpl
}

const openModerationAction = (user: ModeratedUser, action: 'MUTE' | 'BAN' | 'UNMUTE' | 'UNBAN') => {
  moderationTargetUser.value = user
  moderationAction.value = action
  moderationReason.value = ''
  moderationDialogVisible.value = true
}

const confirmModeration = async () => {
  if (!moderationTargetUser.value || !moderationAction.value) {
    moderationDialogVisible.value = false
    return
  }

  const userId = moderationTargetUser.value.id
  const reason = moderationReason.value

  try {
    if (moderationAction.value === 'MUTE') {
      await adminApi.muteUser(userId, { days: 7, reason })
      ElMessage.success('已禁言用户 7 天')
    } else if (moderationAction.value === 'BAN') {
      await adminApi.banUser(userId, { reason })
      ElMessage.success('已封禁用户')
    } else if (moderationAction.value === 'UNMUTE') {
      await adminApi.unmuteUser(userId, { reason })
      ElMessage.success('已解除禁言')
    } else if (moderationAction.value === 'UNBAN') {
      await adminApi.unbanUser(userId, { reason })
      ElMessage.success('已解除封禁')
    }

    moderationDialogVisible.value = false
    await fetchModeratedUsers()
  } catch (error) {
    ElMessage.error('用户治理操作失败')
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

.moderation-section {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin: 2rem 0;
}

.moderation-container {
  margin-top: 1rem;
}

.moderation-last {
  font-size: 0.75rem;
  color: #4b5563;

  .moderation-reason {
    margin-top: 2px;
    color: #6b7280;
  }
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

.review-tags,
.reason-templates {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-item.clickable {
  cursor: pointer;
}

.moderation-dialog-text {
  font-size: 0.875rem;
  color: #4b5563;
  margin-bottom: 0.75rem;
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

