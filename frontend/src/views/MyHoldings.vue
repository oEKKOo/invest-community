<template>
  <div class="my-holdings">
    <div class="holdings-header">
      <div class="header-left">
        <h2 class="page-title">我的持仓</h2>
        <span class="subtitle">管理并跟踪您持有的资产持仓</span>
      </div>
      <el-button
        type="primary"
        size="large"
        :icon="Plus"
        class="add-btn"
        @click="openAddDialog()"
      >
        添加持仓
      </el-button>
    </div>

    <!-- 收益概览 Banner -->
    <div class="perf-banner" v-if="holdings.length > 0">
      <div class="perf-loading-mask" v-if="perfLoading">
        <el-skeleton :rows="2" animated />
      </div>

      <template v-else>
        <!-- 左侧：总市值+ 总成本-->
        <div class="perf-section perf-section--main">
          <div class="perf-metric">
            <span class="perf-metric__label">总市值</span>
            <span class="perf-metric__val">
              {{ perf ? formatMoney(perf.totalMarketValue) : '--' }}
            </span>
          </div>
          <div class="perf-divider" />
          <div class="perf-metric">
            <span class="perf-metric__label">持仓成本</span>
            <span class="perf-metric__val perf-metric__val--sub">
              {{ perf ? formatMoney(perf.totalCostValue) : '--' }}
            </span>
          </div>
        </div>

        <div class="perf-sep" />

        <!-- 中：当日收益 -->
        <div class="perf-section">
          <div class="perf-metric__label">当日收益</div>
          <div
            class="perf-metric__pnl"
            :class="pnlClass(perf?.totalDailyPnl)"
          >
            {{ perf ? formatPnl(perf.totalDailyPnl) : '--' }}
          </div>
          <div
            class="perf-metric__rate"
            :class="pnlClass(perf?.totalDailyReturn)"
          >
            {{ perf ? formatRate(perf.totalDailyReturn) : '' }}
          </div>
        </div>

        <div class="perf-sep" />

        <!-- 右：持有收益（浮盈亏）-->
        <div class="perf-section">
          <div class="perf-metric__label">持有收益（浮盈）</div>
          <div
            class="perf-metric__pnl"
            :class="pnlClass(perf?.totalUnrealizedPnl)"
          >
            {{ perf ? formatPnl(perf.totalUnrealizedPnl) : '--' }}
          </div>
          <div
            class="perf-metric__rate"
            :class="pnlClass(perf?.totalUnrealizedReturn)"
          >
            {{ perf ? formatRate(perf.totalUnrealizedReturn) : '' }}
          </div>
        </div>

        <!-- 估值日期-->
        <div class="perf-date" v-if="perf?.asOf">
          估值日期：{{ perf.asOf }}
          <el-tooltip content="基于日K收盘价，每日一次更新，无实时行情" placement="top">
            <el-icon class="perf-date__tip"><InfoFilled /></el-icon>
          </el-tooltip>
        </div>
        <div class="perf-nodata" v-else-if="perf && !perf.hasAnyData">
          <el-icon><Warning /></el-icon> 暂无行情快照，请先运行数据同步
        </div>
      </template>
    </div>

    <!-- 持仓汇总卡片-->
    <div class="summary-cards" v-if="holdings.length > 0">
      <div class="summary-card">
        <div class="summary-label">持仓数量</div>
        <div class="summary-value">{{ holdings.length }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">持仓成本（估算）</div>
        <div class="summary-value">{{ formatTotalCost }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">市场分布</div>
        <div class="summary-markets">
          <el-tag
            v-for="(count, market) in marketDistribution"
            :key="market"
            size="small"
            class="market-tag"
          >
            {{ market }}: {{ count }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 累计收益曲线 -->
    <div class="returns-chart-card" v-if="holdings.length > 0">
      <div class="returns-chart-header">
        <div class="returns-chart-title-row">
          <h3 class="returns-chart-title">累计收益曲线</h3>
          <el-tooltip content="基于每日收盘价快照计算，以持仓成本为基准线（0%）" placement="top">
            <el-icon class="info-icon"><InfoFilled /></el-icon>
          </el-tooltip>
        </div>
        <div class="returns-chart-meta" v-if="returnsHistory && returnsHistory.items.length">
          <span class="meta-item">
            <span class="meta-label">数据区间</span>
            <span class="meta-value mono">{{ returnsHistory.items[0].date }} - {{ returnsHistory.items[returnsHistory.items.length - 1].date }}</span>
          </span>
          <span class="meta-item">
            <span class="meta-label">{{ returnsHistory.items.length }} 个交易日</span>
          </span>
          <span
            class="meta-item meta-return"
            :class="Number(returnsHistory.items[returnsHistory.items.length - 1].unrealizedReturn) >= 0 ? 'pnl-up' : 'pnl-down'"
          >
            最新累计收益率：
            <strong>
              {{ Number(returnsHistory.items[returnsHistory.items.length - 1].unrealizedReturn) >= 0 ? '+' : '' }}{{ (Number(returnsHistory.items[returnsHistory.items.length - 1].unrealizedReturn) * 100).toFixed(2) }}%
            </strong>
          </span>
        </div>
      </div>

      <div class="returns-chart-body">
        <el-skeleton v-if="returnsHistoryLoading" :rows="4" animated style="padding: 1rem" />

        <el-empty
          v-else-if="!returnsHistory || !returnsHistory.items.length"
          description="暂无收益历史数据，请先运行数据同步生成每日快照"
          :image-size="80"
        />

        <v-chart
          v-else
          class="returns-chart"
          :option="returnsChartOption"
          autoresize
        />
      </div>
    </div>

    <!-- 持仓列表 -->
    <div class="holdings-table-wrap">
      <el-skeleton :rows="5" animated v-if="loading" />

      <el-empty
        v-else-if="holdings.length === 0"
        description="暂无持仓记录，点击「添加持仓」开始跟踪您的投资"
        :image-size="120"
      >
        <el-button type="primary" @click="openAddDialog()">添加第一笔持仓</el-button>
      </el-empty>

      <el-table
        v-else
        :data="holdings"
        class="holdings-table"
        row-class-name="holding-row"
        @row-click="(row) => openEditDialog(row)"
      >
        <!-- 资产信息 -->
        <el-table-column label="资产" min-width="180">
          <template #default="{ row }">
            <div class="asset-cell">
              <span class="asset-code" @click.stop="goToAsset(row.assetId)">{{ row.code }}</span>
              <span class="asset-name">{{ row.name }}</span>
              <el-tag size="small" class="market-badge">{{ row.displayMarket }}</el-tag>
            </div>
          </template>
        </el-table-column>

        <!-- 类型 -->
        <el-table-column label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getAssetTypeTag(row.assetType)">
              {{ row.assetType }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 持有数量 -->
        <el-table-column label="数量（股）" width="130" align="right">
          <template #default="{ row }">
            <span class="mono-value">{{ formatNumber(row.quantity) }}</span>
          </template>
        </el-table-column>

        <!-- 成本均价 -->
        <el-table-column label="成本均价" width="130" align="right">
          <template #default="{ row }">
            <span class="mono-value">¥ {{ formatPrice(row.costPrice) }}</span>
          </template>
        </el-table-column>

        <!-- 持仓成本 -->
        <el-table-column label="持仓成本" width="130" align="right">
          <template #default="{ row }">
            <span class="mono-value cost-value">
              ¥ {{ formatCost(row.quantity, row.costPrice) }}
            </span>
          </template>
        </el-table-column>

        <!-- 今日估值价 -->
        <el-table-column label="今日估值价" width="110" align="right">
          <template #default="{ row }">
            <template v-if="getPerfItem(row.id)?.hasData">
              <span class="mono-value">¥ {{ formatPrice(getPerfItem(row.id)?.todayPrice) }}</span>
            </template>
            <span v-else class="no-data-dash">--</span>
          </template>
        </el-table-column>

        <!-- 市值-->
        <el-table-column label="市值" width="120" align="right">
          <template #default="{ row }">
            <template v-if="getPerfItem(row.id)?.hasData">
              <span class="mono-value">{{ formatMoneyShort(getPerfItem(row.id)?.marketValue) }}</span>
            </template>
            <span v-else class="no-data-dash">--</span>
          </template>
        </el-table-column>

        <!-- 当日收益 -->
        <el-table-column label="当日收益" width="130" align="right">
          <template #default="{ row }">
            <template v-if="getPerfItem(row.id)?.hasData">
              <div class="pnl-cell" :class="pnlClass(getPerfItem(row.id)?.dailyPnl)">
                <span>{{ formatPnl(getPerfItem(row.id)?.dailyPnl) }}</span>
                <span class="pnl-rate">{{ formatRate(getPerfItem(row.id)?.dailyReturn) }}</span>
              </div>
            </template>
            <span v-else class="no-data-dash">--</span>
          </template>
        </el-table-column>

        <!-- 持有收益（浮盈） -->
        <el-table-column label="持有收益" width="130" align="right">
          <template #default="{ row }">
            <template v-if="getPerfItem(row.id)?.hasData">
              <div class="pnl-cell" :class="pnlClass(getPerfItem(row.id)?.unrealizedPnl)">
                <span>{{ formatPnl(getPerfItem(row.id)?.unrealizedPnl) }}</span>
                <span class="pnl-rate">{{ formatRate(getPerfItem(row.id)?.unrealizedReturn) }}</span>
              </div>
            </template>
            <span v-else class="no-data-dash">--</span>
          </template>
        </el-table-column>

        <!-- 备注 -->
        <el-table-column label="备注" min-width="100">
          <template #default="{ row }">
            <span class="notes-text" :title="row.notes">{{ row.notes || '--' }}</span>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              text
              @click.stop="openEditDialog(row)"
            >编辑</el-button>
            <el-button
              size="small"
              type="danger"
              text
              @click.stop="handleDelete(row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加/编辑持仓对话框-->
    <el-dialog
      v-model="showDialog"
      :title="editingHolding ? '编辑持仓' : '添加持仓'"
      width="500px"
      class="holding-dialog"
      @closed="resetDialog"
    >
      <el-form
        ref="holdingFormRef"
        :model="holdingForm"
        :rules="holdingRules"
        label-width="90px"
        label-position="left"
      >
        <!-- 资产选择（新增时可搜索）-->
        <el-form-item label="选择资产" prop="assetId" v-if="!editingHolding">
          <el-select
            v-model="holdingForm.selectedAsset"
            filterable
            remote
            clearable
            placeholder="输入代码或名称搜索"
            :remote-method="searchAssets"
            :loading="assetSearchLoading"
            value-key="id"
            style="width: 100%"
            @change="onAssetSelected"
          >
            <el-option
              v-for="item in assetSearchResults"
              :key="item.id"
              :label="`${item.code} ${item.name}`"
              :value="item"
            >
              <div class="asset-option">
                <span class="opt-code">{{ item.code }}</span>
                <span class="opt-name">{{ item.name }}</span>
                <el-tag size="small" class="opt-market">{{ item.market }}</el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 编辑时展示当前资产（不可修改）-->
        <el-form-item label="持仓资产" v-if="editingHolding">
          <div class="edit-asset-info">
            <span class="asset-code">{{ editingHolding.code }}</span>
            <span class="asset-name">{{ editingHolding.name }}</span>
            <el-tag size="small">{{ editingHolding.displayMarket }}</el-tag>
          </div>
        </el-form-item>

        <el-form-item label="持有数量" prop="quantity">
          <el-input-number
            v-model="holdingForm.quantity"
            :min="0"
            :precision="0"
            style="width: 100%"
            placeholder="持有股数/份额"
            controls-position="right"
          />
            <div class="form-hint">股票单位：股；基金/ETF单位：份</div>
        </el-form-item>

        <el-form-item label="成本均价" prop="costPrice">
          <el-input-number
            v-model="holdingForm.costPrice"
            :min="0"
            :precision="2"
            style="width: 100%"
            placeholder="买入均价（元）"
            controls-position="right"
          />
          <div class="form-hint">
            持仓成本：
            <strong>¥ {{ formatCost(holdingForm.quantity, holdingForm.costPrice) }}</strong>
          </div>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="holdingForm.notes"
            type="textarea"
            :rows="2"
            placeholder="可填写买入理由、策略备注等..."
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDialog = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleSave"
            :loading="saving"
          >
            {{ editingHolding ? '保存修改' : '添加持仓' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, InfoFilled, Warning } from '@element-plus/icons-vue'
import type { UserHolding, HoldingPerformance, HoldingPerformanceItem } from '@/types'
import type { AssetWithQuote } from '@/api/market'
import { getAssetsWithQuote } from '@/api/market'
import { getMyHoldings, upsertHolding, updateHolding, deleteHolding, getHoldingPerformance, getHoldingReturnsHistory } from '@/api/holdings'
import type { HoldingReturnsHistory } from '@/api/holdings'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent])

const router = useRouter()

// ---- 状态----
const loading = ref(false)
const saving = ref(false)
const holdings = ref<UserHolding[]>([])
const showDialog = ref(false)
const editingHolding = ref<UserHolding | null>(null)

// 收益数据
const perfLoading = ref(false)
const perf = ref<HoldingPerformance | null>(null)
// 建立 holdingId -> item 的映射，供表格按行查询
const perfMap = ref<Map<number, HoldingPerformanceItem>>(new Map())

// 累计收益历史
const returnsHistoryLoading = ref(false)
const returnsHistory = ref<HoldingReturnsHistory | null>(null)

// 资产搜索
const assetSearchLoading = ref(false)
const assetSearchResults = ref<AssetWithQuote[]>([])

// 表单
const holdingFormRef = ref<FormInstance>()
const holdingForm = ref({
  selectedAsset: null as AssetWithQuote | null,
  assetId: null as number | null,
  quantity: 0,
  costPrice: 0,
  notes: ''
})

const holdingRules: FormRules = {
  assetId: [
    { required: true, message: '请选择资产', trigger: 'change' }
  ],
  quantity: [
    { required: true, message: '请输入持有数量', trigger: 'blur' },
    { type: 'number', min: 0, message: '数量不能为负数', trigger: 'blur' }
  ],
  costPrice: [
    { required: true, message: '请输入成本均价', trigger: 'blur' },
    { type: 'number', min: 0, message: '成本价不能为负数', trigger: 'blur' }
  ]
}

// ---- 计算属性----
const formatTotalCost = computed(() => {
  const total = holdings.value.reduce((sum, h) => {
    return sum + Number(h.quantity) * Number(h.costPrice)
  }, 0)
  if (total >= 100_000_000) return `¥ ${(total / 100_000_000).toFixed(2)} 亿`
  if (total >= 10_000) return `¥ ${(total / 10_000).toFixed(2)} 万`
  return `¥ ${total.toFixed(2)}`
})

const marketDistribution = computed(() => {
  const dist: Record<string, number> = {}
  holdings.value.forEach(h => {
    const m = h.displayMarket || h.market || '其他'
    dist[m] = (dist[m] || 0) + 1
  })
  return dist
})

// ---- 方法 ----
const fetchHoldings = async () => {
  loading.value = true
  try {
    const res = await getMyHoldings()
    holdings.value = res.items || []
  } catch {
    ElMessage.error('获取持仓数据失败')
  } finally {
    loading.value = false
  }
}

const fetchPerformance = async () => {
  perfLoading.value = true
  try {
    const data = await getHoldingPerformance()
    perf.value = data
    // 建立 holdingId -> item 索引
    const map = new Map<number, HoldingPerformanceItem>()
    data.items?.forEach(item => map.set(item.holdingId, item))
    perfMap.value = map
  } catch {
    // 收益接口失败不影响主列表展示
    perf.value = null
  } finally {
    perfLoading.value = false
  }
}

const fetchReturnsHistory = async () => {
  returnsHistoryLoading.value = true
  try {
    const data = await getHoldingReturnsHistory()
    returnsHistory.value = data
  } catch {
    returnsHistory.value = null
  } finally {
    returnsHistoryLoading.value = false
  }
}

// 累计收益折线图 ECharts 配置
const returnsChartOption = computed(() => {
  const items = returnsHistory.value?.items ?? []
  if (!items.length) return {}

  const dates = items.map(i => i.date)
  const returnRates = items.map(i => (Number(i.unrealizedReturn) * 100).toFixed(2))
  const marketValues = items.map(i => Number(i.totalMarketValue).toFixed(2))
  const costValue = Number(returnsHistory.value?.totalCostValue ?? 0)

  // 找最新值的颜色
  const lastReturn = Number(returnRates[returnRates.length - 1])
  const lineColor = lastReturn >= 0 ? '#10b981' : '#f43f5e'

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: 'rgba(29, 78, 216, 0.22)',
      borderWidth: 1,
      textStyle: { color: '#1F2937', fontFamily: 'IBM Plex Mono', fontSize: 12 },
      formatter: (params: any[]) => {
        const p = params[0]
        const mv = Number(marketValues[p.dataIndex])
        const pnl = mv - costValue
        const pnlStr = pnl >= 0 ? `+${pnl.toFixed(2)}` : pnl.toFixed(2)
        const pnlColor = pnl >= 0 ? '#10b981' : '#f43f5e'
        const rateVal = Number(returnRates[p.dataIndex])
        const rateStr = rateVal >= 0 ? `+${rateVal}%` : `${rateVal}%`
        return `
          <div style="min-width:160px">
            <div style="color:#A0AABF;margin-bottom:4px">${p.axisValue}</div>
            <div>市值：<span style="font-weight:700">¥ ${mv >= 10000 ? (mv / 10000).toFixed(2) + '万' : mv.toFixed(2)}</span></div>
            <div>浮盈：<span style="color:${pnlColor};font-weight:700">${pnlStr}</span></div>
            <div>收益率：<span style="color:${pnlColor};font-weight:700">${rateStr}</span></div>
          </div>
        `
      }
    },
    grid: { top: 20, right: 20, bottom: 40, left: 60 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: {
        color: '#475569',
        fontSize: 11,
        fontFamily: 'IBM Plex Mono',
        rotate: dates.length > 60 ? 30 : 0,
        interval: Math.floor(dates.length / 8),
      },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#475569',
        fontSize: 11,
        fontFamily: 'IBM Plex Mono',
        formatter: (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`,
      },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    },
    series: [
      {
        name: '累计收益',
        type: 'line',
        data: returnRates.map(Number),
        smooth: true,
        symbol: 'none',
        lineStyle: { color: lineColor, width: 2 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: lastReturn >= 0 ? 'rgba(16,185,129,0.25)' : 'rgba(244,63,94,0.25)' },
              { offset: 1, color: 'rgba(0,0,0,0)' },
            ]
          }
        },
        markLine: {
          silent: true,
          symbol: ['none', 'none'],
          lineStyle: { color: 'rgba(255,255,255,0.2)', type: 'dashed', width: 1 },
          data: [{ yAxis: 0 }],
        },
      }
    ]
  }
})

/** 根据持仓 id 查找收益条目 */
const getPerfItem = (holdingId: number): HoldingPerformanceItem | undefined => {
  return perfMap.value.get(holdingId)
}

const searchAssets = async (query: string) => {
  if (!query) {
    assetSearchResults.value = []
    return
  }
  assetSearchLoading.value = true
  try {
    const res = await getAssetsWithQuote({ q: query, pageSize: 20 })
    assetSearchResults.value = res.items || []
  } catch {
    assetSearchResults.value = []
  } finally {
    assetSearchLoading.value = false
  }
}

const onAssetSelected = (asset: AssetWithQuote | null) => {
  holdingForm.value.selectedAsset = asset
  holdingForm.value.assetId = asset?.id || null
}

const openAddDialog = () => {
  editingHolding.value = null
  showDialog.value = true
}

const openEditDialog = (holding: UserHolding) => {
  editingHolding.value = holding
  holdingForm.value = {
    selectedAsset: null,
    assetId: holding.assetId,
    quantity: Number(holding.quantity),
    costPrice: Number(holding.costPrice),
    notes: holding.notes || ''
  }
  showDialog.value = true
}

const resetDialog = () => {
  editingHolding.value = null
  holdingForm.value = {
    selectedAsset: null,
    assetId: null,
    quantity: 0,
    costPrice: 0,
    notes: ''
  }
  assetSearchResults.value = []
  holdingFormRef.value?.clearValidate()
}

const handleSave = async () => {
  if (!holdingFormRef.value) return

  // 新增时校验已选资产
  if (!editingHolding.value && !holdingForm.value.assetId) {
    ElMessage.warning('请先搜索并选择资产')
    return
  }

  saving.value = true
  try {
    if (editingHolding.value) {
      // 编辑模式
      await updateHolding(editingHolding.value.id, {
        quantity: holdingForm.value.quantity,
        costPrice: holdingForm.value.costPrice,
        notes: holdingForm.value.notes
      })
      ElMessage.success('持仓已更新')
    } else {
      // 新增模式（upsert）
      await upsertHolding({
        assetId: holdingForm.value.assetId!,
        quantity: holdingForm.value.quantity,
        costPrice: holdingForm.value.costPrice,
        notes: holdingForm.value.notes
      })
      ElMessage.success('持仓已添加')
    }
    showDialog.value = false
    await fetchHoldings()
    fetchPerformance() // 非阻塞刷新收益
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (holding: UserHolding) => {
  try {
    await ElMessageBox.confirm(
      `确认删除 ${holding.code} (${holding.name}) 的持仓记录？`,
      '删除持仓',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
    )
    await deleteHolding(holding.id)
    ElMessage.success('持仓已删除')
    await fetchHoldings()
    await fetchPerformance()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const goToAsset = (assetId: number) => {
  router.push(`/assets/${assetId}`)
}

// ---- 格式化----
const formatNumber = (val: number | string) => {
  return Number(val).toLocaleString('zh-CN')
}

const formatPrice = (val: number | string) => {
  return Number(val).toFixed(2)
}

const formatCost = (quantity: number | string, price: number | string) => {
  const cost = Number(quantity) * Number(price)
  if (cost >= 100_000_000) return `${(cost / 100_000_000).toFixed(2)}亿`
  if (cost >= 10_000) return `${(cost / 10_000).toFixed(2)}万`
  return cost.toFixed(2)
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '--';
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const getAssetTypeTag = (type: string) => {
  const map: Record<string, string> = {
    STOCK: '',
    ETF: 'success',
    FUND: 'warning',
    BOND: 'info'
  }
  return map[type] || 'info'
}

/** 格式化货币（带万/亿单位） */
const formatMoney = (val: string | number | null | undefined) => {
  if (val === null || val === undefined) return '--';
  const n = Number(val)
  if (isNaN(n)) return '--';
  if (n >= 1e8) return `¥ ${(n / 1e8).toFixed(2)} 亿`
  if (n >= 1e4) return `¥ ${(n / 1e4).toFixed(2)} 万`
  return `¥ ${n.toFixed(2)}`
}

/** 简短金额格式（表格内） */
const formatMoneyShort = (val: string | number | null | undefined) => {
  if (val === null || val === undefined) return '--';
  const n = Number(val)
  if (isNaN(n)) return '--';
  if (n >= 1e8) return `${(n / 1e8).toFixed(2)}亿`
  if (n >= 1e4) return `${(n / 1e4).toFixed(2)}万`
  return n.toFixed(2)
}

  /** 格式化PnL，带正负号*/
const formatPnl = (val: string | number | null | undefined) => {
  if (val === null || val === undefined) return '--';
  const n = Number(val)
  if (isNaN(n)) return '--';
  const prefix = n >= 0 ? '+' : ''
  if (Math.abs(n) >= 1e8) return `${prefix}${(n / 1e8).toFixed(2)}亿`
  if (Math.abs(n) >= 1e4) return `${prefix}${(n / 1e4).toFixed(2)}万`
  return `${prefix}${n.toFixed(2)}`
}

/** 格式化收益率，如 "0.0556" --> "+5.56%" */
const formatRate = (val: string | number | null | undefined) => {
  if (val === null || val === undefined) return ''
  const n = Number(val)
  if (isNaN(n)) return ''
  const prefix = n >= 0 ? '+' : ''
  return `${prefix}${(n * 100).toFixed(2)}%`
}

/** 根据 PnL 值返回颜色类*/
const pnlClass = (val: string | number | null | undefined) => {
  if (val === null || val === undefined) return ''
  const n = Number(val)
  if (isNaN(n) || n === 0) return 'pnl-zero'
  return n > 0 ? 'pnl-up' : 'pnl-down'
}

onMounted(() => {
  fetchHoldings()
  fetchPerformance()
  fetchReturnsHistory()
})
</script>

<style lang="scss" scoped>
.my-holdings {
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.holdings-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;

  @media (max-width: 640px) {
    flex-direction: column;
    gap: 1rem;
  }
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0;
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: 0.875rem;
  color: $text-muted;
}

.add-btn {
  background: $gradient-primary !important;
  border: none !important;
  box-shadow: $shadow-purple !important;
  font-weight: 600 !important;
  border-radius: 10px !important;

  &:hover {
    box-shadow: 0 8px 24px rgba(29, 78, 216, 0.3) !important;
    transform: translateY(-1px);
  }
}

// ---- 收益 Banner ----
.perf-banner {
  position: relative;
  background: linear-gradient(135deg, rgba(29, 78, 216, 0.08) 0%, rgba(16, 185, 129, 0.06) 100%);
  border: 1px solid rgba(29, 78, 216, 0.12);
  border-radius: $border-radius;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.25rem;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.25rem;
  min-height: 80px;
}

.perf-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 140px;

  &--main {
    flex-direction: row;
    align-items: center;
    gap: 1rem;
  }
}

.perf-sep {
  width: 1px;
  height: 48px;
  background: rgba(255,255,255,0.1);
  flex-shrink: 0;
}

.perf-divider {
  width: 1px;
  height: 32px;
  background: rgba(255,255,255,0.08);
}

.perf-metric {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;

  &__label {
    font-size: 0.7rem;
    color: $text-muted;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  &__val {
    font-size: 1.2rem;
    font-weight: 700;
    color: $text-primary;
    font-family: 'IBM Plex Mono', monospace;

    &--sub {
      font-size: 0.95rem;
      color: $text-secondary;
    }
  }

  &__pnl {
    font-size: 1.25rem;
    font-weight: 700;
    font-family: 'IBM Plex Mono', monospace;
  }

  &__rate {
    font-size: 0.8rem;
    font-family: 'IBM Plex Mono', monospace;
  }
}

.perf-date {
  margin-left: auto;
  font-size: 0.72rem;
  color: $text-muted;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  align-self: flex-end;

  &__tip {
    cursor: help;
    vertical-align: middle;
  }
}

.perf-nodata {
  margin-left: auto;
  font-size: 0.78rem;
  color: #f59e0b;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

// PnL 颜色
.pnl-up   { color: #10b981; }  // 绿涨
.pnl-down { color: #f43f5e; }  // 红跌
.pnl-zero { color: $text-muted; }

.pnl-cell {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  align-items: flex-end;
}

.pnl-rate {
  font-size: 0.72rem;
}

.no-data-dash {
  color: $text-muted;
  font-size: 0.85rem;
}

// ---- 汇总卡片----
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.summary-card {
  background: #FFFFFF;
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  padding: 1rem 1.25rem;
}

.summary-label {
  font-size: 0.75rem;
  color: $text-muted;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: $text-primary;
  font-family: 'IBM Plex Mono', monospace;
}

.summary-markets {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-top: 0.25rem;
}

.market-tag {
  font-size: 0.7rem !important;
}

// ---- 持仓表格 ----
.holdings-table-wrap {
  background: #FFFFFF;
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  overflow: hidden;
}

.holdings-table {
  width: 100%;
  background: transparent !important;

  :deep(.el-table__header-wrapper th) {
    background: rgba(255,255,255,0.03) !important;
    color: $text-muted !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1px solid $border-subtle !important;
  }

  :deep(.el-table__row) {
    background: transparent !important;
    cursor: pointer;
    transition: background 0.2s;

    &:hover td {
      background: rgba(29, 78, 216, 0.04) !important;
    }
  }

  :deep(td) {
    border-bottom: 1px solid rgba(255,255,255,0.04) !important;
    color: $text-primary !important;
  }
}

.asset-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.asset-code {
  font-weight: 700;
  font-family: 'IBM Plex Mono', monospace;
  color: $primary-color;
  cursor: pointer;
  font-size: 0.9rem;

  &:hover {
    text-decoration: underline;
  }
}

.asset-name {
  font-size: 0.8125rem;
  color: $text-secondary;
}

.market-badge {
  font-size: 0.65rem !important;
  padding: 0 5px !important;
  height: 18px !important;
  line-height: 18px !important;
}

.mono-value {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.875rem;
}

.cost-value {
  color: $primary-color;
}

.notes-text {
  font-size: 0.8125rem;
  color: $text-muted;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  max-width: 150px;
}

.time-text {
  font-size: 0.75rem;
  color: $text-muted;
  font-family: 'IBM Plex Mono', monospace;
}

// ---- 对话框----
.holding-dialog {
  :deep(.el-dialog) {
    background: $bg-card !important;
    border: 1px solid $border-strong !important;
    border-radius: $border-radius-xl !important;
  }

  :deep(.el-dialog__title) {
    color: $text-primary !important;
    font-weight: 700 !important;
  }

  :deep(.el-form-item__label) {
    color: $text-secondary !important;
  }
}

.edit-asset-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid $border-subtle;
  border-radius: 8px;
}

.form-hint {
  font-size: 0.75rem;
  color: $text-muted;
  margin-top: 0.25rem;

  strong {
    color: $primary-color;
    font-family: 'IBM Plex Mono', monospace;
  }
}

.asset-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;

  .opt-code {
    font-weight: 700;
    font-family: 'IBM Plex Mono', monospace;
    min-width: 70px;
  }

  .opt-name {
    flex: 1;
    color: $text-secondary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .opt-market {
    font-size: 0.65rem !important;
    padding: 0 4px !important;
    height: 16px !important;
    line-height: 16px !important;
    flex-shrink: 0;
  }
}

.dialog-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

// ---- 累计收益曲线卡片 ----
.returns-chart-card {
  background: #FFFFFF;
  border: 1px solid $border-subtle;
  border-radius: $border-radius;
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.returns-chart-header {
  padding: 1rem 1.5rem 0.75rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.returns-chart-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.returns-chart-title {
  font-size: 0.9375rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0;
  letter-spacing: -0.01em;
}

.info-icon {
  color: $text-muted;
  font-size: 0.875rem;
  cursor: help;
}

.returns-chart-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.meta-item {
  font-size: 0.75rem;
  color: $text-muted;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.meta-label {
  color: $text-muted;
}

.meta-value {
  color: $text-secondary;
  &.mono { font-family: 'IBM Plex Mono', monospace; }
}

.meta-return {
  font-size: 0.8125rem;

  strong {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1rem;
  }
}

.returns-chart-body {
  padding: 0.5rem 0.5rem 0.25rem;
}

.returns-chart {
  width: 100%;
  height: 260px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>






