<template>
  <div class="group-detail" v-loading="loading">
    <el-card v-if="group">
      <div class="header">
        <div>
          <h2>{{ group.name }}</h2>
          <p>{{ group.description || '暂无简介' }}</p>
        </div>
        <div class="actions">
          <el-button
            v-if="group?.visibility === 'APPROVAL' && isMember"
            @click="goRequests"
          >
            审核列表
          </el-button>
          <el-button
            v-if="group?.visibility === 'APPROVAL' && isOwner"
            @click="openReviewerDialog"
          >
            审核人管理
          </el-button>
          <el-button
            v-if="group?.visibility === 'PRIVATE' && isOwner"
            @click="openInviteDialog"
          >
            邀请成员
          </el-button>
          <el-button v-if="showJoinButton" :disabled="joinDisabled" type="primary" @click="handleJoin">
            {{ joinButtonText }}
          </el-button>
          <el-button v-else @click="handleLeave">退出群组</el-button>
        </div>
      </div>
      <div class="meta">
        <span>{{ group.memberCount }} 成员</span>
        <span>{{ group.postCount }} 讨论</span>
        <span>{{ group.fileCount }} 资料</span>
      </div>
    </el-card>

    <el-tabs v-if="canShowContent" v-model="activeTab" class="tabs">
      <el-tab-pane label="群讨论" name="posts">
        <el-card>
          <el-form inline>
            <el-form-item>
              <el-input v-model="postForm.title" placeholder="讨论标题" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="postForm.body" placeholder="说点什么..." />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitPost">发布</el-button>
            </el-form-item>
          </el-form>
          <el-divider />
          <div v-for="p in groupsStore.posts" :key="p.id" class="post-item">
            <h4>{{ p.title }}</h4>
            <p>{{ p.body }}</p>
            <span class="sub">{{ p.authorName }} · {{ formatDate(p.createdAt) }}</span>
          </div>
          <el-empty v-if="groupsStore.posts.length === 0" description="暂无讨论" />
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="群资料" name="files">
        <el-card>
          <el-upload :auto-upload="false" :show-file-list="false" :on-change="onChooseFile">
            <el-button type="primary">上传资料</el-button>
          </el-upload>
          <el-divider />
          <div v-for="f in groupsStore.files" :key="f.id" class="file-item">
            <a :href="f.fileUrl" target="_blank">{{ f.original_name }}</a>
            <span>{{ bytes(f.file_size) }}</span>
            <el-button size="small" text type="danger" @click="removeFile(f.id)">删除</el-button>
          </div>
          <el-empty v-if="groupsStore.files.length === 0" description="暂无资料" />
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="成员" name="members">
        <el-card>
          <div v-for="m in groupsStore.members" :key="m.id" class="member-item">
            <span>{{ m.displayName }} (@{{ m.username }})</span>
            <el-tag size="small">{{ m.role }}</el-tag>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
    <el-empty v-else-if="group" description="暂无权限查看群聊内容" />

    <el-dialog v-model="reviewerDialogVisible" title="审核人管理" width="560px">
      <div class="reviewer-panel">
        <div class="reviewer-section-title">当前审核人</div>
        <div v-if="groupsStore.reviewers.length" class="reviewer-list">
          <div v-for="item in groupsStore.reviewers" :key="item.id" class="reviewer-item">
            <span>{{ item.userName }} (@{{ item.username }})</span>
            <el-button
              size="small"
              text
              type="danger"
              :disabled="item.userId === group?.ownerId"
              @click="removeReviewerAction(item.userId)"
            >
              移除
            </el-button>
          </div>
        </div>
        <el-empty v-else description="暂无审核人" :image-size="70" />

        <el-divider />
        <div class="reviewer-section-title">添加审核人</div>
        <el-input
          v-model="reviewerSearch"
          placeholder="按昵称或用户名搜索群成员"
          clearable
          style="margin-bottom: 10px"
        />
        <el-select v-model="selectedReviewerUserId" placeholder="请选择群成员" filterable style="width: 100%">
          <el-option
            v-for="m in filteredMemberCandidates"
            :key="m.userId"
            :label="`${m.displayName} (@${m.username})`"
            :value="m.userId"
          />
        </el-select>
      </div>
      <template #footer>
        <el-button @click="reviewerDialogVisible = false">关闭</el-button>
        <el-button type="primary" :disabled="!selectedReviewerUserId" @click="addReviewerAction">添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="inviteDialogVisible" title="邀请成员" width="520px">
      <el-form label-width="90px">
        <el-form-item label="选择用户">
          <el-select
            v-model="inviteForm.inviteeId"
            placeholder="按昵称/用户名搜索可邀请用户"
            filterable
            :loading="inviteCandidatesLoading"
            style="width: 100%"
          >
            <el-option
              v-for="item in inviteCandidates"
              :key="item.id"
              :label="`${item.displayName} (@${item.username})`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="邀请说明">
          <el-input v-model="inviteForm.message" type="textarea" :rows="3" maxlength="300" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inviteDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!inviteForm.inviteeId" @click="submitInvite">发送邀请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { User } from '../types'
