<template>
  <div class="group-invites" v-loading="loading">
    <el-card>
      <template #header>
        <div class="header">
          <div>
            <h3>我收到的群邀请</h3>
            <p>可在此接受或拒绝私密群邀请</p>
          </div>
          <el-select v-model="statusFilter" style="width: 180px" @change="loadInvites">
            <el-option label="全部状态" value="" />
            <el-option label="待处理" value="PENDING" />
            <el-option label="已接受" value="ACCEPTED" />
            <el-option label="已拒绝" value="REJECTED" />
          </el-select>
        </div>
      </template>

      <el-table :data="groupsStore.invites" empty-text="暂无群邀请">
        <el-table-column prop="groupName" label="群组" min-width="160" />
        <el-table-column prop="inviterName" label="邀请人" min-width="120" />
        <el-table-column prop="message" label="邀请说明" min-width="220" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" @click="toGroup(row.groupId)">查看群组</el-button>
            <template v-if="row.status === 'PENDING'">
              <el-button size="small" type="success" @click="respond(row.groupId, row.id, 'ACCEPT')">接受</el-button>
              <el-button size="small" type="danger" @click="respond(row.groupId, row.id, 'REJECT')">拒绝</el-button>
            </template>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty
            :description="statusFilter === 'PENDING' ? '暂无待处理邀请，去群组广场看看吧' : '暂无符合条件的邀请记录'"
            :image-size="90"
          >
            <el-button type="primary" @click="goGroups">前往群组广场</el-button>
          </el-empty>
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { dayjs } from '../utils/date'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useGroupsStore } from '../stores/groups'

const router = useRouter()
const groupsStore = useGroupsStore()
const loading = ref(false)
const statusFilter = ref<'PENDING' | 'ACCEPTED' | 'REJECTED' | ''>('PENDING')

const loadInvites = async () => {
  loading.value = true
  try {
    await groupsStore.fetchMyInvites(statusFilter.value || undefined)
  } finally {
    loading.value = false
  }
}

const respond = async (groupId: number, inviteId: number, action: 'ACCEPT' | 'REJECT') => {
  await groupsStore.respondInvite(groupId, inviteId, action)
  ElMessage.success(action === 'ACCEPT' ? '已接受邀请' : '已拒绝邀请')
  await loadInvites()
}

const toGroup = (groupId: number) => {
  router.push(`/groups/${groupId}`)
}
const goGroups = () => {
  router.push('/groups')
}

const formatDate = (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm')
const statusText = (status: string) => {
  if (status === 'PENDING') return '待处理'
  if (status === 'ACCEPTED') return '已接受'
  if (status === 'REJECTED') return '已拒绝'
  return '已取消'
}
const statusTagType = (status: string) => {
  if (status === 'PENDING') return 'warning'
  if (status === 'ACCEPTED') return 'success'
  if (status === 'REJECTED') return 'danger'
  return 'info'
}

onMounted(loadInvites)
</script>

<style scoped>
.group-invites {
  max-width: 1100px;
  margin: 0 auto;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header p {
  margin: 6px 0 0;
  color: #666;
}
</style>
