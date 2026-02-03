<template>
  <div class="profile">
    <!-- 用户资料卡片 -->
    <div class="profile-header">
      <div class="profile-card">
        <div class="profile-avatar">
          <el-avatar 
            :src="authStore.user?.avatar" 
            :size="128"
            class="user-avatar"
          >
            {{ authStore.user?.displayName?.[0] }}
          </el-avatar>
        </div>
        
        <div class="profile-info">
          <div class="profile-main">
            <div class="user-identity">
              <h2 class="user-name">{{ authStore.user?.displayName }}</h2>
              <el-tag 
                :type="getRoleType(authStore.user?.role)"
                class="user-role-tag"
              >
                {{ getRoleText(authStore.user?.role) }}
              </el-tag>
            </div>
            <p class="username">@{{ authStore.user?.username }}</p>
            <p class="user-bio">{{ authStore.user?.bio || '这个人很懒，还没有填写个人简介' }}</p>
            
            <div class="user-stats">
              <div class="stat-item">
                <span class="stat-value">{{ authStore.user?.followers || 0 }}</span>
                <span class="stat-label">关注者</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ authStore.user?.following || 0 }}</span>
                <span class="stat-label">关注中</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ userPosts.length }}</span>
                <span class="stat-label">帖子</span>
              </div>
            </div>
          </div>
        </div>

        <div class="profile-actions">
          <el-button 
            type="primary" 
            plain
            @click="showEditProfile = true"
          >
            编辑资料
          </el-button>
        </div>
      </div>
    </div>

    <div class="profile-content">
      <!-- 左侧：账户设置 -->
      <aside class="profile-sidebar">
        <div class="settings-card">
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

      <!-- 右侧：活动记录 -->
      <main class="profile-main-content">
        <h3 class="section-title">最近活动</h3>
        
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
              发表第一篇讨论
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
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { usePostsStore } from '../stores/posts'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { PostStatus } from '../types'
import {
  Star,
  ChatLineRound
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const authStore = useAuthStore()
const postsStore = usePostsStore()

// 状态
const loading = ref(false)
const showEditProfile = ref(false)
const updating = ref(false)

// 编辑表单
const editFormRef = ref<FormInstance>()
const editForm = ref({
  displayName: '',
  bio: '',
  avatar: ''
})

const editRules: FormRules = {
  displayName: [
    { required: true, message: '请输入显示昵称', trigger: 'blur' },
    { min: 2, max: 50, message: '昵称长度应在2-50字符之间', trigger: 'blur' }
  ],
  bio: [
    { max: 200, message: '个人简介不能超过200字符', trigger: 'blur' }
  ]
}

// 计算属性
const userPosts = computed(() => {
  return postsStore.posts.filter(post => post.authorId === authStore.user?.id)
})

// 方法
const fetchUserPosts = async () => {
  if (!authStore.user) return
  
  loading.value = true
  try {
    await postsStore.fetchPosts({
      authorId: authStore.user.id,
      sort: 'new'
    })
  } catch (error) {
    ElMessage.error('获取用户帖子失败')
  } finally {
    loading.value = false
  }
}

const handleUpdateProfile = async () => {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()
    updating.value = true

    // TODO: 调用更新用户资料API
    // await userApi.updateProfile(editForm.value)

    ElMessage.success('资料更新成功')
    showEditProfile.value = false
    
    // 更新本地用户信息
    if (authStore.user) {
      authStore.user.displayName = editForm.value.displayName
      authStore.user.bio = editForm.value.bio
      authStore.user.avatar = editForm.value.avatar
    }
  } catch (error: any) {
    if (error.fields) return // 表单验证错误
    ElMessage.error('更新失败，请稍后重试')
  } finally {
    updating.value = false
  }
}

const copyInviteLink = async () => {
  try {
    const inviteLink = `${window.location.origin}?ref=${authStore.user?.username}`
    await navigator.clipboard.writeText(inviteLink)
    ElMessage.success('邀请链接已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

const getRoleType = (role?: string) => {
  switch (role) {
    case 'ADMIN': return 'danger'
    case 'MODERATOR': return 'warning'
    default: return 'info'
  }
}

const getRoleText = (role?: string) => {
  switch (role) {
    case 'ADMIN': return '管理员'
    case 'MODERATOR': return '版主'
    default: return '用户'
  }
}

const getStatusType = (status: PostStatus) => {
  switch (status) {
    case 'PUBLISHED': return 'success'
    case 'PENDING_REVIEW': return 'warning'
    case 'DRAFT': return 'info'
    default: return 'info'
  }
}

const getStatusText = (status: PostStatus) => {
  switch (status) {
    case 'PUBLISHED': return '已发布'
    case 'PENDING_REVIEW': return '待审核'
    case 'DRAFT': return '草稿'
    case 'REJECTED': return '已驳回'
    case 'TAKEN_DOWN': return '已下架'
    default: return '未知'
  }
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD')
}

// 监听编辑对话框打开，初始化表单
const handleEditProfileOpen = () => {
  if (!authStore.user) return
  
  editForm.value = {
    displayName: authStore.user.displayName || '',
    bio: authStore.user.bio || '',
    avatar: authStore.user.avatar || ''
  }
}

onMounted(() => {
  fetchUserPosts()
})

// 监听对话框显示状态
watch(showEditProfile, (newVal) => {
  if (newVal) {
    handleEditProfileOpen()
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

.profile-avatar {
  flex-shrink: 0;
}

.user-avatar {
  border: 4px solid white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.profile-info {
  flex: 1;
}

.user-identity {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;

  @media (max-width: 768px) {
    justify-content: center;
  }
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

  @media (max-width: 768px) {
    justify-content: center;
  }
}

.stat-item {
  text-align: center;
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

.profile-actions {
  flex-shrink: 0;
}

.profile-content {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 2rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.profile-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.settings-card {
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

.setting-label {
  color: #6b7280;
}

.setting-value {
  font-weight: 600;
  color: #1f2937;

  &.verified {
    color: #059669;
  }
}

.invite-card {
  background: linear-gradient(135deg, #2563eb, #4f46e5);
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
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;

  &:hover {
    background: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.4);
  }
}

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

.loading-container {
  padding: 1.5rem;
}

.activity-skeleton {
  padding: 1.5rem;
  border-bottom: 1px solid #f3f4f6;

  &:last-child {
    border-bottom: none;
  }
}

.empty-activity {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.activity-list {
  padding: 0 1.5rem 1.5rem;
}

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

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #9ca3af;
}

.dialog-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
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