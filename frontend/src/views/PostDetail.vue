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
              class="author-clickable"
              @click.stop="$router.push({ name: 'UserProfile', params: { userId: postsStore.currentPost.authorId } })"
            >
              {{ postsStore.currentPost.authorName[0] }}
            </el-avatar>
            <div
              class="author-details author-clickable"
              @click.stop="$router.push({ name: 'UserProfile', params: { userId: postsStore.currentPost.authorId } })"
            >
              <h3 class="author-name">{{ postsStore.currentPost.authorName }}</h3>
              <p class="post-meta">{{ formatDate(postsStore.currentPost.createdAt) }}</p>
            </div>
          </div>
          
          <el-tag 
            :type="getStatusType(postsStore.currentPost.status)" 
            size="small"
            class="status-tag"
          >
            {{ getStatusText(postsStore.currentPost.status) }}
          </el-tag>
        </header>

        <h1 class="post-title">{{ postsStore.currentPost.title }}</h1>
        
        <div class="post-content">
          {{ postsStore.currentPost.content }}
        </div>

        <div v-if="postsStore.currentPost.poll" class="post-tags" style="flex-direction: column; align-items: stretch;">
          <div style="font-weight:600;">投票：{{ postsStore.currentPost.poll.question }}</div>
          <div style="display:flex; gap:8px; flex-wrap: wrap;">
            <el-button
              v-for="opt in postsStore.currentPost.poll.options"
              :key="opt.id"
              size="small"
              @click="handleVote(opt.id)"
            >
              {{ opt.text }} ({{ opt.vote_count }})
            </el-button>
          </div>
        </div>

        <div v-if="postsStore.currentPost.attachments?.length" class="post-tags">
          <el-tag
            v-for="att in postsStore.currentPost.attachments"
            :key="att.id"
            :type="att.status === 'APPROVED' ? 'success' : att.status === 'REJECTED' ? 'danger' : 'warning'"
            class="tag-item"
            @click="handleDownloadAttachment(att.id)"
          >
            附件: {{ att.original_name || `#${att.id}` }}（{{ att.status }}）
          </el-tag>
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
            @mouseenter="preloadAssetDetailCharts"
            @mousedown="preloadAssetDetailCharts"
          >
            <el-tag
              size="default"
              :type="getAssetMarketType(asset.market)"
              class="asset-chip-tag"
            >
              {{ asset.code }} · {{ asset.name }}
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
          <el-button
            type="text"
            @click="handleRepost"
            class="action-btn"
          >
            <span>转发 {{ postsStore.currentPost.reposts || 0 }}</span>
          </el-button>
        </div>
      </article>

      <!-- 评论区域 -->
      <section class="comments-section">
        <h3 class="comments-title">评论 ({{ commentCount }})</h3>
        
        <!-- 发表评论（顶级评论） -->
        <div class="comment-form" v-if="authStore.isLoggedIn">
          <el-input
            v-model="newComment"
            type="textarea"
            :rows="3"
            placeholder="写下你的看法…"
            class="comment-input"
          />
          <div class="comment-attachment-upload">
            <el-upload
              :show-file-list="false"
              :auto-upload="false"
              :disabled="commenting || commentUploading"
              :on-change="handleCommentAttachmentSelect"
            >
              <el-button size="small" :loading="commentUploading">上传附件</el-button>
            </el-upload>
            <div v-if="selectedCommentAttachments.length" class="comment-attachment-list">
              <el-tag
                v-for="att in selectedCommentAttachments"
                :key="att.id"
                closable
                class="comment-attachment-tag"
                @close="removeSelectedCommentAttachment(att.id)"
              >
                {{ att.original_name || `附件#${att.id}` }}
              </el-tag>
            </div>
          </div>
          <div class="comment-actions">
            <el-button
              plain
              class="comment-submit-primary"
              @click="handleAddComment"
              :loading="commenting"
              :disabled="!newComment.trim() && !selectedCommentAttachments.length"
            >
              发表评论
            </el-button>
          </div>
        </div>

        <div class="comments-list">
          <el-skeleton v-if="loadingComments" :rows="3" animated />
          <el-empty v-else-if="!comments.length" description="暂无评论" />
          <div v-else class="comment-items">
            <div
              v-for="comment in comments"
              :key="comment.id"
              class="comment-item"
            >
              <div class="comment-main">
                <div class="comment-header">
                  <div class="comment-user">
                    <span
                      class="comment-author author-clickable"
                      @click="$router.push({ name: 'UserProfile', params: { userId: comment.authorId } })"
                    >
                      {{ comment.authorName }}
                    </span>
                    <div class="comment-meta-line">
                      <span class="comment-time">{{ formatDate(comment.createdAt) }}</span>
                    </div>
                  </div>
                  <div class="comment-actions-inline">
                    <el-button
                      v-if="authStore.isLoggedIn"
                      link
                      size="small"
                      @click="startReply(comment)"
                    >
                      回复
                    </el-button>
                    <el-button
                      v-if="canEditOrDelete(comment)"
                      link
                      size="small"
                      @click="startEdit(comment)"
                    >
                      编辑
                    </el-button>
                    <el-button
                      v-if="canEditOrDelete(comment)"
                      link
                      size="small"
                      @click="handleDeleteComment(comment)"
                    >
                      删除
                    </el-button>
                    <el-button
                      v-if="authStore.isLoggedIn"
                      link
                      size="small"
                      @click="openReportDialog('COMMENT', comment.id, comment.body)"
                    >
                      举报
                    </el-button>
                  </div>
                </div>

                <div class="comment-body">
                  <template v-if="editingCommentId === comment.id">
                    <el-input
                      v-model="editText"
                      type="textarea"
                      :rows="2"
                      class="comment-edit-input"
                    />
                    <div class="comment-edit-actions">
                      <el-button
                        size="small"
                        @click="cancelEdit"
                      >
                        取消
                      </el-button>
                      <el-button
                        size="small"
                        type="primary"
                        :loading="editing"
                        @click="confirmEdit(comment)"
                      >
                        保存
                      </el-button>
                    </div>
                  </template>
                  <template v-else>
                    {{ comment.body }}
                  </template>
                </div>
                <div v-if="comment.attachments?.length" class="comment-attachments-view">
                  <a
                    v-for="att in comment.attachments"
                    :key="att.id"
                    :href="att.fileUrl"
                    class="comment-attachment-link"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {{ att.original_name || `附件#${att.id}` }}
                  </a>
                </div>

                <div class="comment-footer">
                  <el-button
                    class="comment-like-btn"
                    :class="{ 'is-liked': comment.isLiked }"
                    link
                    size="small"
                    @click="toggleCommentLike(comment)"
                  >
                    赞 {{ comment.likeCount }}
                  </el-button>
                </div>
              </div>

              <!-- 子回复列表 -->
              <div class="comment-replies" v-if="comment.replies && comment.replies.length">
                <div
                  v-for="reply in visibleReplies(comment)"
                  :key="reply.id"
                  class="comment-reply-item"
                >
                  <div class="comment-header">
                    <div class="comment-user">
                      <span
                        class="comment-author author-clickable"
                        @click="$router.push({ name: 'UserProfile', params: { userId: reply.authorId } })"
                      >
                        {{ reply.authorName }}
                      </span>
                      <div class="comment-meta-line">
                        <span v-if="reply.replyToUsername" class="reply-to">
                          回复 @{{ reply.replyToUsername }}
                        </span>
                        <span class="comment-time">{{ formatDate(reply.createdAt) }}</span>
                      </div>
                    </div>
                    <div class="comment-actions-inline">
                      <el-button
                        v-if="authStore.isLoggedIn"
                        link
                        size="small"
                        @click="startReply(reply, comment)"
                      >
                        回复
                      </el-button>
                      <el-button
                        v-if="canEditOrDelete(reply)"
                        link
                        size="small"
                        @click="startEdit(reply)"
                      >
                        编辑
                      </el-button>
                      <el-button
                        v-if="canEditOrDelete(reply)"
                        link
                        size="small"
                        @click="handleDeleteComment(reply)"
                      >
                        删除
                      </el-button>
                      <el-button
                        v-if="authStore.isLoggedIn"
                        link
                        size="small"
                        @click="openReportDialog('COMMENT', reply.id, reply.body)"
                      >
                        举报
                      </el-button>
                    </div>
                  </div>
                  <div class="comment-body">
                    <template v-if="editingCommentId === reply.id">
                      <el-input
                        v-model="editText"
                        type="textarea"
                        :rows="2"
                        class="comment-edit-input"
                      />
                      <div class="comment-edit-actions">
                        <el-button
                          size="small"
                          @click="cancelEdit"
                        >
                          取消
                        </el-button>
                        <el-button
                          size="small"
                          type="primary"
                          :loading="editing"
                          @click="confirmEdit(reply)"
                        >
                          保存
                        </el-button>
                      </div>
                    </template>
                    <template v-else>
                      {{ reply.body }}
                    </template>
                  </div>
                  <div v-if="reply.attachments?.length" class="comment-attachments-view">
                    <a
                      v-for="att in reply.attachments"
                      :key="att.id"
                      :href="att.fileUrl"
                      class="comment-attachment-link"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {{ att.original_name || `附件#${att.id}` }}
                    </a>
                  </div>
                  <div class="comment-footer">
                    <el-button
                      class="comment-like-btn"
                      :class="{ 'is-liked': reply.isLiked }"
                      link
                      size="small"
                      @click="toggleCommentLike(reply)"
                    >
                      赞 {{ reply.likeCount }}
                    </el-button>
                  </div>
                </div>

                <!-- 展开更多回复 -->
                <div class="comment-more-replies">
                  <el-button
                    v-if="(comment.replies && comment.replies.length > 1) || (hasMoreReplies(comment) && !isRepliesExpanded(comment.id))"
                    link
                    size="small"
                    :loading="loadingRepliesId === comment.id"
                    @click="toggleReplies(comment)"
                  >
                    {{ isRepliesExpanded(comment.id)
                      ? '收起回复'
                      : `展开${hiddenReplyCount(comment)}条回复` }}
                  </el-button>
                </div>
              </div>

              <!-- 回复输入框（针对某条评论） -->
              <div
                v-if="replyingTo && replyingTo.id === comment.id"
                class="comment-reply-form"
              >
                <el-input
                  v-model="replyText"
                  type="textarea"
                  :rows="2"
                  placeholder="分享你的补充判断…"
                />
                <div v-if="selectedReplyAttachments.length" class="comment-attachment-list reply-attachment-list">
                  <el-tag
                    v-for="att in selectedReplyAttachments"
                    :key="att.id"
                    closable
                    class="comment-attachment-tag"
                    @close="removeSelectedReplyAttachment(att.id)"
                  >
                    {{ att.original_name || `附件#${att.id}` }}
                  </el-tag>
                </div>
                <div class="comment-edit-actions">
                  <el-upload
                    :show-file-list="false"
                    :auto-upload="false"
                    :disabled="replying || replyUploading"
                    :on-change="handleReplyAttachmentSelect"
                  >
                    <el-button
                      size="small"
                      class="reply-action-btn"
                      :loading="replyUploading"
                    >
                      上传附件
                    </el-button>
                  </el-upload>
                  <el-button
                    size="small"
                    class="reply-action-btn"
                    @click="cancelReply"
                  >
                    取消
                  </el-button>
                  <el-button
                    size="small"
                    class="reply-action-btn"
                    :loading="replying"
                    :disabled="!replyText.trim() && !selectedReplyAttachments.length"
                    @click="confirmReply(comment)"
                  >
                    发送回复
                  </el-button>
                </div>
              </div>
            </div>
          </div>
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

    <!-- 举报对话框 -->
    <el-dialog
      v-model="showReportDialog"
      title="举报内容"
      width="480px"
    >
      <el-form :model="reportForm" label-width="90px">
        <el-form-item label="举报类型">
          <el-select v-model="reportForm.reportType" placeholder="选择举报类型">
            <el-option label="广告/垃圾信息" value="AD" />
            <el-option label="辱骂/人身攻击" value="ABUSE" />
            <el-option label="虚假收益/诱导荐股" value="FAKE_RETURN" />
            <el-option label="违法违规内容" value="ILLEGAL" />
            <el-option label="其他" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item label="详细说明">
          <el-input
            v-model="reportForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请补充举报原因，便于管理员处理"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showReportDialog = false">取消</el-button>
          <el-button
            type="danger"
            :loading="reporting"
            @click="submitReport"
          >
            提交举报
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePostsStore } from '../stores/posts'
import { useAuthStore } from '../stores/auth'
import type { Comment, CommentAttachment } from '../types'
import { PostStatus } from '../types'
import * as postsApi from '../api/posts'
import * as reportsApi from '../api/reports'
import { ElMessage } from 'element-plus'
import {
  Star,
  Share
} from '@element-plus/icons-vue'
import { dayjs } from '../utils/date'
import { preloadAssetDetailCharts } from '../utils/preload'
import { getAvatarPlaceholderDataUrl } from '@/utils/avatarPlaceholder'