import { useGroupsStore } from '../stores/groups'
import {
  addGroupReviewer,
  createGroupInvite,
  createGroupPost,
  deleteGroupFile,
  joinGroup,
  leaveGroup,
  removeGroupReviewer,
  uploadGroupFile
} from '../api/groups'
import { getConversations } from '../api/messages'
import { getUserFollowers, getUserFollowing, type UserFollowItem } from '../api/users'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const groupsStore = useGroupsStore()
const groupId = computed(() => Number(route.params.groupId))
const loading = ref(false)
const activeTab = ref('posts')
const postForm = ref({ title: '', body: '' })
const pendingJoin = ref(false)
const canShowContent = ref(false)
const reviewerDialogVisible = ref(false)
const inviteDialogVisible = ref(false)
const reviewerSearch = ref('')
const selectedReviewerUserId = ref<number | null>(null)
const inviteForm = ref<{ inviteeId: number | null; message: string }>({ inviteeId: null, message: '' })
const inviteCandidates = ref<User[]>([])
const inviteCandidatesLoading = ref(false)

const group = computed(() => groupsStore.currentGroup)
const isMember = computed(() => groupsStore.members.some((m) => m.userId === authStore.user?.id))
const isOwner = computed(() => !!group.value && group.value.ownerId === authStore.user?.id)
const memberCandidates = computed(() => {
  const reviewerIds = new Set(groupsStore.reviewers.map((item) => item.userId))
  return groupsStore.members.filter((m) => !reviewerIds.has(m.userId))
})
const filteredMemberCandidates = computed(() => {
  const keyword = reviewerSearch.value.trim().toLowerCase()
  if (!keyword) return memberCandidates.value
  return memberCandidates.value.filter((m) =>
    `${m.displayName}${m.username}`.toLowerCase().includes(keyword)
  )
})
const joinButtonText = computed(() => {
  if (!group.value) return '加入群组'
  if (group.value.visibility === 'APPROVAL') {
    return pendingJoin.value ? '审核中' : '申请加入'
  }
  if (group.value.visibility === 'PRIVATE') return '需邀请加入'
  return '加入群组'
})
const showJoinButton = computed(() => !isMember.value)
const joinDisabled = computed(() => !group.value || group.value.visibility === 'PRIVATE' || pendingJoin.value)

const getErrorData = (error: any) => error?.response?.data || {}
const showNoAccessAlert = async (message: string) => {
  await ElMessageBox.alert(message, '无权限查看', { type: 'warning' })
}

const loadAll = async () => {
  loading.value = true
  try {
    canShowContent.value = false
    pendingJoin.value = false
    await groupsStore.fetchGroupDetail(groupId.value)
    await groupsStore.fetchGroupMembers(groupId.value)

    if (!group.value) return
    if (group.value.visibility === 'PUBLIC' || isMember.value) {
      await Promise.all([groupsStore.fetchGroupPosts(groupId.value), groupsStore.fetchGroupFiles(groupId.value)])
      canShowContent.value = true
      return
    }

    try {
      await groupsStore.fetchGroupPosts(groupId.value)
      await groupsStore.fetchGroupFiles(groupId.value)
      canShowContent.value = true
    } catch (error: any) {
      const data = getErrorData(error)
      pendingJoin.value = data.reason === 'WAIT_REVIEW'
      await showNoAccessAlert(data.message || '你暂无权限查看该群聊内容')
    }
  } catch (error: any) {
    const data = getErrorData(error)
    if (error?.response?.status === 403) {
      await showNoAccessAlert(data.message || '你暂无权限查看该群聊内容')
    }
  } finally {
    loading.value = false
  }
}

const handleJoin = async () => {
  if (!group.value || group.value.visibility === 'PRIVATE') {
    ElMessage.warning('私密群仅支持群主邀请加入')
    return
  }
  try {
    await joinGroup(groupId.value)
    ElMessage.success(group.value.visibility === 'APPROVAL' ? '申请已提交' : '加入成功')
    await loadAll()
  } catch (error: any) {
    const data = getErrorData(error)
    if (data.reason === 'WAIT_REVIEW') pendingJoin.value = true
  }
}

const handleLeave = async () => {
  await leaveGroup(groupId.value)
  ElMessage.success('已退出')
  await loadAll()
}

const goRequests = () => {
  router.push(`/groups/${groupId.value}/requests`)
}

