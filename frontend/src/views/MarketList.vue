<template>
  <div class="market-list-page">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-section">
        <div class="page-title-row">
          <div class="title-group">
            <h2 class="page-title">行情列表</h2>
            <p class="page-subtitle">浏览全球市场中的股票 / ETF / 基金</p>
          </div>
          <router-link :to="{ name: 'MarketRankings' }" class="rankings-link">
            <el-button size="small" type="default" plain class="rankings-btn">
              <el-icon style="margin-right:4px;">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6">
                  <path d="M8 4h8v3a4 4 0 0 1-4 4 4 4 0 0 1-4-4V4Z" />
                  <path d="M8 4H5a2 2 0 0 0-2 2v1a4 4 0 0 0 4 4" />
                  <path d="M16 4h3a2 2 0 0 1 2 2v1a4 4 0 0 1-4 4" />
                </svg>
              </el-icon>
              涨跌幅榜
            </el-button>
          </router-link>
        </div>

        <!-- 搜索 + 筛选-->
        <div class="filter-row">
          <el-input
            v-model="searchQ"
            placeholder="搜索代码或名称..."
            clearable
            class="search-input"
            @input="handleSearchInput"
            @clear="handleSearch"
          >
            <template #prefix>
              <el-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></el-icon>
            </template>
          </el-input>

          <el-select
            v-model="filterMarket"
            placeholder="全部市场"
            clearable
            size="default"
            @change="handleFilter"
            class="filter-select"
          >
            <el-option label="全部市场" value="" />
            <el-option label="A股沪市(SH)" value="SH" />
            <el-option label="A股深市(SZ)" value="SZ" />
            <el-option label="港股 (HK)" value="HK" />
            <el-option label="美股 (US)" value="US" />
          </el-select>

          <el-select
            v-model="filterType"
            placeholder="全部类型"
            clearable
            size="default"
            @change="handleFilter"
            class="filter-select"
          >
            <el-option label="全部类型" value="" />
            <el-option label="股票 STOCK" value="STOCK" />
            <el-option label="基金 FUND" value="FUND" />
            <el-option label="ETF" value="ETF" />
            <el-option label="债券 BOND" value="BOND" />
          </el-select>
        </div>
      </div>
    </div>

    <!-- 市场摘要区 -->
    <div class="market-summary" v-if="!loading && assets.length > 0">
      <span class="summary-item">
        <span class="summary-label">共</span>
        <span class="summary-value">{{ total }}</span>
        <span class="summary-label">支资产</span>
      </span>
      <span class="summary-divider">·</span>
      <span class="summary-item" v-if="filterMarket || filterType">
        <span class="summary-label">当前筛选：</span>
        <span class="summary-value">{{ getFilterText() }}</span>
      </span>
      <span class="summary-divider">·</span>
      <span class="summary-item">
        <span class="summary-label">数据来源：</span>
        <span class="summary-value">Tushare</span>
      </span>
    </div>

    <!-- 资产列表 -->
    <div class="list-card card">
      <!-- 表头 -->
      <div class="list-header">
        <div class="col-code">代码 / 名称</div>
        <div class="col-market">市场</div>
        <div class="col-type">类型</div>
        <div class="col-price">最新价</div>
        <div class="col-change">涨跌幅</div>
        <div class="col-volume">成交量</div>
        <div class="col-time">更新时间</div>
      </div>

      <!-- 骨架图-->
      <div v-if="loading" class="skeleton-wrapper">
        <div v-for="i in 10" :key="i" class="skeleton-row">
          <el-skeleton animated :rows="1" />
        </div>
      </div>

      <!-- 空状态-->
      <div v-else-if="assets.length === 0" class="empty-state">
        <el-empty description="未找到相关资产" :image-size="80" />
      </div>

      <!-- 资产列表-->
      <template v-else>
        <router-link
          v-for="item in assets"
          :key="item.id"
          :to="{ name: 'AssetDetail', params: { assetId: item.id } }"
          class="list-row"
          :class="getChangePctClass(item.changePct)"
          @mouseenter="preloadAssetDetailCharts"
          @mousedown="preloadAssetDetailCharts"
        >
          <div class="col-code">
            <span class="asset-code">{{ item.code }}</span>
            <span class="asset-name">{{ item.name }}</span>
          </div>
          <div class="col-market">
            <el-tag size="small" :type="getMarketTagType(item.market)">
              {{ item.market || '--' }}
            </el-tag>
          </div>
          <div class="col-type">
            <span class="type-label">{{ item.asset_type }}</span>
          </div>
          <div class="col-price" :class="getChangePctClass(item.changePct)">
            {{ formatPrice(item.price) }}
          </div>
          <div class="col-change">
            <span class="change-badge" :class="getChangePctClass(item.changePct)">
              {{ formatChangePct(item.changePct) }}
            </span>
          </div>
          <div class="col-volume">
            {{ formatVolume(item.volume) }}
          </div>
          <div class="col-time">{{ formatTime(item.quoteTime) }}</div>
        </router-link>
      </template>
    </div>

    <!-- 分页 -->
    <div class="pagination-row" v-if="total > pageSize">
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, jumper, total"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 免责声明 -->
    <div class="disclaimer">
      <el-icon><InfoFilled /></el-icon>
      行情数据来源：Tushare，仅供学习研究，不构成投资建议。数据可能有延迟。
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'
import { getAssetsWithQuote } from '../api/market'
import type { AssetWithQuote } from '../api/market'
import { preloadAssetDetailCharts } from '../utils/preload'

