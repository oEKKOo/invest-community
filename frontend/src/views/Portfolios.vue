<template>
  <div class="portfolios">
    <div class="portfolios-header">
      <div class="header-content">
        <div class="header-text">
          <h2 class="page-title">投资组合</h2>
          <p class="page-subtitle">探索社区中的策略组合与资产配置思路</p>
        </div>
        <el-button 
          type="primary" 
          size="large"
          @click="showCreatePortfolio = true"
          :icon="Plus"
          class="create-btn"
        >
          创建我的组合
        </el-button>
      </div>
      <div class="filter-tabs">
        <button
          v-for="filter in filterOptions"
          :key="filter.value"
          type="button"
          class="filter-tab"
          :class="{ active: currentFilter === filter.value }"
          @click="handleFilterChange(filter.value)"
        >
          {{ filter.label }}
        </button>
      </div>
    </div>

    <!-- 创建组合对话框-->
    <el-dialog
      v-model="showCreatePortfolio"
      title="构建投资策略"
      width="700px"
      class="create-portfolio-dialog"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="80px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="组合名称" prop="title">
              <el-input
                v-model="createForm.title"
                placeholder="给你的组合起个名字"
              />
            </el-form-item>

            <el-form-item label="组合描述" prop="description">
              <el-input
                v-model="createForm.description"
                type="textarea"
                :rows="3"
                placeholder="描述你的投资策略..."
              />
            </el-form-item>

            <el-form-item label="策略说明" prop="strategyNote">
              <el-input
                v-model="createForm.strategyNote"
                type="textarea"
                :rows="3"
                placeholder="可填写核心逻辑、择时思路、风险控制要点"
              />
            </el-form-item>

            <el-form-item label="风险等级" prop="riskLevel">
              <el-select v-model="createForm.riskLevel" placeholder="选择风险等级">
                <el-option label="低风险" value="Low" />
                <el-option label="中等风险" value="Medium" />
                <el-option label="高风险" value="High" />
              </el-select>
            </el-form-item>

            <el-form-item label="是否公开">
              <el-switch
                v-model="createForm.isPublic"
                active-text="公开"
                inactive-text="私有"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <div class="assets-section">
              <div class="assets-header">
                <h4 class="assets-title">资产配置</h4>
                <div class="add-mode-tabs">
                  <button
                    type="button"
                    class="mode-tab"
                    :class="{ active: addMode === 'manual' }"
                    @click="addMode = 'manual'"
                  >手动添加</button>
                  <button
                    type="button"
                    class="mode-tab"
                    :class="{ active: addMode === 'import' }"
                    @click="switchToImport"
                  >从持仓导入</button>
                </div>
              </div>

              <!-- 手动添加模式 -->
              <template v-if="addMode === 'manual'">
                <div class="add-asset">
                  <el-select
                    v-model="assetForm.selectedAsset"
                    filterable
                    remote
                    clearable
                    placeholder="搜索股票/基金/ETF"
                    :remote-method="searchAssets"
                    :loading="assetSearchLoading"
                    size="small"
                    style="flex: 1; min-width: 0"
                    value-key="id"
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
                  <el-input-number
                    v-model="assetForm.amount"
                    placeholder="金额"
                    size="small"
                    style="width: 100px"
                    :min="0.01"
                    :precision="2"
                    controls-position="right"
                  />
                  <el-button
                    size="small"
                    type="primary"
                    @click="addAsset"
                    :disabled="!canAddAsset"
                  >
                    添加
                  </el-button>
                </div>
                <p class="mode-hint">输入持仓金额，占比将自动计算</p>
              </template>

              <!-- 从持仓导入模式-->
              <template v-else>
                <div v-if="holdingsLoading" class="holdings-loading">
                  <el-skeleton :rows="3" animated />
                </div>
                <div v-else-if="myHoldings.length === 0" class="holdings-empty">
                  <el-icon><InfoFilled /></el-icon>
                  <span>暂无持仓记录</span>
                </div>
                <template v-else>
                  <div class="import-toolbar">
                    <el-checkbox
                      :model-value="isAllSelected"
                      :indeterminate="isIndeterminate"
                      @change="toggleSelectAll"
                    >全选</el-checkbox>
                    <el-button
                      size="small"
                      type="primary"
                      :disabled="selectedHoldingIds.size === 0"
                      @click="importSelectedHoldings"
                    >
                      导入选中 ({{ selectedHoldingIds.size }})
                    </el-button>
                  </div>
                  <div class="holdings-import-list">
                    <div
                      v-for="h in myHoldings"
                      :key="h.id"
                      class="holding-import-row"
                      :class="{ selected: selectedHoldingIds.has(h.id), already: isAlreadyAdded(h) }"
                      @click="!isAlreadyAdded(h) && toggleHolding(h.id)"
                    >
                      <el-checkbox
                        :model-value="selectedHoldingIds.has(h.id)"
                        :disabled="isAlreadyAdded(h)"
                        @change="toggleHolding(h.id)"
                        @click.stop
                      />
                      <span class="h-code">{{ h.code }}</span>
                      <span class="h-name">{{ h.name }}</span>
                      <el-tag size="small" class="opt-market">{{ h.displayMarket || h.market }}</el-tag>
                      <span class="h-amount">¥{{ formatAmount(Number(h.quantity) * Number(h.costPrice)) }}</span>
                      <span v-if="isAlreadyAdded(h)" class="h-added-badge">已添加</span>
                    </div>
                  </div>
                </template>
              </template>

              <!-- 已配置资产列表（两种模式共享）-->
              <div class="assets-list" v-if="createForm.assets.length > 0">
                <div 
                  v-for="(asset, index) in createForm.assets"
                  :key="index"
                  class="asset-item"
                >
                  <div class="asset-info">
                    <span class="asset-symbol">{{ asset.symbol }}</span>
                    <span class="asset-name-small">{{ asset.name }}</span>
                    <el-tag v-if="asset.displayMarket" size="small" class="asset-market-tag">
                      {{ asset.displayMarket }}
                    </el-tag>
                  </div>
                  <div class="asset-right">
                    <span class="asset-amount-small">¥{{ formatAmount(asset.amount) }}</span>
                    <span class="asset-allocation">{{ getAssetAllocation(asset.amount).toFixed(1) }}%</span>
                  </div>
                  <el-button
                    size="small"
                    type="text"
                    @click="removeAsset(index)"
                    class="remove-btn"
                  >
                    删除
                  </el-button>
                </div>
              </div>

              <div class="allocation-summary">
                <span>总金额： ¥{{ formatAmount(totalAmount) }}</span>
                <span class="alloc-pct" :class="{ 'alloc-ok': createForm.assets.length > 0 }">
                  占比合计: {{ createForm.assets.length > 0 ? '100.0' : '0.0' }}%
                </span>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreatePortfolio = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleCreatePortfolio" 
            :loading="creating"
            :disabled="createForm.assets.length === 0"
          >
            发布组合
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 组合列表 -->
    <div class="portfolios-grid">
      <div v-if="portfoliosStore.loading" class="loading-grid">
        <div v-for="i in 6" :key="i" class="portfolio-skeleton">
          <el-skeleton :rows="4" animated />
        </div>
      </div>

      <div v-else-if="portfoliosStore.portfolios.length === 0" class="empty-state">
        <el-empty 
          description="暂无投资组合"
          :image-size="120"
        >
          <el-button type="primary" @click="showCreatePortfolio = true">
            创建第一个组合
          </el-button>
        </el-empty>
      </div>

      <div
        v-else
        v-for="portfolio in portfoliosStore.portfolios"
        :key="portfolio.id"
        class="portfolio-card"
        @click="$router.push(`/portfolios/${portfolio.id}`)"
      >
        <!-- 第一层：组合名称 + 风险标签 -->
        <div class="portfolio-header">
          <h3 class="portfolio-title">{{ portfolio.title }}</h3>
          <span
            class="risk-pill"
            :class="`risk-pill--${portfolio.riskLevel.toLowerCase()}`"
          >
            {{ portfolio.riskLevel === 'Low' ? '低风险' : portfolio.riskLevel === 'Medium' ? '中等风险' : '高风险' }}
          </span>
        </div>

        <p v-if="portfolio.description" class="portfolio-summary">
          {{ portfolio.description }}
        </p>

        <!-- 第二层：收益表现（前置并突出） -->
        <div class="portfolio-return-section">
          <div class="return-value" :class="pnlClass(getDisplayTotalReturn(portfolio))">
            {{ fmtRate(getDisplayTotalReturn(portfolio)) || '--' }}
          </div>
          <div class="return-label">总收益率</div>
          <div class="return-stats">
            <div class="return-stat">
              <span class="return-stat-label">今日</span>
              <span class="return-stat-value" :class="pnlClass(portfolio.dailyReturn)">{{ fmtRate(portfolio.dailyReturn) || '—' }}</span>
            </div>
            <div class="return-stat">
              <span class="return-stat-label">7 日</span>
              <span class="return-stat-value" :class="pnlClass(portfolio.sevenDayReturn)">{{ fmtRate(portfolio.sevenDayReturn) || '—' }}</span>
            </div>
          </div>
        </div>

        <!-- 第三层：配置可视化 -->
        <div class="chart-section">
          <div class="chart-container">
            <v-chart 
              class="pie-chart" 
              :option="getPieChartOption(portfolio.assets)"
              v-if="portfolio.assets?.length"
              autoresize
            />
          </div>
          <div class="chart-meta">
            <span class="meta-chip">{{ (portfolio.assetCount ?? portfolio.assets?.length) || 0 }} 只标的</span>
            <span class="meta-chip" v-if="portfolio.assets?.[0]">
              主要 {{ portfolio.assets[0].symbol }}
            </span>
            <span class="meta-chip" v-if="portfolio.isPublic">公开</span>
            <span class="meta-chip">更新 {{ formatDate(portfolio.updatedAt || portfolio.createdAt) }}</span>
          </div>
        </div>

        <!-- 第四层：创建者信息（轻量展示） -->
        <div class="portfolio-footer">
          <div class="portfolio-author">
            <el-avatar
              :size="28"
              :src="getAvatarUrl(portfolio.id)"
              class="author-clickable"
              @click.stop="$router.push({ name: 'UserProfile', params: { userId: portfolio.userId } })"
            >
              {{ portfolio.userName[0] }}
            </el-avatar>
            <span
              class="author-name author-clickable"
              @click.stop="$router.push({ name: 'UserProfile', params: { userId: portfolio.userId } })"
            >
              {{ portfolio.userName }}
            </span>
          </div>
          <div class="portfolio-actions">
            <el-button
              type="text"
              :class="{ liked: portfolio.isLiked }"
              @click.stop="handleLike(portfolio.id)"
              class="like-btn"
            >
              <el-icon><Star /></el-icon>
              <span>{{ portfolio.likes }}</span>
            </el-button>
            <el-button
              type="text"
              :class="{ liked: portfolio.isFavorited }"
              @click.stop="handleFavorite(portfolio.id)"
              class="like-btn"
            >
              <el-icon><StarFilled /></el-icon>
              <span>{{ portfolio.favorites || 0 }}</span>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="portfoliosStore.portfolios.length > 0">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :total="portfoliosStore.pagination.total"
        layout="prev, pager, next, total"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted, computed } from 'vue'
