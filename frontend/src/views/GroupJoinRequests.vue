<template>
  <div class="group-join-requests" v-loading="loading">
    <el-card>
      <template #header>
        <div class="header">
          <div>
            <h3>入群申请审核</h3>
            <p>仅审核人可查看并处理申请</p>
          </div>
          <el-select v-model="statusFilter" style="width: 160px" @change="loadRequests">
            <el-option label="待审核" value="PENDING" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已拒绝" value="REJECTED" />
            <el-option label="全部" value="" />
          </el-select>
        </div>
      </template>

      <el-table :data="groupsStore.joinRequests" empty-text="暂无申请记录">
        <el-table-column prop="userName" label="申请人" min-width="140" />
        <el-table-column prop="message" label="申请说明" min-width="220" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="申请时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'PENDING'"
              size="small"
              type="success"
              @click="handleReview(row.id, 'APPROVE')"
            >
              通过
            </el-button>
            <el-button
              v-if="row.status === 'PENDING'"
              size="small"
              type="danger"
              @click="handleReview(row.id, 'REJECT')"
            >
              拒绝
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useGroupsStore } from '../stores/groups'

const route = useRoute()
const groupsStore = useGroupsStore()
const loading = ref(false)
const statusFilter = ref<'PENDING' | 'APPROVED' | 'REJECTED' | ''>('PENDING')
const groupId = computed(() => Number(route.params.groupId))

const loadRequests = async () => {
  loading.value = true
  try {
    await groupsStore.fetchJoinRequests(groupId.value, statusFilter.value || undefined)
  } finally {
    loading.value = false
  }
}

const formatDate = (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm')

const handleReview = async (requestId: number, action: 'APPROVE' | 'REJECT') => {
  await groupsStore.reviewJoinRequest(groupId.value, requestId, action)
  ElMessage.success('审核成功')
  await loadRequests()
}

onMounted(loadRequests)
</script>

<style scoped>
.group-join-requests {
  max-width: 1100px;
  margin: 0 auto;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header p {
  margin: 6px 0 0;
  color: #666;
}
</style>
