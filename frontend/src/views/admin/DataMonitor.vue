<template>
  <div class="data-monitor">
    <div class="page-header">
      <h2 class="page-title">数据监控面板</h2>
      <el-button size="small" @click="refreshAll" :loading="refreshing">
        <el-icon><RefreshRight /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 系统状态卡-->
    <div class="status-grid" v-if="!statusLoading && status">
      <div class="status-card card">
        <div class="status-icon">🔑</div>
        <div class="status-info">
          <div class="status-label">Tushare Token</div>
          <div class="status-value">
            <el-tag :type="status.finnhubKeyConfigured ? 'success' : 'danger'" size="small">
              {{ status.finnhubKeyConfigured ? '已配' : '未配' }}
            </el-tag>
          </div>
        </div>
      </div>

      <div class="status-card card">
        <div class="status-icon">📦</div>
        <div class="status-info">
          <div class="status-label">资产数量</div>
          <div class="status-value count">{{ status.assetCount?.toLocaleString() }}</div>
        </div>
      </div>

      <div class="status-card card">
        <div class="status-icon">📊</div>
        <div class="status-info">
          <div class="status-label">行情快照</div>
          <div class="status-value count">{{ status.snapshotCount?.toLocaleString() }}</div>
        </div>
      </div>

      <div class="status-card card">
        <div class="status-icon">📈</div>
        <div class="status-info">
          <div class="status-label">K线数</div>
          <div class="status-value count">{{ status.klineCount?.toLocaleString() }}</div>
        </div>
      </div>
    </div>

    <div v-else-if="statusLoading" class="status-grid">
      <div class="status-card card" v-for="i in 4" :key="i">
        <el-skeleton :rows="2" animated />
      </div>
    </div>

    <!-- 最近任务状态-->
    <div class="card recent-jobs-card" v-if="status?.recentJobs">
      <div class="card-header">
        <h3 class="card-title">最近任务状态</h3>
      </div>
      <div class="jobs-grid">
        <div
          v-for="(jobData, jobType) in status.recentJobs"
          :key="jobType"
          class="job-status-item"
        >
          <div class="job-type">{{ jobType }}</div>
          <div class="job-info">
            <el-tag :type="getJobStatusTagType(jobData?.status)" size="small">
              {{ jobData?.status || '--' }}
            </el-tag>
            <span class="job-rows" v-if="jobData?.affected_rows !== undefined">
              {{ jobData.affected_rows }} --
            </span>
            <span class="job-time" v-if="jobData?.started_at">
              {{ formatJobTime(jobData.started_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 手动触发任务 -->
    <div class="card trigger-card">
      <div class="card-header">
        <h3 class="card-title">手动触发任务</h3>
      </div>

      <div class="trigger-form">
        <div class="form-row">
          <el-select v-model="triggerForm.jobType" placeholder="选择任务类型" size="default" class="trigger-select">
            <el-option label="SYMBOLS_SYNC - 同步资产符号" value="SYMBOLS_SYNC" />
            <el-option label="KLINE_SYNC - 同步K线数" value="KLINE_SYNC" />
            <el-option label="QUOTE_REFRESH - 刷新行情快照" value="QUOTE_REFRESH" />
            <el-option label="DQ_CHECK - 数据质量检查" value="DQ_CHECK" />
            <el-option label="CLEANUP - 清理过期数据" value="CLEANUP" />
          </el-select>

          <el-select
            v-if="triggerForm.jobType === 'SYMBOLS_SYNC'"
            v-model="triggerForm.market"
            placeholder="市场（可选）"
            clearable
            size="default"
            class="trigger-market"
          >
            <el-option label="SH" value="SH" />
            <el-option label="SZ" value="SZ" />
            <el-option label="HK" value="HK" />
            <el-option label="US" value="US" />
          </el-select>

          <el-input-number
            v-if="['KLINE_SYNC', 'DQ_CHECK'].includes(triggerForm.jobType)"
            v-model="triggerForm.daysBack"
            :min="1"
            :max="365"
            placeholder="回溯天数"
            size="default"
            class="trigger-days"
          />

          <el-button
            type="primary"
            @click="handleTriggerJob"
            :loading="triggering"
            :disabled="!triggerForm.jobType"
            size="default"
          >
            触发任务
          </el-button>
        </div>

        <!-- 触发结果 -->
        <el-alert
          v-if="triggerResult"
          :title="triggerResult.message || '任务已触发'"
          :type="triggerResult.success ? 'success' : 'error'"
          show-icon
          :closable="true"
          @close="triggerResult = null"
          class="trigger-result"
        />
      </div>
    </div>

    <!-- 任务日志 -->
    <div class="card jobs-log-card">
      <div class="card-header">
        <h3 class="card-title">任务日志</h3>
        <div class="log-filters">
          <el-select
            v-model="logFilter.jobType"
            placeholder="全部类型"
            clearable
            size="small"
            @change="loadJobs"
            style="width: 160px;"
          >
            <el-option label="全部类型" value="" />
            <el-option label="SYMBOLS_SYNC" value="SYMBOLS_SYNC" />
            <el-option label="KLINE_SYNC" value="KLINE_SYNC" />
            <el-option label="QUOTE_REFRESH" value="QUOTE_REFRESH" />
            <el-option label="DQ_CHECK" value="DQ_CHECK" />
            <el-option label="CLEANUP" value="CLEANUP" />
          </el-select>

          <el-select
            v-model="logFilter.status"
            placeholder="全部状态"
            clearable
            size="small"
            @change="loadJobs"
            style="width: 120px;"
          >
            <el-option label="全部状态" value="" />
            <el-option label="SUCCESS" value="SUCCESS" />
            <el-option label="FAILED" value="FAILED" />
            <el-option label="RUNNING" value="RUNNING" />
          </el-select>
        </div>
      </div>

      <div v-if="jobsLoading" class="jobs-loading">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="jobs.length === 0" class="jobs-empty">
        <el-empty description="暂无任务记录" :image-size="60" />
      </div>

      <div v-else class="jobs-table">
        <div class="table-header">
          <div>ID</div>
          <div>任务类型</div>
          <div>状态</div>
          <div>影响行数</div>
          <div>开始时间</div>
          <div>耗时</div>
          <div>备注</div>
        </div>
        <div
          v-for="job in jobs"
          :key="job.id"
          class="table-row"
          :class="job.status.toLowerCase()"
        >
          <div class="job-id">#{{ job.id }}</div>
          <div class="job-type-badge">{{ job.jobType }}</div>
          <div>
            <el-tag :type="getJobStatusTagType(job.status)" size="small">{{ job.status }}</el-tag>
          </div>
          <div class="job-rows-col">{{ job.affectedRows ?? '--' }}</div> 
          <div class="job-time-col">{{ formatJobTime(job.startedAt) }}</div>
          <div class="job-duration">{{ job.durationSeconds ? `${job.durationSeconds.toFixed(1)}s` : '--' }}</div>
          <div class="job-message" :title="job.message">{{ job.message || '--' }}</div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="jobs-pagination" v-if="jobsTotal > jobsPageSize">
        <el-pagination
          v-model="jobsPage"
          :page-size="jobsPageSize"
          :total="jobsTotal"
          layout="prev, pager, next"
          @current-change="loadJobs"
      >
      </el-pagination>
          small
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { RefreshRight } from '@element-plus/icons-vue'
import { getMarketStatus, getDataJobs, triggerDataJob } from '../../api/market'
import type { MarketStatus, DataJobStatus } from '../../types/market'

const statusLoading = ref(false)
const jobsLoading = ref(false)
const refreshing = ref(false)
const triggering = ref(false)

const status = ref<MarketStatus | null>(null)
const jobs = ref<DataJobStatus[]>([])
const jobsTotal = ref(0)
const jobsPage = ref(1)
const jobsPageSize = ref(20)

const triggerForm = ref<{
  jobType: string
  market?: string
  daysBack?: number
}>({
  jobType: '',
  market: undefined,
  daysBack: 30
})

const triggerResult = ref<{ success: boolean; message: string } | null>(null)

const logFilter = ref({
  jobType: '',
  status: ''
})

const loadStatus = async () => {
  statusLoading.value = true
  try {
    status.value = await getMarketStatus()
  } catch {
    status.value = null
  } finally {
    statusLoading.value = false
  }
}

const loadJobs = async () => {
  jobsLoading.value = true
  try {
    const params: any = {
      page: jobsPage.value,
      pageSize: jobsPageSize.value
    }
    if (logFilter.value.jobType) params.jobType = logFilter.value.jobType
    if (logFilter.value.status) params.status = logFilter.value.status

    const res = await getDataJobs(params)
    jobs.value = res.items
    jobsTotal.value = res.total
  } catch {
    jobs.value = []
  } finally {
    jobsLoading.value = false
  }
}

const handleTriggerJob = async () => {
  if (!triggerForm.value.jobType) return
  triggering.value = true
  triggerResult.value = null
  try {
    const params: any = { jobType: triggerForm.value.jobType }
    if (triggerForm.value.market) params.market = triggerForm.value.market
    if (triggerForm.value.daysBack) params.daysBack = triggerForm.value.daysBack

    const res = await triggerDataJob(params)
    triggerResult.value = { success: true, message: `任务 ${triggerForm.value.jobType} 已触发` }
    ElMessage.success('任务触发成功')
    // 延迟刷新日志
    setTimeout(() => {
      loadJobs()
      loadStatus()
    }, 2000)
  } catch (e: any) {
    triggerResult.value = {
      success: false,
      message: e?.response?.data?.detail || '任务触发失败，请检查权限或参数'
    }
    ElMessage.error('触发失败')
  } finally {
    triggering.value = false
  }
}

const refreshAll = async () => {
  refreshing.value = true
  await Promise.all([loadStatus(), loadJobs()])
  refreshing.value = false
  ElMessage.success('数据已刷新')
}

const getJobStatusTagType = (status?: string) => {
  if (status === 'SUCCESS') return 'success'
  if (status === 'FAILED') return 'danger'
  if (status === 'RUNNING') return 'warning'
  return 'info'
}

const formatJobTime = (timeStr?: string) => {
  if (!timeStr) return '--';
  const d = new Date(timeStr)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${min}`
}

onMounted(() => {
  loadStatus()
  loadJobs()
})
</script>

<style lang="scss" scoped>
.data-monitor {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .page-title {
    font-size: 1.375rem;
    font-weight: 700;
    color: #F0F4FF;
    margin: 0;
  }
}

.card {
  background: #141B2D;
  border: 1px solid rgba(15, 23, 42, 0.05);
  border-radius: 14px;
  padding: 1.25rem;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #F0F4FF;
  margin: 0;
}

// 状态卡-->
.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;

  @media (max-width: 900px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.status-card {
  display: flex;
  align-items: center;
  gap: 0.875rem;

  .status-icon {
    font-size: 1.5rem;
    flex-shrink: 0;
  }

  .status-label {
    font-size: 0.75rem;
    color: #6B7A99;
    margin-bottom: 4px;
  }

  .status-value {
    font-size: 0.875rem;
    color: #E2E8F0;

    &.count {
      font-size: 1.1rem;
      font-weight: 700;
      color: #3B82F6;
    }
  }
}

// 最近任务状态-->
.recent-jobs-card {
  .jobs-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 0.75rem;
  }

  .job-status-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(15, 23, 42, 0.05);
    border-radius: 8px;
    padding: 0.75rem;

    .job-type {
      font-size: 0.75rem;
      font-weight: 700;
      color: #3B82F6;
      margin-bottom: 6px;
    }

    .job-info {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }

    .job-rows, .job-time {
      font-size: 0.7rem;
      color: #6B7A99;
    }
  }
}

// 触发任务
.trigger-form {
  .form-row {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
  }

  .trigger-select {
    min-width: 260px;
    flex: 1;
  }

  .trigger-market, .trigger-days {
    width: 140px;
  }

  .trigger-result {
    margin-top: 0.75rem;
  }
}

// 任务日志
.log-filters {
  display: flex;
  gap: 0.5rem;
}

.jobs-loading, .jobs-empty {
  padding: 1rem;
}

.jobs-table {
  overflow-x: auto;
}

.table-header {
  display: grid;
  grid-template-columns: 60px 150px 100px 80px 120px 80px 1fr;
  gap: 0;
  padding: 0.5rem 0.75rem;
  background: rgba(15, 23, 42, 0.03);
  border-radius: 6px;
  font-size: 0.7rem;
  color: #6B7A99;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 4px;
}

.table-row {
  display: grid;
  grid-template-columns: 60px 150px 100px 80px 120px 80px 1fr;
  gap: 0;
  padding: 0.625rem 0.75rem;
  border-bottom: 1px solid rgba(15, 23, 42, 0.03);
  font-size: 0.8rem;
  color: #A0AABF;
  align-items: center;
  transition: background 0.15s;

  &:hover {
    background: rgba(255, 255, 255, 0.025);
  }

  &:last-child {
    border-bottom: none;
  }

  &.failed {
    background: rgba(245, 108, 108, 0.04);
  }

  &.running {
    background: rgba(230, 162, 60, 0.04);
  }
}

.job-id {
  color: #6B7A99;
  font-size: 0.7rem;
}

.job-type-badge {
  font-size: 0.7rem;
  font-weight: 600;
  color: #3B82F6;
}

.job-rows-col, .job-duration {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.75rem;
}

.job-time-col {
  font-size: 0.7rem;
  color: #6B7A99;
}

.job-message {
  font-size: 0.72rem;
  color: #6B7A99;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.jobs-pagination {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}
</style>