import { usePortfoliosStore } from '../stores/portfolios'
import { useAuthStore } from '../stores/auth'
import type { PortfolioAsset, UserHolding } from '../types'
import type { AssetWithQuote } from '../api/market'
import { getAssetsWithQuote } from '../api/market'
import { getMyHoldings, getHoldingPerformance } from '../api/holdings'
import type { HoldingPerformance, HoldingPerformanceItem } from '../types'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createLazyChartComponent, loadPortfoliosChartComponent } from '@/utils/chart-loader'
import {
  Plus,
  Star,
  StarFilled,
  InfoFilled
} from '@element-plus/icons-vue'

const VChart = createLazyChartComponent(loadPortfoliosChartComponent)

// 扩展资产类型，包含持仓金额字段
interface FormAsset extends PortfolioAsset {
  amount: number  // 持仓金额（用于自动计算占比）
}

const portfoliosStore = usePortfoliosStore()
const authStore = useAuthStore()

// 状态
const showCreatePortfolio = ref(false)
const creating = ref(false)
const currentPage = ref(1)
const pageSize = ref(12)
const currentFilter = ref<string>('all')

// 筛选选项
const filterOptions = [
  { label: '全部', value: 'all' },
  { label: '稳健', value: 'Low' },
  { label: '均衡', value: 'Medium' },
  { label: '激进', value: 'High' },
  { label: '热门', value: 'hot' }
]