const route = useRoute()
const postsStore = usePostsStore()
const authStore = useAuthStore()

const newComment = ref('')
const commenting = ref(false)
const comments = ref<Comment[]>([])
const commentCount = ref(0)
const loadingComments = ref(false)
const showShareDialog = ref(false)

// 楼中楼 & 交互状态
const replyingTo = ref<Comment | null>(null)
const replyText = ref('')
const replying = ref(false)
const commentUploading = ref(false)
const replyUploading = ref(false)
const selectedCommentAttachments = ref<CommentAttachment[]>([])
const selectedReplyAttachments = ref<CommentAttachment[]>([])
const editingCommentId = ref<number | null>(null)
const editText = ref('')
const editing = ref(false)
const loadingRepliesId = ref<number | null>(null)
const expandedReplies = ref<Record<number, boolean>>({})

// 举报
const showReportDialog = ref(false)
const reporting = ref(false)
const reportTargetType = ref<'POST' | 'COMMENT' | null>(null)
const reportTargetId = ref<number | null>(null)
const reportForm = ref({
  reportType: '',
  reason: ''
})

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

const handleRepost = async () => {
  if (!authStore.isLoggedIn || !postsStore.currentPost) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    await postsApi.repostPost(postsStore.currentPost.id)
    postsStore.currentPost.reposts = (postsStore.currentPost.reposts || 0) + 1
    ElMessage.success('转发成功')
  } catch (error) {
    ElMessage.error('转发失败')
  }
}

