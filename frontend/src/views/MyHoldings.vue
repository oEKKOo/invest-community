<template>
  <div class="my-holdings">
    <div class="holdings-header">
      <div class="header-left">
        <h2 class="page-title">我的持仓</h2>
        <span class="subtitle">跟踪资产表现、成本结构与累计收益</span>
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
            <span class="meta-label">
              <span class="meta-value mono">{{ returnsHistory.items.length }}</span>
              个交易日
            </span>
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
        <el-table-column label="资产" min-width="160">
          <template #default="{ row }">
            <div class="asset-cell">
              <div class="asset-identity">
                <span class="asset-code" @click.stop="goToAsset(row.assetId)">{{ row.code }}</span>
                <span class="asset-name">{{ row.name }}</span>
              </div>
              <el-tag size="small" class="market-badge">{{ row.displayMarket }}</el-tag>
            </div>
          </template>
        </el-table-column>

        <!-- 类型 -->
        <el-table-column label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getAssetTypeTag(row.assetType)">
              {{ row.assetType }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 持有数量 -->
        <el-table-column label="数量（股）" width="100" align="right">
          <template #default="{ row }">
            <span class="mono-value">{{ formatNumber(row.quantity) }}</span>
          </template>
        </el-table-column>

        <!-- 成本均价 -->
        <el-table-column label="成本均价" width="105" align="right">
          <template #default="{ row }">
            <span class="mono-value">¥ {{ formatPrice(row.costPrice) }}</span>
          </template>
        </el-table-column>

        <!-- 持仓成本 -->
        <el-table-column label="持仓成本" width="115" align="right">
          <template #default="{ row }">
            <span class="mono-value cost-value">
              ¥ {{ formatCost(row.quantity, row.costPrice) }}
            </span>
          </template>
        </el-table-column>

        <!-- 今日估值价 -->
        <el-table-column label="今日估值价" width="105" align="right">
          <template #default="{ row }">
            <template v-if="getPerfItem(row.id)?.hasData">
              <span class="mono-value">¥ {{ formatPrice(getPerfItem(row.id)?.todayPrice) }}</span>
            </template>
            <span v-else class="no-data-dash">--</span>
          </template>
        </el-table-column>

        <!-- 市值-->
        <el-table-column label="市值" width="95" align="right">
          <template #default="{ row }">
            <template v-if="getPerfItem(row.id)?.hasData">
              <span class="mono-value">{{ formatMoneyShort(getPerfItem(row.id)?.marketValue) }}</span>
            </template>
            <span v-else class="no-data-dash">--</span>
          </template>
        </el-table-column>

        <!-- 当日收益 -->
        <el-table-column label="当日收益" width="115" align="right">
          <template #default="{ row }">
            <template v-if="getPerfItem(row.id)?.hasData">
              <div class="pnl-cell pnl-cell--daily" :class="pnlClass(getPerfItem(row.id)?.dailyPnl)">
                <span class="pnl-amount">{{ formatPnl(getPerfItem(row.id)?.dailyPnl) }}</span>
                <span class="pnl-rate">{{ formatRate(getPerfItem(row.id)?.dailyReturn) }}</span>
              </div>
            </template>
            <span v-else class="no-data-dash">--</span>
          </template>
        </el-table-column>

        <!-- 持有收益（浮盈） -->
        <el-table-column label="持有收益" width="125" align="right">
          <template #default="{ row }">
            <template v-if="getPerfItem(row.id)?.hasData">
              <div class="pnl-cell pnl-cell--unrealized" :class="pnlClass(getPerfItem(row.id)?.unrealizedPnl)">
                <span class="pnl-amount">{{ formatPnl(getPerfItem(row.id)?.unrealizedPnl) }}</span>
                <span class="pnl-rate">{{ formatRate(getPerfItem(row.id)?.unrealizedReturn) }}</span>
              </div>
            </template>
            <span v-else class="no-data-dash">--</span>
          </template>
        </el-table-column>

        <!-- 备注 -->
        <el-table-column label="备注" min-width="120">
          <template #default="{ row }">
            <span class="notes-text" :title="row.notes">{{ row.notes || '--' }}</span>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
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
            </div>
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
            class="holding-input-number"
          />
          <div class="cost-summary" v-if="holdingForm.quantity > 0 && holdingForm.costPrice > 0">
            <span class="cost-summary-label">预计持仓成本</span>
            <span class="cost-summary-value">¥ {{ formatCost(holdingForm.quantity, holdingForm.costPrice) }}</span>
          </div>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="holdingForm.notes"
            type="textarea"
            :rows="2"
            placeholder="记录买入逻辑、仓位规划或策略备注…"
            class="holding-textarea"
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
import { createLazyChartComponent, loadHoldingsChartComponent } from '@/utils/chart-loader'

const VChart = createLazyChartComponent(loadHoldingsChartComponent)

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

  // 找最新值的颜色（低饱和度）
  const lastReturn = Number(returnRates[returnRates.length - 1])
  const lineColor = lastReturn >= 0 ? '#16a34a' : '#dc2626'

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
        const pnlColor = pnl >= 0 ? '#16a34a' : '#dc2626'
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
      axisLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.08)' } },
      axisLabel: {
        color: '#8e8e93',
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
        color: '#8e8e93',
        fontSize: 11,
        fontFamily: 'IBM Plex Mono',
        formatter: (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`,
      },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.04)' } },
    },
    series: [
      {
        name: '累计收益',
        type: 'line',
        data: returnRates.map(Number),
        smooth: true,
        symbol: 'none',
        lineStyle: { color: lineColor, width: 2.5 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: lastReturn >= 0 ? 'rgba(22,163,74,0.15)' : 'rgba(220,38,38,0.15)' },
              { offset: 1, color: 'rgba(0,0,0,0)' },
            ]
          }
        },
        markLine: {
          silent: true,
          symbol: ['none', 'none'],
          lineStyle: { color: 'rgba(0, 0, 0, 0.12)', type: 'dashed', width: 1 },
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
  padding: 0 1rem;
  animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  background: $apple-bg-page;
  min-height: 100vh;
}

.holdings-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $apple-space-6;

  @media (max-width: 640px) {
    flex-direction: column;
    gap: $apple-space-4;
  }
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.page-title {
  font-size: $apple-font-h2; // 32px
  font-weight: 700;
  color: $apple-text-primary;
  margin: 0;
  letter-spacing: -0.025em;
  font-family: $apple-font-family;
}

.subtitle {
  font-size: $apple-font-caption; // 13px
  color: $apple-text-secondary;
  font-family: $apple-font-family;
}

.add-btn {
  background: $gradient-primary !important;
  border: none !important;
  box-shadow: $apple-shadow-md !important;
  font-weight: 600 !important;
  border-radius: $apple-radius-sm !important; // 10px
  font-family: $apple-font-family !important;
  transition: $transition-all !important;

  &:hover {
    box-shadow: 0 10px 30px rgba(29, 78, 216, 0.25) !important;
    transform: translateY(-1px);
  }
}

// ---- 收益 Banner (Hero Summary) ----
.perf-banner {
  position: relative;
  background: linear-gradient(135deg, rgba(255,255,255,0.85), rgba(245,250,255,0.92));
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: $apple-radius-xl; // 28px
  padding: $apple-space-8; // 32px
  margin-bottom: $apple-space-6;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $apple-space-6;
  align-items: start;
  box-shadow: $apple-shadow-md;
  min-height: 120px;

  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
    gap: $apple-space-4;
  }
}

.perf-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0; // 防止flex子项溢出

  &--main {
    grid-column: span 2;
    
    @media (max-width: 1024px) {
      grid-column: span 2;
    }
    
    @media (max-width: 640px) {
      grid-column: span 1;
    }
    
    flex-direction: row;
    align-items: center; // 改为center，确保垂直居中
    gap: $apple-space-6;
    flex-wrap: nowrap; // 防止换行
  }
}

.perf-sep {
  display: none; // 移除分隔线，使用grid gap
}

.perf-divider {
  width: 1px;
  height: 48px;
  background: rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
  align-self: center; // 确保分隔线垂直居中
}

.perf-metric {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  min-width: 0; // 防止内容溢出
  flex: 0 0 auto; // 防止被压缩

  &__label {
    font-size: $apple-font-mini; // 12px
    color: $apple-text-tertiary;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-family: $apple-font-family;
    white-space: nowrap; // 防止标签换行
  }

  &__val {
    font-size: 1.75rem; // 主焦点：总市值
    font-weight: 700;
    color: $apple-text-primary;
    line-height: 1.2;
    white-space: nowrap; // 防止数字换行
    word-break: keep-all; // 保持数字完整

    &--sub {
      font-size: 1.1rem; // 第二层：持仓成本
      color: $apple-text-secondary;
      font-weight: 600;
      white-space: nowrap;
    }
  }

  &__pnl {
    font-size: 1.5rem; // 主焦点：持有收益
    font-weight: 700;
    line-height: 1.2;
    white-space: nowrap; // 防止收益数字换行
  }

  &__rate {
    font-size: 0.875rem; // 第二层：今日收益
    font-weight: 500;
    white-space: nowrap;
  }
}

.perf-date {
  grid-column: span 4;
  justify-self: flex-end;
  font-size: $apple-font-mini;
  color: $apple-text-tertiary;
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin-top: $apple-space-2;
  font-family: $apple-font-family;

  @media (max-width: 1024px) {
    grid-column: span 2;
  }

  @media (max-width: 640px) {
    grid-column: span 1;
  }

  &__tip {
    cursor: help;
    vertical-align: middle;
  }
}

.perf-nodata {
  grid-column: span 4;
  justify-self: flex-end;
  font-size: $apple-font-caption;
  color: $warning-color;
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin-top: $apple-space-2;
  font-family: $apple-font-family;

  @media (max-width: 1024px) {
    grid-column: span 2;
  }

  @media (max-width: 640px) {
    grid-column: span 1;
  }
}

// PnL 颜色（低饱和度）
.pnl-up   { color: #16a34a; }  // 低饱和绿色
.pnl-down { color: #dc2626; }  // 低饱和红色
.pnl-zero { color: $apple-text-tertiary; }

.pnl-cell {
  display: flex;
  flex-direction: column;
  gap: 0.15rem; // 减小间距
  align-items: flex-end;
  line-height: 1.2;

  &--daily {
    // 当日收益：轻量显示
    .pnl-amount {
      font-size: 12px; // 从13px减小到12px
      font-weight: 500;
    }
    .pnl-rate {
      font-size: 10px; // 从11px减小到10px
      opacity: 0.75;
    }
  }

  &--unrealized {
    // 持有收益：更重要
    .pnl-amount {
      font-size: 13px; // 从14px减小到13px
      font-weight: 600;
    }
    .pnl-rate {
      font-size: 11px; // 从12px减小到11px
    }
  }
}

.pnl-amount {
  line-height: 1.3;
}

.pnl-rate {
  line-height: 1.3;
}

.no-data-dash {
  color: $apple-text-tertiary;
  font-size: 12px; // 减小字体
}

// ---- 汇总卡片 (Quick Stats) ----
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: $apple-space-4;
  margin-bottom: $apple-space-6;
}

.summary-card {
  background: $apple-bg-elevated; // rgba(255, 255, 255, 0.78)
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: $apple-radius-lg; // 20px
  padding: $apple-space-5 $apple-space-6; // 20px 24px
  box-shadow: $apple-shadow-sm;
  transition: $transition-all;

  &:hover {
    box-shadow: $apple-shadow-md;
    transform: translateY(-2px);
  }
}

.summary-label {
  font-size: $apple-font-mini; // 12px
  color: $apple-text-tertiary;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: $apple-space-3;
  font-family: $apple-font-family;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: $apple-text-primary;
  line-height: 1.2;
}

.summary-markets {
  display: flex;
  flex-wrap: wrap;
  gap: $apple-space-2;
  margin-top: $apple-space-2;
}

.market-tag {
  font-size: $apple-font-mini !important;
  border-radius: $apple-radius-sm !important;
}

// ---- 持仓表格 ----
.holdings-table-wrap {
  background: $apple-bg-elevated;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: $apple-radius-lg; // 20px
  overflow: hidden;
  box-shadow: $apple-shadow-sm;
}

.holdings-table {
  width: 100%;
  background: transparent !important;

  :deep(.el-table__header-wrapper th) {
    background: rgba(0, 0, 0, 0.02) !important;
    color: $apple-text-tertiary !important;
    font-size: $apple-font-mini !important; // 12px
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
    font-family: $apple-font-family !important;
    padding: 12px 10px !important; // 减小padding，避免列太宽
    white-space: nowrap !important;
  }

  :deep(.el-table__row) {
    background: transparent !important;
    cursor: pointer;
    transition: background 0.2s ease;

    &:hover td {
      background: rgba(0, 113, 227, 0.04) !important;
    }
  }

  :deep(td) {
    border-bottom: 1px solid rgba(0, 0, 0, 0.04) !important;
    color: $apple-text-primary !important;
    padding: 14px 10px !important; // 减小padding，增加列间距
    vertical-align: middle !important; // 确保单元格内容垂直居中
  }
  
  // 确保表格单元格内容不换行（除非明确需要）
  :deep(.el-table__cell) {
    word-break: keep-all;
    overflow-wrap: break-word;
    overflow: hidden; // 防止内容溢出
  }
  
  // 固定列样式优化
  :deep(.el-table__fixed-right) {
    box-shadow: -2px 0 8px rgba(0, 0, 0, 0.04) !important;
  }
}

.asset-cell {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-start;
  min-width: 0; // 防止内容溢出
}

.asset-identity {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  width: 100%;
  min-width: 0;
}

.asset-code {
  font-weight: 700;
  color: $apple-accent;
  cursor: pointer;
  font-size: 13px; // 减小字体
  line-height: 1.3;
  white-space: nowrap; // 防止代码换行
  display: inline-block;

  &:hover {
    text-decoration: underline;
    color: $primary-dark;
  }
}

.asset-name {
  font-size: 12px; // 减小字体，从13px改为12px
  color: $apple-text-secondary;
  line-height: 1.3;
  white-space: nowrap; // 防止名称换行
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  display: block;
}

.market-badge {
  font-size: $apple-font-mini !important; // 12px
  padding: 2px 6px !important;
  height: 20px !important;
  line-height: 20px !important;
  border-radius: $apple-radius-sm !important;
  flex-shrink: 0; // 防止标签被压缩
  white-space: nowrap; // 防止标签文字换行
  display: inline-flex !important;
  align-items: center !important;
}

.mono-value {
  font-size: 14px; // 减小字体，从16px改为14px
  white-space: nowrap; // 防止数字换行
  display: inline-block;
}

.cost-value {
  color: $apple-accent;
  font-weight: 600;
}

.notes-text {
  font-size: 12px; // 减小字体
  color: $apple-text-tertiary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  max-width: 120px; // 减小最大宽度
}

// 操作按钮组
.action-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px; // 横向排列，间距8px
  flex-wrap: nowrap; // 防止换行
  
  :deep(.el-button) {
    padding: 4px 8px !important; // 减小按钮padding
    font-size: 12px !important; // 减小按钮字体
    min-height: 24px !important; // 减小按钮高度
    margin: 0 !important;
  }
}

.time-text {
  font-size: $apple-font-mini;
  color: $apple-text-tertiary;
}

// ---- 对话框----
.holding-dialog {
  :deep(.el-dialog) {
    background: $apple-bg-elevated !important;
    border: 1px solid rgba(0, 0, 0, 0.06) !important;
    border-radius: $apple-radius-xl !important; // 28px
    box-shadow: $apple-shadow-lg !important;
  }

  :deep(.el-dialog__header) {
    padding: $apple-space-6 $apple-space-8 $apple-space-4 !important;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
  }

  :deep(.el-dialog__title) {
    color: $apple-text-primary !important;
    font-weight: 700 !important;
    font-size: $apple-font-h3 !important; // 20px
    font-family: $apple-font-family !important;
  }

  :deep(.el-dialog__body) {
    padding: $apple-space-6 $apple-space-8 !important;
  }

  :deep(.el-form-item__label) {
    color: $apple-text-secondary !important;
    font-family: $apple-font-family !important;
  }

  // 输入框统一样式
  :deep(.el-input__wrapper) {
    border-radius: $apple-radius-segmented !important; // 14px
    background: $apple-input-bg !important;
    border: 1px solid $apple-input-border !important;
    box-shadow: none !important;
    min-height: $apple-input-height !important; // 48px
  }

  :deep(.el-input__inner) {
    font-family: $apple-font-family !important;
  }

  :deep(.el-textarea__inner) {
    border-radius: $apple-radius-segmented !important; // 14px
    background: $apple-input-bg !important;
    border: 1px solid $apple-input-border !important;
    font-family: $apple-font-family !important;
  }

  :deep(.el-input-number) {
    width: 100%;

    .el-input__wrapper {
      width: 100%;
    }
  }

  :deep(.el-select) {
    .el-input__wrapper {
      border-radius: $apple-radius-segmented !important;
      background: $apple-input-bg !important;
      border: 1px solid $apple-input-border !important;
      min-height: $apple-input-height !important;
    }
  }
}

.edit-asset-info {
  display: flex;
  align-items: center;
  gap: $apple-space-2;
  padding: $apple-space-3 $apple-space-4;
  background: rgba(245, 245, 247, 0.6);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: $apple-radius-sm;
}

.cost-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: $apple-space-3;
  padding: $apple-space-3 $apple-space-4;
  background: rgba(0, 113, 227, 0.05);
  border: 1px solid rgba(0, 113, 227, 0.1);
  border-radius: 12px;

  &-label {
    font-size: $apple-font-caption;
    color: $apple-text-secondary;
    font-family: $apple-font-family;
  }

  &-value {
    font-size: $apple-font-body;
    font-weight: 600;
    color: $apple-accent;
  }
}

.form-hint {
  font-size: $apple-font-mini;
  color: $apple-text-tertiary;
  margin-top: $apple-space-2;
  font-family: $apple-font-family;
}

.asset-option {
  display: flex;
  align-items: center;
  gap: $apple-space-2;
  font-size: $apple-font-caption;
  font-family: $apple-font-family;

  .opt-code {
    font-weight: 700;
    min-width: 70px;
  }

  .opt-name {
    flex: 1;
    color: $apple-text-secondary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .opt-market {
    font-size: $apple-font-mini !important;
    padding: 2px 4px !important;
    height: 18px !important;
    line-height: 18px !important;
    flex-shrink: 0;
    border-radius: $apple-radius-sm !important;
  }
}

.dialog-footer {
  display: flex;
  gap: $apple-space-3;
  justify-content: flex-end;
  padding: $apple-space-4 $apple-space-8 $apple-space-6 !important;

  :deep(.el-button) {
    border-radius: 12px !important;
    font-family: $apple-font-family !important;
    
    &.el-button--default {
      color: $apple-text-secondary !important;
    }
  }
}

// ---- 累计收益曲线卡片 (Performance Chart) ----
.returns-chart-card {
  background: $apple-bg-elevated;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: $apple-radius-lg; // 24px
  margin-bottom: $apple-space-6;
  overflow: hidden;
  box-shadow: $apple-shadow-md;
}

.returns-chart-header {
  padding: $apple-space-6 $apple-space-8 $apple-space-4; // 24px 28px 16px
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.returns-chart-title-row {
  display: flex;
  align-items: center;
  gap: $apple-space-2;
  margin-bottom: $apple-space-4;
}

.returns-chart-title {
  font-size: $apple-font-h2; // 24px
  font-weight: 700;
  color: $apple-text-primary;
  margin: 0;
  letter-spacing: -0.01em;
  font-family: $apple-font-family;
}

.info-icon {
  color: $apple-text-tertiary;
  font-size: $apple-font-body;
  cursor: help;
}

.returns-chart-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: $apple-space-5;
}

.meta-item {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  display: flex;
  align-items: center;
  gap: $apple-space-2;
  font-family: $apple-font-family;
}

.meta-label {
  color: $apple-text-tertiary;
}

.meta-value {
  color: $apple-text-secondary;
  &.mono {
  }
}

.meta-return {
  font-size: $apple-font-body;
  font-weight: 600;
  font-family: $apple-font-family;

  strong {
    font-size: 1.25rem; // 突出显示最新收益率
    font-weight: 700;
  }
}

.returns-chart-body {
  padding: $apple-space-4 $apple-space-5 $apple-space-3;
}

.returns-chart {
  width: 100%;
  height: 280px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

// 统一字体系统
* {
  font-family: $apple-font-family;
}

// 确保本页中所有数字相关展示统一使用等宽字体
.mono-value,
.perf-metric__val,
.perf-metric__pnl,
.perf-metric__rate,
.summary-value,
.asset-code,
.pnl-amount,
.pnl-rate,
.cost-summary-value,
.meta-value,
.time-text,
.no-data-dash,
.meta-return strong,
.asset-option .opt-code {
  font-family: 'IBM Plex Mono', monospace;
}
</style>