// 添加模式：manual 手动 | import 从持仓导入
const addMode = ref<'manual' | 'import'>('manual')

// 资产搜索状态
const assetSearchLoading = ref(false)
const assetSearchResults = ref<AssetWithQuote[]>([])

// 持仓导入状态
const holdingsLoading = ref(false)
const myHoldings = ref<UserHolding[]>([])
const selectedHoldingIds = ref<Set<number>>(new Set())

// 持仓收益数据（用于显示实际收益）
const holdingPerf = ref<HoldingPerformance | null>(null)
const holdingPerfMap = ref<Map<number, HoldingPerformanceItem>>(new Map())

// 表单
const createFormRef = ref<FormInstance>()
const createForm = ref({
  title: '',
  description: '',
  strategyNote: '',
  riskLevel: 'Medium' as 'Low' | 'Medium' | 'High',
  isPublic: true,
  assets: [] as FormAsset[]
})

const assetForm = ref({
  selectedAsset: null as AssetWithQuote | null,
  amount: 0  // 持仓金额（元），用于自动计算占比
})

const createRules: FormRules = {
  title: [
    { required: true, message: '请输入组合名称', trigger: 'blur' },
    { min: 2, max: 50, message: '组合名称长度应在2-50字符之间', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过200字符', trigger: 'blur' }
  ],
  strategyNote: [
    { max: 2000, message: '策略说明不能超过2000字符', trigger: 'blur' }
  ],
  riskLevel: [
    { required: true, message: '请选择风险等级', trigger: 'change' }
  ]
}

/** 组合卡片饼图：蓝系为主、克制统一（与 variables $portfolio-chart-colors 对齐） */
const PIE_PALETTE = ['#2563eb', '#3b82f6', '#60a5fa', '#38bdf8', '#94a3b8']

interface PieSliceItem {
  value: number
  name: string
}

/** 取前若干大项，其余合并为「其他」，避免扇区与图例过多 */
const buildPieSliceData = (assets: PortfolioAsset[]): PieSliceItem[] => {
  if (!assets?.length) return []
  const sorted = [...assets].sort(
    (a, b) => (Number(b.allocation) || 0) - (Number(a.allocation) || 0)
  )
  const maxSlices = 4
  if (sorted.length <= maxSlices) {
    return sorted.map((a) => ({
      value: Number(a.allocation) || 0,
      name: (a.symbol || a.name || '—').slice(0, 14)
    }))
  }
  const head = sorted.slice(0, maxSlices - 1)
  const tail = sorted.slice(maxSlices - 1)
  const otherVal = tail.reduce((s, a) => s + (Number(a.allocation) || 0), 0)
  return [
    ...head.map((a) => ({
      value: Number(a.allocation) || 0,
      name: (a.symbol || a.name || '—').slice(0, 14)
    })),
    { value: otherVal, name: '其他' }
  ]
}

// ============ 计算属性============

// 所有资产的总持仓金额
const totalAmount = computed(() => {
  return createForm.value.assets.reduce((sum, a) => sum + (Number(a.amount) || 0), 0)
})

// 根据金额计算单个资产的占比（%）
const getAssetAllocation = (amount: number): number => {
  if (totalAmount.value === 0) return 0
  return (amount / totalAmount.value) * 100
}

// 手动添加时：是否可添加
const canAddAsset = computed(() => {
  return assetForm.value.selectedAsset !== null &&
         assetForm.value.amount > 0 &&
         !createForm.value.assets.some(a => a.assetId === assetForm.value.selectedAsset?.id)
})

// 全选状态
const selectableHoldings = computed(() =>
  myHoldings.value.filter(h => !isAlreadyAdded(h))
)
const isAllSelected = computed(() =>
  selectableHoldings.value.length > 0 &&
  selectableHoldings.value.every(h => selectedHoldingIds.value.has(h.id))
)
const isIndeterminate = computed(() =>
  selectableHoldings.value.some(h => selectedHoldingIds.value.has(h.id)) && !isAllSelected.value
)

// ============ 格式化============
const formatAmount = (val: number): string => {
  if (val >= 1_0000_0000) return `${(val / 1_0000_0000).toFixed(2)}亿`
  if (val >= 10_000) return `${(val / 10_000).toFixed(2)}万`
  return val.toFixed(2)
}

const fmtRate = (val: string | number | null | undefined): string => {
  if (val === null || val === undefined) return ''
  const n = Number(val)
  if (isNaN(n)) return ''
  return `${n >= 0 ? '+' : ''}${(n * 100).toFixed(2)}%`
}

const pnlClass = (val: string | number | null | undefined): string => {
  if (val === null || val === undefined) return ''
  const n = Number(val)
  if (isNaN(n) || n === 0) return 'pnl-zero'
  return n > 0 ? 'pnl-up' : 'pnl-down'
}

// ============ 资产搜索（手动模式） ============
const searchAssets = async (query: string) => {
  if (!query || query.length < 1) {
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
  assetForm.value.selectedAsset = asset
}

// ============ 持仓导入模式 ============
const switchToImport = async () => {
  addMode.value = 'import'
  if (myHoldings.value.length === 0) {
    holdingsLoading.value = true
    try {
      const res = await getMyHoldings()
      myHoldings.value = res.items || []
    } catch {
      ElMessage.error('获取持仓数据失败')
    } finally {
      holdingsLoading.value = false
    }
  }
}

const isAlreadyAdded = (h: UserHolding): boolean => {
  return createForm.value.assets.some(a => a.assetId === h.assetId)
}

const toggleHolding = (id: number) => {
  const set = new Set(selectedHoldingIds.value)
  if (set.has(id)) {
    set.delete(id)
  } else {
    set.add(id)
  }
  selectedHoldingIds.value = set
}

const toggleSelectAll = (val: boolean) => {
  if (val) {
    const set = new Set(selectedHoldingIds.value)
    selectableHoldings.value.forEach(h => set.add(h.id))
    selectedHoldingIds.value = set
  } else {
    const set = new Set(selectedHoldingIds.value)
    selectableHoldings.value.forEach(h => set.delete(h.id))
    selectedHoldingIds.value = set
  }
}

const importSelectedHoldings = () => {
  if (selectedHoldingIds.value.size === 0) return
  let importCount = 0
  myHoldings.value.forEach(h => {
    if (!selectedHoldingIds.value.has(h.id)) return
    if (isAlreadyAdded(h)) return
    const amount = Number(h.quantity) * Number(h.costPrice)
    createForm.value.assets.push({
      assetId: h.assetId,
      symbol: h.code,
      name: h.name,
      market: h.market || '',
      displayMarket: h.displayMarket || h.market || '',
      allocation: 0,  // 占比（getAssetAllocation 动态计算）
      amount
    })
    importCount++
  })
    // 清除已导入的勾选项
  const remaining = new Set<number>()
  selectedHoldingIds.value.forEach(id => {
    const h = myHoldings.value.find(h => h.id === id)
    if (h && !isAlreadyAdded(h)) remaining.add(id)
  })
  selectedHoldingIds.value = remaining
  if (importCount > 0) {
    ElMessage.success(`已导入 ${importCount} 个持仓`)
  }
}

// ============ 手动添加资产 ============
const addAsset = () => {
  if (!canAddAsset.value || !assetForm.value.selectedAsset) return
  const asset = assetForm.value.selectedAsset
  createForm.value.assets.push({
    assetId: asset.id,
    symbol: asset.code,
    name: asset.name,
    market: asset.market || '',
    displayMarket: (asset as any).displayMarket || asset.market || '',
    allocation: 0,  // 占比（getAssetAllocation 动态计算）
    amount: assetForm.value.amount
  })
  assetForm.value = { selectedAsset: null, amount: 0 }
  assetSearchResults.value = []
}

const removeAsset = (index: number) => {
  createForm.value.assets.splice(index, 1)
}

// ============ 持仓收益相关 ============
const fetchHoldingPerf = async () => {
  if (!authStore.isLoggedIn) return
  try {
    const data = await getHoldingPerformance()
    holdingPerf.value = data
    const map = new Map<number, HoldingPerformanceItem>()
    data.items?.forEach(item => map.set(item.assetId, item))
    holdingPerfMap.value = map
  } catch {
    // 收益接口失败不影响列表展示
    holdingPerf.value = null
    holdingPerfMap.value = new Map()
  }
}

/** 计算指定组合的实际持仓收益（基于组合中的资产） */
const getPortfolioReturn = (portfolio: any): string | null => {
  if (!authStore.isLoggedIn || !holdingPerfMap.value.size || !portfolio.assets?.length) {
    return null
  }
  
  // 检查是否是当前用户的组合
  if (portfolio.userId !== authStore.user?.id) {
    return null
  }

  // 计算该组合中所有资产的持仓收益
  let totalMarketValue = 0
  let totalCostValue = 0
  let hasAnyData = false
  
  portfolio.assets.forEach((asset: PortfolioAsset) => {
    const perf = holdingPerfMap.value.get(asset.assetId)
    if (perf?.hasData) {
      hasAnyData = true
      totalMarketValue += Number(perf.marketValue || 0)
      totalCostValue += Number(perf.costValue || 0)
    }
  })

  // 如果没有任何资产有持仓数据，返回 null（回退到 returnsYTD）
  if (!hasAnyData || totalCostValue === 0) return null
  
  const totalReturn = (totalMarketValue - totalCostValue) / totalCostValue
  return totalReturn.toString()
}

const getDisplayTotalReturn = (portfolio: any): number | null => {
  // 自己的组合：优先用持仓市值/成本推算的真实收益（与列表接口的 K 线口径可并存）
  const ownerReturn = getPortfolioReturn(portfolio)
  if (ownerReturn !== null && ownerReturn !== undefined && ownerReturn !== '') {
    const n = Number(ownerReturn)
    if (!isNaN(n)) return n
  }
  // 接口 totalReturn：列表接口由后端按持仓权重与日 K 推算的「年初至今」加权收益；勿用「!== 0」跳过，否则会与今日/7 日脱节
  const total = Number(portfolio.totalReturn)
  if (!isNaN(total)) return total
  const ytd = Number(portfolio.returnsYTD)
  if (!isNaN(ytd)) return ytd
  return null
}

// ============ 分页 / 列表 ============
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchPortfolios()
}

const handleFilterChange = (filter: string) => {
  currentFilter.value = filter
  currentPage.value = 1
  fetchPortfolios()
}

const fetchPortfolios = async () => {
  try {
    const params: any = {
      page: currentPage.value,
      pageSize: pageSize.value,
      sortBy: currentFilter.value === 'hot' ? 'likes' : 'returnsYTD'
    }
    
    // 根据筛选条件添加风险等级过滤
    if (currentFilter.value !== 'all' && currentFilter.value !== 'hot') {
      // 这里需要后端支持，暂时在前端过滤
    }
    
    await portfoliosStore.fetchPortfolios(params)
    // 获取持仓收益（如果已登录）
    fetchHoldingPerf()
  } catch (error) {
    ElMessage.error('获取投资组合失败')
  }
}

// ============ 创建组合 ============
const handleCreatePortfolio = async () => {
  if (!createFormRef.value) return
  try {
    await createFormRef.value.validate()

    if (createForm.value.assets.length === 0) {
      ElMessage.warning('请至少添加一个资产配置')
      return
    }

    creating.value = true

    // 将金额比例换算为 allocation（保留2位小数，最后一项补100%）
    const assets = createForm.value.assets
    const total = totalAmount.value
    let usedPct = 0
    const mappedAssets = assets.map((a, i) => {
      let pct: number
      if (i === assets.length - 1) {
        pct = parseFloat((100 - usedPct).toFixed(1))
      } else {
        pct = parseFloat(((a.amount / total) * 100).toFixed(1))
        usedPct += pct
      }
      return {
        assetId: a.assetId,
        symbol: a.symbol,
        name: a.name,
        allocation: pct
      }
    })

    const payload = {
      title: createForm.value.title,
      description: createForm.value.description,
      strategyNote: createForm.value.strategyNote,
      riskLevel: createForm.value.riskLevel,
      isPublic: createForm.value.isPublic,
      assets: mappedAssets
    }

    await portfoliosStore.createPortfolio(payload)

    ElMessage.success('投资组合创建成功')
    showCreatePortfolio.value = false
    resetCreateForm()
    fetchPortfolios()
  } catch (error: any) {
    if (error.fields) return
    ElMessage.error('创建失败，请稍后重试')
  } finally {
    creating.value = false
  }
}

const resetCreateForm = () => {
  createForm.value = {
    title: '',
    description: '',
    strategyNote: '',
    riskLevel: 'Medium',
    isPublic: true,
    assets: []
  }
  assetForm.value = { selectedAsset: null, amount: 0 }
  assetSearchResults.value = []
  addMode.value = 'manual'
  selectedHoldingIds.value = new Set()
  createFormRef.value?.clearValidate()
}

const handleLike = async (portfolioId: number) => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }

  try {
    await portfoliosStore.toggleLike(portfolioId)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleFavorite = async (portfolioId: number) => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    await portfoliosStore.toggleFavorite(portfolioId)
  } catch {
    ElMessage.error('操作失败')
  }
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${m}-${day}`
}

const getPieChartOption = (assets: PortfolioAsset[]) => {
  const data = buildPieSliceData(assets)
  const n = assets.length
  return {
    color: PIE_PALETTE,
    animationDuration: 480,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'item',
      confine: true,
      formatter: (params: unknown) => {
        const p = (Array.isArray(params) ? params[0] : params) as {
          name?: string
          value?: number
          percent?: number
          marker?: string
        }
        if (!p?.name) return ''
        const v = Number(p.value ?? 0).toFixed(1)
        const pct = p.percent != null ? Number(p.percent).toFixed(1) : '—'
        return `${p.marker ?? ''}<span style="font-weight:600">${p.name}</span><br/><span style="color:#64748b;font-size:11px">占比 ${v}% · 扇区 ${pct}%</span>`
      },
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: 'rgba(148, 163, 184, 0.45)',
      borderWidth: 1,
      padding: [10, 12],
      extraCssText: 'box-shadow: 0 4px 20px rgba(15,23,42,0.08); border-radius: 10px;',
      textStyle: {
        color: '#334155',
        fontSize: 12,
        fontFamily: 'Inter, system-ui, sans-serif'
      }
    },
    legend: {
      type: 'scroll',
      orient: 'horizontal',
      bottom: 0,
      left: 'center',
      width: '92%',
      itemGap: 14,
      itemWidth: 7,
      itemHeight: 7,
      icon: 'circle',
      pageIconColor: '#64748b',
      pageTextStyle: { color: '#64748b' },
      textStyle: {
        color: '#64748b',
        fontSize: 11,
        fontWeight: 500,
        fontFamily: 'Inter, system-ui, sans-serif'
      },
      formatter: (name: string) => (name.length > 10 ? `${name.slice(0, 9)}…` : name)
    },
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '36%',
        style: {
          text: '资产配置',
          textAlign: 'center',
          fill: '#94a3b8',
          fontSize: 11,
          fontWeight: 500,
          fontFamily: 'Inter, system-ui, sans-serif'
        }
      },
      {
        type: 'text',
        left: 'center',
        top: '44%',
        style: {
          text: `${n} 项持仓`,
          textAlign: 'center',
          fill: '#0f172a',
          fontSize: 15,
          fontWeight: 600,
          fontFamily: 'Inter, system-ui, "Segoe UI", sans-serif'
        }
      }
    ],
    series: [
      {
        name: '资产配置',
        type: 'pie',
        radius: ['52%', '74%'],
        center: ['50%', '46%'],
        clockwise: true,
        minAngle: 2,
        avoidLabelOverlap: true,
        itemStyle: {
          borderColor: '#f8fafc',
          borderWidth: 2,
          borderRadius: 2
        },
        label: { show: false },
        labelLine: { show: false },
        emphasis: {
          itemStyle: {
            shadowBlur: 14,
            shadowOffsetY: 2,
            shadowColor: 'rgba(37, 99, 235, 0.2)'
          }
        },
        data: data.map((d, index) => ({
          ...d,
          itemStyle: {
            color: PIE_PALETTE[index % PIE_PALETTE.length]
          }
        }))
      }
    ]
  }
}

const getAvatarUrl = (id: number) => {
  return `https://picsum.photos/seed/${id}/40/40`
}