const openReviewerDialog = async () => {
  await groupsStore.fetchReviewers(groupId.value)
  selectedReviewerUserId.value = null
  reviewerSearch.value = ''
  reviewerDialogVisible.value = true
}

const addReviewerAction = async () => {
  if (!selectedReviewerUserId.value) return
  await addGroupReviewer(groupId.value, selectedReviewerUserId.value)
  await groupsStore.fetchReviewers(groupId.value)
  selectedReviewerUserId.value = null
  ElMessage.success('审核人添加成功')
}

const removeReviewerAction = async (userId: number) => {
  await removeGroupReviewer(groupId.value, userId)
  await groupsStore.fetchReviewers(groupId.value)
  ElMessage.success('审核人移除成功')
}

const openInviteDialog = () => {
  inviteForm.value = { inviteeId: null, message: '' }
  void loadInviteCandidates()
  inviteDialogVisible.value = true
}

const loadInviteCandidates = async () => {
  if (!authStore.user?.id) return
  inviteCandidatesLoading.value = true
  try {
    const inGroupIds = new Set(groupsStore.members.map((m) => m.userId))
    const currentUserId = authStore.user.id
    const ranked = new Map<number, { user: User; rank: number }>()

    const collect = (users: User[], rank: number) => {
      users.forEach((u) => {
        if (!u?.id || u.id === currentUserId || inGroupIds.has(u.id)) return
        const old = ranked.get(u.id)
        if (!old || rank < old.rank) {
          ranked.set(u.id, { user: u, rank })
        }
      })
    }

    const [followersRows, followingRows, conversations] = await Promise.all([
      getUserFollowers(currentUserId).catch(() => [] as UserFollowItem[]),
      getUserFollowing(currentUserId).catch(() => [] as UserFollowItem[]),
      getConversations().catch(() => ({ items: [] as any[] }))
    ])

    if (followersRows.length) {
      collect(followersRows.map((row: UserFollowItem) => row.follower), 1)
    }
    if (followingRows.length) {
      collect(followingRows.map((row: UserFollowItem) => row.followee), 2)
    }
    if (conversations.items.length) {
      const recentUsers: User[] = []
      conversations.items.forEach((conv) => {
        conv.participants.forEach((p) => {
          if (p.userId === currentUserId) return
          recentUsers.push({
            id: p.userId,
            username: p.username,
            displayName: p.displayName,
            avatar: p.avatar || '',
            role: 'USER',
            followers: 0,
            following: 0
          })
        })
      })
      collect(recentUsers, 3)
    }

    inviteCandidates.value = Array.from(ranked.values())
      .sort((a, b) => a.rank - b.rank || a.user.id - b.user.id)
      .map((item) => item.user)
  } finally {
    inviteCandidatesLoading.value = false
  }
}

const submitInvite = async () => {
  if (!inviteForm.value.inviteeId) return
  await createGroupInvite(groupId.value, {
    inviteeId: inviteForm.value.inviteeId,
    message: inviteForm.value.message || undefined
  })
  inviteDialogVisible.value = false
  ElMessage.success('邀请已发送')
}

const submitPost = async () => {
  if (!canShowContent.value) return
  if (!postForm.value.title.trim() || !postForm.value.body.trim()) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  await createGroupPost(groupId.value, { ...postForm.value, content_type: 'NORMAL' })
  postForm.value = { title: '', body: '' }
  await groupsStore.fetchGroupPosts(groupId.value)
}

const onChooseFile = async (uploadFile: any) => {
  if (!canShowContent.value) return
  if (!uploadFile?.raw) return
  await uploadGroupFile(groupId.value, uploadFile.raw as File)
  await groupsStore.fetchGroupFiles(groupId.value)
  ElMessage.success('上传成功')
}

const removeFile = async (fileId: number) => {
  await deleteGroupFile(groupId.value, fileId)
  await groupsStore.fetchGroupFiles(groupId.value)
}

const formatDate = (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm')
const bytes = (v: number) => (v > 1024 * 1024 ? `${(v / 1024 / 1024).toFixed(1)} MB` : `${(v / 1024).toFixed(1)} KB`)

onMounted(loadAll)
</script>

<style scoped>
.group-detail { max-width: 1100px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; }
.meta { display: flex; gap: 12px; margin-top: 8px; color: #666; }
.tabs { margin-top: 16px; }
.post-item, .file-item, .member-item { padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.sub { color: #999; font-size: 12px; }
.reviewer-panel { min-height: 220px; }
.reviewer-section-title { font-size: 14px; font-weight: 600; margin-bottom: 10px; }
.reviewer-list { display: flex; flex-direction: column; gap: 8px; }
.reviewer-item { display: flex; align-items: center; justify-content: space-between; }
</style>
