<template>
  <div class="admin-sub-page">
    <div class="header">
      <h2>可疑内容队列</h2>
      <el-button @click="fetchData">刷新</el-button>
    </div>
    <el-table :data="items" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="content_title" label="内容标题" min-width="220" />
      <el-table-column prop="source" label="来源" width="100" />
      <el-table-column prop="risk_level" label="风险等级" width="100" />
      <el-table-column prop="risk_score" label="风险分" width="90" />
      <el-table-column prop="reason_summary" label="命中摘要" min-width="240" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="decide(row.id, 'PUBLISHED')">通过</el-button>
          <el-button size="small" type="warning" @click="decide(row.id, 'TAKEN_DOWN')">下架</el-button>
          <el-button size="small" type="danger" @click="decide(row.id, 'REJECTED')">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as adminApi from '../../api/admin'

const items = ref<adminApi.ModerationQueueItem[]>([])
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    const res = await adminApi.getModerationQueue({ status: 'PENDING', page: 1, pageSize: 50 })
    items.value = res.items || []
  } catch (e: any) {
    ElMessage.error(e?.message || '获取队列失败')
  } finally {
    loading.value = false
  }
}

const decide = async (id: number, status: 'PUBLISHED' | 'REJECTED' | 'TAKEN_DOWN') => {
  try {
    await adminApi.decideModerationQueue(id, { status })
    ElMessage.success('处理成功')
    await fetchData()
  } catch (e: any) {
    ElMessage.error(e?.message || '处理失败')
  }
}

onMounted(fetchData)
</script>

<style scoped>
.admin-sub-page { max-width: 1200px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
</style>