onMounted(() => {
  fetchPortfolios()
})
</script>

<style lang="scss" scoped>
.portfolios {
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.portfolios-header {
  margin-bottom: $portfolio-space-8;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $portfolio-space-6;

  @media (max-width: 640px) {
    flex-direction: column;
    gap: $portfolio-space-4;
    align-items: stretch;
  }
}

.header-text {
  flex: 1;
}

.page-title {
  font-size: $portfolio-section-title;
  font-weight: 700;
  color: $portfolio-text-primary;
  margin: 0 0 $portfolio-space-2 0;
  letter-spacing: -0.01em;
}

.page-subtitle {
  font-size: $portfolio-body;
  color: $portfolio-text-secondary;
  margin: 0;
  line-height: 1.5;
}

.filter-tabs {
  display: flex;
  gap: $portfolio-space-2;
  flex-wrap: wrap;
}

.filter-tab {
  font-size: $portfolio-caption;
  font-weight: 500;
  padding: $portfolio-space-2 $portfolio-space-4;
  border: 1px solid $border-subtle;
  border-radius: $apple-radius-sm;
  background: $bg-card;
  color: $text-secondary;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    border-color: $border-default;
    color: $text-primary;
  }

  &.active {
    background: $primary-color;
    color: #fff;
    border-color: $primary-color;
    box-shadow: $portfolio-card-shadow;
  }
}