const searchQ = ref('') 
const filterMarket = ref('')
const filterType = ref('')
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const loading = ref(false)
const assets = ref<AssetWithQuote[]>([])

let searchTimer: ReturnType<typeof setTimeout> | null = null

const loadData = async () => {
  loading.value = true
  try {
    const params: any = {
      withQuote: 1,
      page: page.value,
      pageSize: pageSize.value,
    }
    if (searchQ.value) params.q = searchQ.value
    if (filterMarket.value) params.market = filterMarket.value
    if (filterType.value) params.type = filterType.value

    const res = await getAssetsWithQuote(params)
    assets.value = res.items as any
    total.value = res.total
  } catch (e) {
    assets.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handleSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadData()
  }, 400)
}

const handleSearch = () => {
  page.value = 1
  loadData()
}

const handleFilter = () => {
  page.value = 1
  loadData()
}

const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadData()
}

// 格式化方法
const formatPrice = (val: any) => {
  if (val === null || val === undefined) return '--'; 
  return parseFloat(String(val)).toFixed(2)
}

const formatChangePct = (val: any) => {
  if (val === null || val === undefined) return '--';
  const num = parseFloat(String(val))
  const sign = num > 0 ? '+' : ''
  return `${sign}${num.toFixed(2)}%`
}

const formatVolume = (val: any) => {
  if (val === null || val === undefined) return '--';
  const n = Number(val)
  if (n >= 1e8) return `${(n / 1e8).toFixed(2)}亿`
  if (n >= 1e4) return `${(n / 1e4).toFixed(2)}万`
  return String(n)
}

