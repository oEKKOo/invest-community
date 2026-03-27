<template>
  <div class="admin-sub-page">
    <div class="header">
      <h2>运营数据分析</h2>
      <el-button @click="fetchData">刷新</el-button>
    </div>

    <div class="stats-grid" v-if="overview">
      <div class="stat-card">7日平均DAU：{{ overview.dauAvg7d }}</div>
      <div class="stat-card">7日发帖：{{ overview.posts7d }}</div>
      <div class="stat-card">7日评论：{{ overview.comments7d }}</div>
      <div class="stat-card">7日举报：{{ overview.reports7d }}</div>
      <div class="stat-card">审核通过率：{{ overview.reviewPassRateAvg7d }}%</div>
    </div>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>论坛活跃度</template>
          <el-table :data="activity" size="small" height="360">
            <el-table-column prop="stat_date" label="日期" width="110" />
            <el-table-column prop="dau" label="DAU" width="80" />
            <el-table-column prop="post_count" label="发帖" width="80" />
            <el-table-column prop="comment_count" label="评论" width="80" />
            <el-table-column prop="report_count" label="举报" width="80" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>热门话题</template>
          <el-table :data="topics" size="small" height="360">
            <el-table-column prop="topic" label="话题" min-width="120" />
            <el-table-column prop="post_count" label="帖子" width="70" />
            <el-table-column prop="comment_count" label="评论" width="70" />
            <el-table-column prop="heat_score" label="热度分" width="90" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as adminApi from '../../api/admin'

const overview = ref<any>(null)
const activity = ref<any[]>([])
const topics = ref<any[]>([])

const fetchData = async () => {
  try {
    const [ov, act, top] = await Promise.all([
      adminApi.getAnalyticsOverview(),
      adminApi.getAnalyticsActivity(),
      adminApi.getAnalyticsTopicsHot({ topN: 20 })
    ])
    overview.value = ov
    activity.value = act.items || []
    topics.value = top.items || []
  } catch (e: any) {
    ElMessage.error(e?.message || '加载分析数据失败')
  }
}

onMounted(fetchData)
</script>

<style scoped>
.admin-sub-page { max-width: 1200px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 14px; }
.stat-card { background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 10px; font-weight: 600; }
</style>