.create-btn {
  background: $gradient-primary !important;
  border: none !important;
  box-shadow: $shadow-purple !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  transition: $transition-all !important;

  &:hover {
    box-shadow: 0 8px 24px rgba(29, 78, 216, 0.3) !important;
    transform: translateY(-1px);
  }
}

.create-portfolio-dialog {
  :deep(.el-dialog) {
    background: $bg-card !important;
    border: 1px solid $border-strong !important;
    border-radius: $border-radius-xl !important;
  }

  :deep(.el-dialog__header) {
    padding: 1.5rem 1.5rem 1rem;
    border-bottom: 1px solid $border-default !important;
  }

  :deep(.el-dialog__title) {
    color: $text-primary !important;
    font-weight: 700 !important;
  }

  :deep(.el-dialog__body) {
    padding: 1.5rem;
  }

  :deep(.el-form-item__label) {
    color: $text-secondary !important;
  }
}

.assets-section {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid $border-subtle;
  border-radius: 12px;
  padding: 1rem;
}

.assets-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: $primary-color;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.add-asset {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.assets-list {
  max-height: 150px;
  overflow-y: auto;
  margin-bottom: 0.75rem;
}

.asset-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: rgba(15, 23, 42, 0.03);
  border: 1px solid $border-subtle;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  transition: $transition-all;

  &:hover {
    background: rgba(15, 23, 42, 0.04);
    border-color: $border-default;
  }
}