const handleVote = async (optionId: number) => {
  if (!authStore.isLoggedIn || !postsStore.currentPost) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    await postsApi.votePoll(postsStore.currentPost.id, [optionId])
    const poll = await postsApi.getPollResult(postsStore.currentPost.id)
    postsStore.currentPost.poll = poll as any
    ElMessage.success('投票成功')
  } catch (error: any) {
    ElMessage.error(error?.message || '投票失败')
  }
}

const handleDownloadAttachment = async (attachmentId: number) => {
  try {
    const data: any = await postsApi.downloadContentAttachment(attachmentId)
    if (data?.url) {
      window.open(data.url, '_blank')
    }
  } catch {
    ElMessage.error('附件暂不可下载（可能仍在审核）')
  }
}

const handleAddComment = async () => {
  if (!newComment.value.trim() && !selectedCommentAttachments.value.length) return

  if (!postsStore.currentPost) return

  commenting.value = true
  try {
    const comment = await postsApi.createComment(postsStore.currentPost.id, {
      text: newComment.value.trim(),
      attachmentIds: selectedCommentAttachments.value.map(item => item.id)
    })
    comments.value.push(comment)
    commentCount.value += 1
    ElMessage.success('评论发表成功')
    newComment.value = ''
    selectedCommentAttachments.value = []
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

const getAvatarUrl = (id: number) => getAvatarPlaceholderDataUrl(id, 48)

const getAssetMarketType = (market?: string) => {
  const m = market?.toUpperCase()
  if (m === 'SH' || m === 'SZ') return 'danger'
  if (m === 'HK') return 'warning'
  if (m === 'US') return 'primary'
  return 'info'
}

const syncCommentCountFromPost = () => {
  const post = postsStore.currentPost
  if (!post) return
  const serverComments: any = post.comments
  commentCount.value =
    typeof serverComments === 'number' ? serverComments : comments.value.length
}

const loadComments = async (postId: number) => {
  loadingComments.value = true
  try {
    const data = await postsApi.getPostComments(postId)
    comments.value = data
    if (postsStore.currentPost) {
      syncCommentCountFromPost()
    } else {
      commentCount.value = data.length
    }
  } finally {
    loadingComments.value = false
  }
}

const canEditOrDelete = (comment: Comment) => {
  if (!authStore.isLoggedIn || !authStore.user) return false
  // 前端仅开放“本人评论”的编辑/删除入口，管理员治理动作走后台页面
  return authStore.user.id === comment.authorId
}

const startReply = (comment: Comment, topLevelParent?: Comment) => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  replyingTo.value = topLevelParent || comment
  replyText.value = ''
  selectedReplyAttachments.value = []
}

const cancelReply = () => {
  replyingTo.value = null
  replyText.value = ''
  selectedReplyAttachments.value = []
}

const confirmReply = async (parentComment: Comment) => {
  if ((!replyText.value.trim() && !selectedReplyAttachments.value.length) || !postsStore.currentPost) return
  replying.value = true
  try {
    const payload: postsApi.CreateCommentParams = {
      text: replyText.value.trim(),
      parentId: parentComment.id,
      replyToUserId: parentComment.authorId,
      attachmentIds: selectedReplyAttachments.value.map(item => item.id)
    }
    const reply = await postsApi.createComment(postsStore.currentPost.id, payload) as Comment
    // 将新回复追加到对应父评论的 replies 列表
    const target = comments.value.find(c => c.id === parentComment.id)
    if (target) {
      if (!target.replies) target.replies = []
      target.replies.push(reply)
    }
    commentCount.value += 1
    ElMessage.success('回复已发送')
    cancelReply()
  } catch (error) {
    ElMessage.error('发送回复失败')
  } finally {
    replying.value = false
  }
}

const handleCommentAttachmentSelect = async (uploadFile: any) => {
  if (!uploadFile?.raw) return
  commentUploading.value = true
  try {
    const attachment = await postsApi.uploadCommentAttachment(uploadFile.raw as File)
    selectedCommentAttachments.value.push(attachment)
    ElMessage.success('评论附件上传成功')
  } catch {
    ElMessage.error('评论附件上传失败')
  } finally {
    commentUploading.value = false
  }
}

const handleReplyAttachmentSelect = async (uploadFile: any) => {
  if (!uploadFile?.raw) return
  replyUploading.value = true
  try {
    const attachment = await postsApi.uploadCommentAttachment(uploadFile.raw as File)
    selectedReplyAttachments.value.push(attachment)
    ElMessage.success('回复附件上传成功')
  } catch {
    ElMessage.error('回复附件上传失败')
  } finally {
    replyUploading.value = false
  }
}

const removeSelectedCommentAttachment = (attachmentId: number) => {
  selectedCommentAttachments.value = selectedCommentAttachments.value.filter(item => item.id !== attachmentId)
}

const removeSelectedReplyAttachment = (attachmentId: number) => {
  selectedReplyAttachments.value = selectedReplyAttachments.value.filter(item => item.id !== attachmentId)
}

const hasMoreReplies = (comment: Comment) => {
  // 底层实现始终只返回前 5 条预览，认为 >=5 就可能还有更多
  return comment.replies && comment.replies.length >= 5
}

const isRepliesExpanded = (commentId: number) => {
  return !!expandedReplies.value[commentId]
}

const visibleReplies = (comment: Comment) => {
  const replies = comment.replies || []
  if (isRepliesExpanded(comment.id)) {
    return replies
  }
  return replies.slice(0, 1)
}

const hiddenReplyCount = (comment: Comment) => {
  const replies = comment.replies || []
  if (isRepliesExpanded(comment.id)) return 0
  return Math.max(0, replies.length - 1)
}

const toggleReplies = async (comment: Comment) => {
  if (isRepliesExpanded(comment.id)) {
    expandedReplies.value[comment.id] = false
    return
  }
  if (hasMoreReplies(comment)) {
    await loadAllReplies(comment)
  }
  expandedReplies.value[comment.id] = true
}

const loadAllReplies = async (comment: Comment) => {
  loadingRepliesId.value = comment.id
  try {
    const data = await postsApi.getCommentReplies(comment.id, { page: 1, pageSize: 50 })
    comment.replies = data.items
  } catch (error) {
    ElMessage.error('加载更多回复失败')
  } finally {
    loadingRepliesId.value = null
  }
}

const startEdit = (comment: Comment) => {
  if (!canEditOrDelete(comment)) return
  editingCommentId.value = comment.id
  editText.value = comment.body
}

const cancelEdit = () => {
  editingCommentId.value = null
  editText.value = ''
}

const confirmEdit = async (comment: Comment) => {
  if (!editText.value.trim()) {
    ElMessage.warning('评论内容不能为空')
    return
  }
  editing.value = true
  try {
    const updated = await postsApi.updateComment(comment.id, { text: editText.value.trim() }) as Comment
    comment.body = updated.body
    comment.createdAt = updated.createdAt
    ElMessage.success('评论已更新')
    cancelEdit()
  } catch (error) {
    ElMessage.error('更新评论失败')
  } finally {
    editing.value = false
  }
}

const handleDeleteComment = async (comment: Comment) => {
  try {
    await postsApi.deleteComment(comment.id)
    // 从顶级或子回复列表中移除
    comments.value = comments.value
      .map(c => {
        if (c.id === comment.id) {
          return null
        }
        if (c.replies && c.replies.length) {
          c.replies = c.replies.filter(r => r.id !== comment.id)
        }
        return c
      })
      .filter((c): c is Comment => c !== null)

    commentCount.value = Math.max(0, commentCount.value - 1)
    ElMessage.success('评论已删除')
  } catch (error) {
    ElMessage.error('删除评论失败')
  }
}

const toggleCommentLike = async (comment: Comment) => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    if (comment.isLiked) {
      await postsApi.unlikeComment(comment.id)
      comment.isLiked = false
      comment.likeCount = Math.max(0, comment.likeCount - 1)
    } else {
      await postsApi.likeComment(comment.id)
      comment.isLiked = true
      comment.likeCount += 1
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const openReportDialog = (targetType: 'POST' | 'COMMENT', targetId: number, summary: string) => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  reportTargetType.value = targetType
  reportTargetId.value = targetId
  reportForm.value = {
    reportType: '',
    reason: ''
  }
  showReportDialog.value = true
}

const submitReport = async () => {
  if (!reportTargetType.value || !reportTargetId.value) return
  if (!reportForm.value.reportType || !reportForm.value.reason.trim()) {
    ElMessage.warning('请完整填写举报类型和原因')
    return
  }
  reporting.value = true
  try {
    await reportsApi.createReport({
      targetType: reportTargetType.value,
      targetId: reportTargetId.value,
      reason: reportForm.value.reason.trim(),
      reportTypeDetail: reportForm.value.reportType
    })
    ElMessage.success('举报已提交，感谢你的反馈')
    showReportDialog.value = false
  } catch (error) {
    ElMessage.error('举报提交失败')
  } finally {
    reporting.value = false
  }
}

onMounted(async () => {
  const postId = Number(route.params.id)
  if (!postId) return

  const [postResult, commentResult] = await Promise.allSettled([
    postsStore.fetchPost(postId),
    loadComments(postId)
  ])

  if (postResult.status === 'rejected') {
    ElMessage.error('获取帖子详情失败')
    return
  }
  syncCommentCountFromPost()
  if (commentResult.status === 'rejected') {
    ElMessage.error('加载评论失败')
  }
})
</script>

<style lang="scss" scoped>
.post-detail {
  max-width: 880px;
  margin: 0 auto;
  animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.loading-container {
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 20px;
  padding: 2rem;
}

.not-found {
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 20px;
  padding: 2rem;
}

.post-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.post-article {
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 20px;
  padding: 2.5rem 3rem;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);

  @media (max-width: 768px) {
    padding: 1.75rem 1.5rem;
  }
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
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
  font-size: 0.875rem;
  font-weight: 600;
  color: $apple-text-primary;
  margin: 0;
  line-height: 1.4;
}

.post-meta {
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
  font-size: 1.875rem;
  font-weight: 700;
  color: $apple-text-primary;
  line-height: 1.35;
  margin: 0 0 1.5rem 0;
  letter-spacing: -0.02em;
}

.post-content {
  font-size: 1rem;
  color: $apple-text-secondary;
  line-height: 1.85;
  margin-bottom: 2rem;
  white-space: pre-wrap;
  font-weight: 400;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 2rem;
}

.tag-item {
  background: rgba(100, 116, 139, 0.1) !important;
  border: 1px solid rgba(100, 116, 139, 0.15) !important;
  color: rgba(100, 116, 139, 0.9) !important;
  border-radius: 10px !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  padding: 0.25rem 0.625rem !important;
  font-family: $apple-font-family !important;
}

.asset-chip-link {
  text-decoration: none;

  .asset-chip-tag {
    cursor: pointer;
    font-weight: 500;
    font-size: 0.75rem;
    border-radius: 10px !important;
    padding: 0.25rem 0.625rem !important;
    border: none !important;
    font-family: $apple-font-family !important;

    .market-suffix {
      font-size: 0.6875rem;
      opacity: 0.75;
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

.post-actions {
  display: flex;
  gap: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  align-items: center;
}

.action-btn {
  display: flex !important;
  align-items: center !important;
  gap: 0.5rem !important;
  color: $apple-text-tertiary !important;
  font-size: 0.875rem !important;
  border-radius: 10px !important;
  padding: 0.5rem 0.75rem !important;
  transition: all 0.2s ease !important;
  cursor: pointer;
  background: transparent !important;
  border: none !important;
  font-weight: 500 !important;

  :deep(.el-icon) {
    font-size: 1.125rem;
  }

  span {
    font-size: 0.875rem;
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
}

.comments-section {
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 20px;
  padding: 2rem;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);

  @media (max-width: 768px) {
    padding: 1.5rem;
  }
}

.comments-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: $apple-text-primary;
  margin: 0 0 1.75rem 0;
  letter-spacing: -0.01em;
}

.comment-form {
  margin-bottom: 2.5rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.comment-input {
  margin-bottom: 1rem;

  :deep(.el-textarea__inner) {
    background: rgba(245, 245, 247, 0.9) !important;
    border: 1px solid rgba(0, 0, 0, 0.06) !important;
    border-radius: 14px !important;
    color: $apple-text-primary !important;
    font-size: 0.9375rem !important;
    line-height: 1.6 !important;
    padding: 1rem 1.25rem !important;
    font-family: $apple-font-family !important;
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

.comment-attachment-upload {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.comment-attachment-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.reply-attachment-list {
  margin-top: 0.5rem;
}

.comment-attachment-tag {
  cursor: default;
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
}

.comment-submit-primary {
  background: #ffffff !important;
  color: $apple-text-primary !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: $apple-shadow-sm !important;
  font-weight: 500;

  &:hover:not(:disabled),
  &:focus:not(:disabled) {
    background: #ffffff !important;
    border-color: rgba(37, 99, 235, 0.22) !important;
    color: $apple-text-primary !important;
    box-shadow: $apple-shadow-md !important;
  }
}

.comment-reply-form {
  margin-top: 0.625rem;
}

.comment-reply-form .comment-edit-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 0.625rem;
  margin-top: 0.625rem;
  flex-wrap: nowrap;
  width: 100%;
}

.comment-reply-form :deep(.el-upload) {
  display: inline-flex !important;
  flex: 0 0 auto !important;
  width: auto !important;
}

.comment-reply-form :deep(.reply-action-btn) {
  background: #fff !important;
  color: $apple-text-secondary !important;
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
  border-radius: 8px !important;
  padding: 0.375rem 0.875rem !important;
  font-weight: 500 !important;
  min-width: 92px !important;
  height: 32px !important;
  line-height: 1 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  white-space: nowrap !important;
  box-sizing: border-box !important;
}

.comment-reply-form :deep(.reply-action-btn:hover) {
  background: rgba(245, 245, 247, 0.9) !important;
}

.comments-list {
  margin-top: 0;
}

.comment-items {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.comment-item {
  padding: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  padding-bottom: 1.5rem;

  &:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  font-size: 0.8125rem;
  color: $apple-text-tertiary;
  margin-bottom: 0.625rem;
}

.comment-author {
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: 0.01em;
  line-height: 1.35;
  color: $apple-text-primary;
  cursor: pointer;
  transition: color 0.2s ease;

  &:hover {
    color: $apple-accent;
  }
}

.comment-user {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.2rem;
}

.comment-meta-line {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.comment-time {
  font-size: 0.8125rem;
  color: $apple-text-tertiary;
  letter-spacing: 0.01em;
  line-height: 1.3;
}

.reply-to {
  font-size: 0.8125rem;
  color: $apple-text-tertiary;
  letter-spacing: 0.01em;
}

.comment-body {
  font-size: 1rem;
  font-weight: 600;
  color: $apple-text-primary;
  line-height: 1.35;
  letter-spacing: 0.01em;
  margin-bottom: 0.875rem;
}

.comment-footer {
  margin-top: 0.375rem;
}

/* 已赞：白底（与评论区卡片一致）+ 红字，避免 danger 类型的红底白字 */
.comment-like-btn.is-liked {
  color: rgba(232, 93, 93, 0.95) !important;
  --el-button-text-color: rgba(232, 93, 93, 0.95);
  --el-button-hover-text-color: rgba(232, 93, 93, 1);
  --el-button-hover-bg-color: rgba(232, 93, 93, 0.08);
  --el-button-bg-color: transparent;
  background: transparent !important;
  border-color: transparent !important;

  &:hover {
    color: rgba(232, 93, 93, 1) !important;
  }
}

.comment-attachments-view {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: -0.25rem;
  margin-bottom: 0.625rem;
}

.comment-attachment-link {
  font-size: 0.8125rem;
  color: $apple-accent;
  text-decoration: none;
  border: 1px solid rgba(0, 113, 227, 0.2);
  border-radius: 8px;
  padding: 0.2rem 0.5rem;
}

.comment-attachment-link:hover {
  background: rgba(0, 113, 227, 0.06);
}

/* 楼中楼：二级评论与一级评论形成清晰层级 */
.comment-replies {
  margin-top: 0.5rem;
  margin-left: 1.75rem;
  padding-left: 1rem;
  border-left: 2px solid rgba(0, 0, 0, 0.08);
}

.comment-reply-item {
  padding: 0.5rem 0;
}

.comment-reply-item .comment-author {
  font-size: 0.9375rem;
}

.comment-reply-item .comment-time,
.comment-reply-item .reply-to {
  font-size: 0.78125rem;
}

.comment-reply-item .comment-body {
  font-size: 0.9375rem;
  font-weight: 600;
  color: $apple-text-primary;
  line-height: 1.35;
  letter-spacing: 0.01em;
}

.comment-more-replies {
  margin-top: 0.25rem;
  margin-left: 0.125rem;
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



