<template>
  <div class="market-list-page">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-row">
        <h2 class="page-title">行情列表</h2>
        <router-link :to="{ name: 'MarketRankings' }" class="rankings-link">
          <el-button size="small" type="primary" plain>
            🏆 涨跌幅榜
          </el-button>
        </router-link>
      </div>

      <!-- 搜索 + 筛选 -->
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
          <el-option label="A股沪市 (SH)" value="SH" />
          <el-option label="A股深市 (SZ)" value="SZ" />
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

      <!-- 骨架屏 -->
      <div v-if="loading" class="skeleton-wrapper">
        <div v-for="i in 10" :key="i" class="skeleton-row">
          <el-skeleton animated :rows="1" />
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="assets.length === 0" class="empty-state">
        <el-empty description="未找到相关资产" :image-size="80" />
      </div>

      <!-- 资产行 -->
      <template v-else>
        <router-link
          v-for="item in assets"
          :key="item.id"
          :to="{ name: 'AssetDetail', params: { assetId: item.id } }"
          class="list-row"
          :class="getChangePctClass(item.changePct)"
        >
          <div class="col-code">
            <span class="asset-code">{{ item.code }}</span>
            <span class="asset-name">{{ item.name }}</span>
          </div>
          <div class="col-market">
            <el-tag size="small" :type="getMarketTagType(item.market)">
              {{ item.market || '—' }}
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
      行情数据来源：Finnhub Finance，仅供学习研究，不构成投资建议。数据可能有延迟。
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'
import { getAssetsWithQuote } from '../api/market'
import type { AssetWithQuote } from '../api/market'

const searchQ = ref('') 
const filterMarket = ref('')
const filterType = ref('')
const page = ref(1)
const pageSize = ref(20)
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

// 格式化
const formatPrice = (val: any) => {
  if (val === null || val === undefined) return '—'
  return parseFloat(String(val)).toFixed(2)
}

const formatChangePct = (val: any) => {
  if (val === null || val === undefined) return '—'
  const num = parseFloat(String(val))
  const sign = num > 0 ? '+' : ''
  return `${sign}${num.toFixed(2)}%`
}

const formatVolume = (val: any) => {
  if (val === null || val === undefined) return '—'
  const n = Number(val)
  if (n >= 1e8) return `${(n / 1e8).toFixed(2)}亿`
  if (n >= 1e4) return `${(n / 1e4).toFixed(2)}万`
  return String(n)
}

const formatTime = (str: string | null | undefined) => {
  if (!str) return '—'
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

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.market-list-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.page-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .page-title {
    font-size: 1.375rem;
    font-weight: 700;
    color: #F0F4FF;
    margin: 0;
  }

  .rankings-link {
    text-decoration: none;
  }
}

.filter-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;

  .search-input {
    flex: 1;
    min-width: 200px;

    :deep(.el-input__wrapper) {
      background: rgba(255, 255, 255, 0.04);
      border-color: rgba(255, 255, 255, 0.1);
    }

    :deep(.el-input__inner) {
      color: #F0F4FF;
      &::placeholder { color: #6B7A99; }
    }
  }

  .filter-select {
    width: 160px;

    :deep(.el-select__wrapper) {
      background: rgba(255, 255, 255, 0.04);
      border-color: rgba(255, 255, 255, 0.1);
      color: #A0AABF;
    }
  }
}

// 列表卡片
.card {
  background: #141B2D;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  overflow: hidden;
}

.list-header {
  display: grid;
  grid-template-columns: 2fr 80px 80px 100px 100px 100px 110px;
  gap: 0;
  padding: 0.625rem 1.25rem;
  background: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 0.75rem;
  color: #6B7A99;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;

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
  grid-template-columns: 2fr 80px 80px 100px 100px 100px 110px;
  gap: 0;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  text-decoration: none;
  color: inherit;
  transition: background 0.15s;
  cursor: pointer;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: rgba(255, 255, 255, 0.035);
  }

  > div {
    display: flex;
    align-items: center;
    font-size: 0.875rem;

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
  gap: 2px;

  .asset-code {
    font-weight: 700;
    color: #E2E8F0;
    font-size: 0.875rem;
  }

  .asset-name {
    font-size: 0.75rem;
    color: #6B7A99;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 160px;
  }
}

.col-market {
  :deep(.el-tag) {
    font-size: 0.7rem;
  }
}

.type-label {
  font-size: 0.7rem;
  color: #6B7A99;
}

.col-price {
  font-weight: 700;
  font-size: 0.9rem !important;

  &.up { color: #f56c6c; }
  &.down { color: #67c23a; }
  &.flat { color: #A0AABF; }
}

.change-badge {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;

  &.up {
    color: #f56c6c;
    background: rgba(245, 108, 108, 0.1);
  }
  &.down {
    color: #67c23a;
    background: rgba(103, 194, 58, 0.1);
  }
  &.flat {
    color: #909399;
    background: rgba(144, 147, 153, 0.1);
  }
}

.col-volume {
  font-size: 0.8rem !important;
  color: #6B7A99;
}

.col-time {
  font-size: 0.75rem !important;
  color: #6B7A99;
}

.skeleton-wrapper {
  padding: 0.5rem 0;

  .skeleton-row {
    padding: 0.75rem 1.25rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
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
    --el-pagination-hover-color: #A78BFA;
  }
}

.disclaimer {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #6B7A99;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  font-style: italic;
}
</style>