const formatTime = (str: string | null | undefined) => {
  if (!str) return '--';
  const d = new Date(str)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${min}`
}

const getChangePctClass = (val: any) => {
  if (val === null || val === undefined) return 'flat'
  const n = parseFloat(String(val))
  if (n > 0) return 'up'
  if (n < 0) return 'down'
  return 'flat'
}

const getMarketTagType = (market?: string) => {
  const m = market?.toUpperCase()
  if (m === 'SH' || m === 'SZ') return 'danger'
  if (m === 'HK') return 'warning'
  if (m === 'US') return 'primary'
  return 'info'
}

const getFilterText = () => {
  const parts: string[] = []
  if (filterMarket.value) {
    const marketMap: Record<string, string> = {
      SH: 'A股沪市',
      SZ: 'A股深市',
      HK: '港股',
      US: '美股'
    }
    parts.push(marketMap[filterMarket.value] || filterMarket.value)
  }
  if (filterType.value) {
    const typeMap: Record<string, string> = {
      STOCK: '股票',
      FUND: '基金',
      ETF: 'ETF',
      BOND: '债券'
    }
    parts.push(typeMap[filterType.value] || filterType.value)
  }
  return parts.length > 0 ? parts.join(' / ') : '全部'
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.market-list-page {
  display: flex;
  flex-direction: column;
  gap: $market-space-5;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: $market-space-4;
}

.page-title-section {
  display: flex;
  flex-direction: column;
  gap: $market-space-4;
}

.page-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: $market-space-4;

  .title-group {
    display: flex;
    flex-direction: column;
    gap: $market-space-2;
  }

  .page-title {
    font-size: $market-font-h1;
    font-weight: 700;
    color: $market-text-primary;
    margin: 0;
    line-height: 1.2;
  }

  .page-subtitle {
    font-size: $market-font-caption;
    color: $market-text-secondary;
    margin: 0;
    line-height: 1.4;
  }

  .rankings-link {
    text-decoration: none;
    flex-shrink: 0;
  }

  .rankings-btn {
    :deep(.el-button) {
      border-color: $apple-border-light;
      color: $market-text-secondary;
      font-weight: 500;
      transition: $transition-colors;

      &:hover {
        border-color: $market-accent;
        color: $market-accent;
        background: $market-accent-soft;
      }
    }
  }
}

.filter-row {
  display: flex;
  gap: $market-space-3;
  flex-wrap: wrap;
  align-items: center;

  .search-input {
    flex: 1;
    min-width: 280px;

    :deep(.el-input__wrapper) {
      background: $apple-input-bg;
      border: 1px solid $apple-input-border;
      border-radius: $market-radius-input;
      height: 48px;
      box-shadow: $market-shadow-sm;
      transition: $transition-all;

      &:hover {
        border-color: $market-accent;
        box-shadow: $market-shadow-md;
      }

      &.is-focus {
        border-color: $market-accent;
        box-shadow: 0 0 0 3px $market-accent-soft;
      }
    }

    :deep(.el-input__inner) {
      color: $market-text-primary;
      font-size: $market-font-body;
      &::placeholder { 
        color: $market-text-tertiary; 
      }
    }

    :deep(.el-input__prefix) {
      color: $market-text-tertiary;
    }
  }

  .filter-select {
    width: 160px;
    height: 48px;

    :deep(.el-select__wrapper) {
      background: $apple-input-bg;
      border: 1px solid $apple-input-border;
      border-radius: $market-radius-input;
      height: 48px;
      box-shadow: $market-shadow-sm;
      transition: $transition-all;
      color: $market-text-primary;

      &:hover {
        border-color: $market-accent;
        box-shadow: $market-shadow-md;
      }

      &.is-focused {
        border-color: $market-accent;
        box-shadow: 0 0 0 3px $market-accent-soft;
      }
    }

    :deep(.el-select__placeholder) {
      color: $market-text-tertiary;
    }
  }
}

// 市场摘要区
.market-summary {
  display: flex;
  align-items: center;
  gap: $market-space-3;
  padding: $market-space-3 $market-space-4;
  background: $market-bg-panel;
  border: 1px solid $apple-border-light;
  border-radius: $market-radius-md;
  font-size: $market-font-caption;
  color: $market-text-secondary;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);

  .summary-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .summary-label {
    color: $market-text-tertiary;
  }

  .summary-value {
    color: $market-text-primary;
    font-weight: 600;
  }

  .summary-divider {
    color: $market-text-tertiary;
    opacity: 0.5;
  }
}

// 列表卡片
.card {
  background: $market-bg-soft;
  border: 1px solid $apple-border-light;
  border-radius: $market-radius-lg;
  overflow: hidden;
  box-shadow: $market-shadow-sm;
  transition: $transition-all;

  &:hover {
    box-shadow: $market-shadow-md;
  }
}

.list-header {
  display: grid;
  grid-template-columns: 2fr 100px 100px 120px 120px 120px 140px;
  gap: 0;
  padding: $market-space-4 $market-space-5;
  background: transparent;
  border-bottom: 1px solid $apple-border-light;
  font-size: $market-font-mini;
  color: $market-text-tertiary;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;

  > div {
    display: flex;
    align-items: center;

    &.col-price, &.col-change, &.col-volume, &.col-time {
      justify-content: flex-end;
    }
  }
}

.list-row {
  display: grid;
  grid-template-columns: 2fr 100px 100px 120px 120px 120px 140px;
  gap: 0;
  padding: $market-space-5 $market-space-5;
  border-bottom: 1px solid rgba(0, 0, 0, 0.02);
  text-decoration: none;
  color: inherit;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  min-height: 80px;
  align-items: center;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: rgba(0, 113, 227, 0.03);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    border-radius: $market-radius-md;
    margin: 0 $market-space-2;
  }

  > div {
    display: flex;
    align-items: center;
    font-size: $market-font-body;

    &.col-price, &.col-volume, &.col-time {
      justify-content: flex-end;
    }

    &.col-change {
      justify-content: flex-end;
    }
  }
}

.col-code {
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-start !important;
  gap: $market-space-2;

  .asset-code {
    font-weight: 700;
    color: $market-text-primary;
    font-size: $market-font-body;
    letter-spacing: 0.02em;
  }

  .asset-name {
    font-size: $market-font-caption;
    color: $market-text-secondary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 200px;
  }
}

.col-market {
  :deep(.el-tag) {
    font-size: $market-font-mini;
    border-radius: $market-radius-sm;
    padding: 2px 8px;
    font-weight: 500;
  }
}

.type-label {
  font-size: $market-font-mini;
  color: $market-text-secondary;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: $market-radius-sm;
}

.col-price {
  font-weight: 700;
  font-size: $market-font-h3 !important;
  letter-spacing: -0.01em;

  &.up { color: $market-up; }
  &.down { color: $market-down; }
  &.flat { color: $market-neutral; }
}

.change-badge {
  font-size: $market-font-caption;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: $market-radius-sm;

  &.up {
    color: $market-up;
    background: rgba(232, 93, 93, 0.1);
  }
  &.down {
    color: $market-down;
    background: rgba(22, 163, 74, 0.1);
  }
  &.flat {
    color: $market-neutral;
    background: rgba(100, 116, 139, 0.1);
  }
}

.col-volume {
  font-size: $market-font-caption !important;
  color: $market-text-secondary;
  font-weight: 500;
}

.col-time {
  font-size: $market-font-mini !important;
  color: $market-text-tertiary;
}

.skeleton-wrapper {
  padding: 0.5rem 0;

  .skeleton-row {
    padding: 0.75rem 1.25rem;
    border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  }
}

.empty-state {
  padding: 3rem;
  display: flex;
  justify-content: center;
}

.pagination-row {
  display: flex;
  justify-content: center;

  :deep(.el-pagination) {
    --el-pagination-bg-color: transparent;
    --el-pagination-text-color: #A0AABF;
    --el-pagination-button-color: #A0AABF;
    --el-pagination-hover-color: #3B82F6;
  }
}

.disclaimer {
  display: flex;
  align-items: center;
  gap: $market-space-2;
  font-size: $market-font-mini;
  color: $market-text-tertiary;
  padding: $market-space-3 $market-space-4;
  background: $market-bg-panel;
  border: 1px solid $apple-border-light;
  border-radius: $market-radius-md;
  font-style: italic;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
</style>