.asset-symbol {
  font-weight: 700;
  color: $text-primary;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.875rem;
}

.asset-allocation {
  color: $primary-color;
  font-weight: 700;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.875rem;
}

.remove-btn {
  color: $error-color !important;

  &:hover {
    background: rgba(239, 68, 68, 0.1) !important;
  }
}


// ============ 资产配置头部 & 模式切换 ============
.assets-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.875rem;
}

.add-mode-tabs {
  display: flex;
  gap: 0;
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid $border-subtle;
  border-radius: 8px;
  padding: 2px;
}

.mode-tab {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 3px 10px;
  border: none;
  background: transparent;
  color: $text-muted;
  border-radius: 6px;
  cursor: pointer;
  transition: $transition-all;
  letter-spacing: 0.02em;

  &:hover {
    color: $text-secondary;
  }

  &.active {
    background: $primary-color;
    color: #fff;
    box-shadow: 0 2px 8px rgba(29, 78, 216, 0.25);
  }
}

.mode-hint {
  font-size: 0.7rem;
  color: $text-muted;
  margin: 0.25rem 0 0.5rem;
  padding-left: 2px;
}

// ============ 持仓导入列表 ============
.holdings-loading {
  padding: 0.5rem 0;
}

.holdings-empty {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8125rem;
  color: $text-muted;
  padding: 0.75rem 0;
}

