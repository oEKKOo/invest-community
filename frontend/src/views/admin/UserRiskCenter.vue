<template>
  <div class="admin-sub-page">
    <div class="header">
      <h2>用户风险中心</h2>
      <el-button @click="fetchData">刷新</el-button>
    </div>
    <el-table :data="items" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column prop="displayName" label="昵称" width="160" />
      <el-table-column prop="riskScore" label="风险分" width="90" />
      <el-table-column prop="qualityScore" label="质量分" width="90" />
      <el-table-column prop="reportedCount" label="被举报" width="90" />
      <el-table-column prop="violationCount" label="违规" width="90" />
      <el-table-column prop="points" label="积分" width="90" />
      <el-table-column prop="level" label="等级" width="90" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="warning" @click="warning(row.id)">警告</el-button>
          <el-button size="small" @click="viewBehavior(row.id)">行为报告</el-button>
          <el-button size="small" type="danger" plain @click="deduct(row.id)">扣分</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as adminApi from '../../api/admin'

const items = ref<adminApi.UserRiskItem[]>([])
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    const res = await adminApi.getAdminUsersRisk({ page: 1, pageSize: 50, sortBy: 'riskScore' })
    items.value = res.items || []
  } catch (e: any) {
    ElMessage.error(e?.message || '获取用户风险列表失败')
  } finally {
    loading.value = false
  }
}

const warning = async (userId: number) => {
  try {
    await adminApi.warningUser(userId, { reason: '风险行为预警' })
    ElMessage.success('警告成功')
  } catch (e: any) {
    ElMessage.error(e?.message || '警告失败')
  }
}

const deduct = async (userId: number) => {
  try {
    await adminApi.adjustUserPoints(userId, { delta: -10, reason: '管理后台人工扣分' })
    ElMessage.success('扣分成功')
    await fetchData()
  } catch (e: any) {
    ElMessage.error(e?.message || '扣分失败')
  }
}

const viewBehavior = async (userId: number) => {
  try {
    const res = await adminApi.getAdminUserBehaviorReport(userId, { range: '7d' })
    ElMessage.info(`近7天发帖 ${res.summary.postCount || 0} 条，评论 ${res.summary.commentCount || 0} 条`)
  } catch (e: any) {
    ElMessage.error(e?.message || '获取行为报告失败')
  }
}

onMounted(fetchData)
</script>

<style scoped>
.admin-sub-page { max-width: 1200px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
</style>