.import-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  padding: 0 2px;

  :deep(.el-checkbox__label) {
    font-size: 0.75rem;
    color: $text-secondary;
  }
}

.holdings-import-list {
  max-height: 140px;
  overflow-y: auto;
  margin-bottom: 0.5rem;
  border: 1px solid $border-subtle;
  border-radius: 8px;
  overflow: hidden;
}

.holding-import-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.375rem 0.625rem;
  cursor: pointer;
  transition: $transition-all;
  border-bottom: 1px solid rgba(15, 23, 42, 0.03);
  font-size: 0.75rem;

  &:last-child {
    border-bottom: none;
  }

  &:hover:not(.already) {
    background: rgba(29, 78, 216, 0.06);
  }

  &.selected {
    background: rgba(124, 58, 237, 0.1);
  }

  &.already {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.h-code {
  font-weight: 700;
  font-family: 'IBM Plex Mono', monospace;
  color: $text-primary;
  min-width: 52px;
}

.h-name {
  flex: 1;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.h-amount {
  font-family: 'IBM Plex Mono', monospace;
  color: $primary-color;
  font-weight: 600;
  font-size: 0.7rem;
  white-space: nowrap;
}

.h-added-badge {
  font-size: 0.65rem;
  color: $success-color;
  background: rgba(52, 211, 153, 0.1);
  padding: 1px 5px;
  border-radius: 4px;
  white-space: nowrap;
}

// ============ 资产条目（含金额+占比）============
.asset-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1px;
  margin-right: 0.25rem;
}

.asset-amount-small {
  font-size: 0.65rem;
  color: $text-muted;
  font-family: 'IBM Plex Mono', monospace;
}

// 总配置摘要（新版）
.allocation-summary {
  font-size: 0.8125rem;
  font-weight: 600;
  color: $text-secondary;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.5rem;
  border-top: 1px solid $border-subtle;
  font-family: 'IBM Plex Mono', monospace;

  .alloc-pct {
    color: $text-muted;
    &.alloc-ok {
      color: $success-color;
    }
  }
}

// ============ 原资产搜索下拉选项 ============
.asset-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;

  .opt-code {
    font-weight: 700;
    font-family: 'IBM Plex Mono', monospace;
    color: $text-primary;
    min-width: 60px;
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

// 资产列表条目信息
.asset-info {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  flex: 1;
  min-width: 0;
}

.asset-name-small {
  font-size: 0.75rem;
  color: $text-muted;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.asset-market-tag {
  font-size: 0.65rem !important;
  padding: 0 4px !important;
  height: 16px !important;
  line-height: 16px !important;
  flex-shrink: 0;
}

.dialog-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

// ============================================
// Portfolio Grid
// ============================================
.portfolios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1.25rem;
  margin-bottom: 2rem;
}

.loading-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1.25rem;
}

.portfolio-skeleton {
  background: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 22px;
  padding: 1.5rem;
  box-shadow: $apple-shadow-sm;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  background: linear-gradient(145deg, rgba(255,255,255,0.03) 0%, transparent 100%);
  border: 1px dashed $border-default;
  border-radius: $border-radius;
}

.portfolio-card {
  font-family: $apple-font-family;
  background: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.38);
  border-radius: 22px;
  padding: 1.65rem 1.5rem 1.5rem;
  cursor: pointer;
  transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1),
    box-shadow 0.28s cubic-bezier(0.4, 0, 0.2, 1),
    border-color 0.28s ease;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 6px 20px rgba(15, 23, 42, 0.05);

  &:hover {
    border-color: rgba(37, 99, 235, 0.22);
    box-shadow:
      0 4px 12px rgba(15, 23, 42, 0.06),
      0 12px 32px rgba(15, 23, 42, 0.08);
    transform: translateY(-3px);
  }
}

.portfolio-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: $portfolio-space-3;
  margin-bottom: $portfolio-space-3;
}

.portfolio-title {
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  flex: 1;
  min-width: 0;
  line-height: 1.35;
  letter-spacing: -0.02em;
}

.portfolio-summary {
  margin: 0 0 $portfolio-space-4 0;
  color: $text-secondary;
  font-size: $portfolio-caption;
  line-height: 1.55;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.risk-pill {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  padding: 5px 11px;
  border-radius: 999px;
  border: none;
  line-height: 1.2;

  &--low {
    background: rgba(22, 163, 74, 0.12);
    color: #15803d;
  }

  &--medium {
    background: rgba(217, 119, 6, 0.12);
    color: #b45309;
  }

  &--high {
    background: rgba(220, 38, 38, 0.1);
    color: #b91c1c;
  }
}

// 收益率区域（前置并突出）
.portfolio-return-section {
  text-align: center;
  margin: $portfolio-space-2 0 $portfolio-space-5;
  padding: $portfolio-space-5 $portfolio-space-3;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.return-value {
  font-size: clamp(1.75rem, 4.5vw, 2.125rem);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum' 1, 'lnum' 1;
  font-family: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  line-height: 1.15;
  margin-bottom: $portfolio-space-2;
  letter-spacing: -0.03em;

  &.pnl-up {
    color: #15803d;
  }

  &.pnl-down {
    color: #b91c1c;
  }

  &.pnl-zero {
    color: #94a3b8;
  }
}

.return-label {
  font-size: 11px;
  font-weight: 500;
  color: #94a3b8;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: $portfolio-space-4;
}

.return-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $portfolio-space-2;
  max-width: 280px;
  margin: 0 auto;
}

.return-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: $portfolio-space-2 $portfolio-space-2;
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.85);
}

.return-stat-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #94a3b8;
}

.return-stat-value {
  font-size: 13px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum' 1;
  font-family: 'IBM Plex Mono', ui-monospace, monospace;
  letter-spacing: -0.02em;

  &.pnl-up {
    color: #15803d;
  }

  &.pnl-down {
    color: #b91c1c;
  }

  &.pnl-zero {
    color: #94a3b8;
  }
}

// 图表区域
.chart-section {
  margin: $portfolio-space-2 0 $portfolio-space-4;
}

.chart-container {
  height: 208px;
  margin-bottom: $portfolio-space-2;
}

.pie-chart {
  width: 100%;
  height: 100%;
}

.chart-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  align-items: center;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  height: 26px;
  padding: 0 11px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.01em;
  color: #475569;
  background: rgba(241, 245, 249, 0.95);
  border: 1px solid rgba(203, 213, 225, 0.75);
  border-radius: 999px;
  white-space: nowrap;
  max-width: 100%;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;

  &:last-child {
    margin-bottom: 0;
  }
}

.stat-label {
  font-size: 0.7rem;
  color: $text-muted;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.stat-value {
  font-size: 0.875rem;
  font-weight: 700;
  color: $text-primary;
  font-family: 'IBM Plex Mono', monospace;

  &.positive {
    color: $success-color;
  }

  &.pnl-up {
    color: #10b981;
  }

  &.pnl-down {
    color: #f43f5e;
  }

  &.pnl-zero {
    color: $text-muted;
  }
}

.portfolio-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: $portfolio-space-4;
  border-top: 1px solid rgba(226, 232, 240, 0.95);
  margin-top: auto;
}

.portfolio-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.portfolio-author {
  display: flex;
  align-items: center;
  gap: $portfolio-space-2;
}

.author-name {
  font-size: $portfolio-caption;
  color: $text-muted;
  font-weight: 400;
}

.author-clickable {
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    opacity: 0.8;
  }
}

.like-btn {
  display: flex !important;
  align-items: center !important;
  gap: $portfolio-space-2 !important;
  color: $text-muted !important;
  font-size: $portfolio-caption !important;
  border-radius: $apple-radius-sm !important;
  padding: 4px 8px !important;
  transition: $transition-all !important;
  font-family: 'IBM Plex Mono', monospace !important;

  &:hover {
    color: $error-color !important;
    background: rgba(239, 68, 68, 0.08) !important;
  }

  &.liked {
    color: $error-color !important;
    background: rgba(239, 68, 68, 0.06) !important;
  }
}

.pagination-container {
  display: flex;
  justify-content: center;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>






