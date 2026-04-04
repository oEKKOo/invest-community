<template>
  <div class="market-rankings-page">
    <!-- 页头 -->
    <div class="page-header">
      <div class="header-row">
        <div class="title-group">
          <router-link :to="{ name: 'MarketList' }" class="back-link">
            <el-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg></el-icon>
            行情列表
          </router-link>
          <h2 class="page-title">涨跌幅榜</h2>
        </div>

        <!-- 市场筛选-->
        <el-select
          v-model="selectedMarket"
          placeholder="全部市场"
          clearable
          size="default"
          @change="loadAll"
          class="market-select"
        >
          <el-option label="全部市场" value="" />
          <el-option label="A股沪市(SH)" value="SH" />
          <el-option label="A股深市(SZ)" value="SZ" />
          <el-option label="港股 (HK)" value="HK" />
          <el-option label="美股 (US)" value="US" />
        </el-select>
      </div>
    </div>

    <!-- 三列榜单 -->
    <div class="rankings-grid">
      <!-- 涨幅榜单-->
      <div class="ranking-card card">
        <div class="ranking-header up">
          <span class="ranking-icon">
            <el-icon>
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6">
                <path d="M4 17 10 11 14 15 20 7" />
                <path d="M14 7h6v6" />
              </svg>
            </el-icon>
          </span>
          <h3 class="ranking-title">涨幅榜单</h3>
          <el-tag size="small" type="danger" class="count-tag">TOP {{ gainers.length }}</el-tag>
        </div>

        <div v-if="gainersLoading" class="ranking-loading">
          <el-skeleton :rows="8" animated />
        </div>
        <div v-else-if="gainers.length === 0" class="ranking-empty">
          <el-empty description="暂无数据" :image-size="48" />
        </div>
        <div v-else class="ranking-list">
          <router-link
            v-for="item in gainers"
            :key="item.assetId"
            :to="{ name: 'AssetDetail', params: { assetId: item.assetId } }"
            class="ranking-item"
            @mouseenter="preloadAssetDetailCharts"
            @mousedown="preloadAssetDetailCharts"
          >
            <span class="rank-badge" :class="getRankClass(item.rank)">{{ item.rank }}</span>
            <div class="asset-info">
              <span class="asset-code">{{ item.code }}</span>
              <span class="asset-name">{{ item.name }}</span>
            </div>
            <div class="quote-info">
              <span class="price up">{{ formatPrice(item.price) }}</span>
              <span class="change-pct up">{{ formatChangePct(item.changePct) }}</span>
            </div>
          </router-link>
        </div>
      </div>

      <!-- 跌幅榜单-->
      <div class="ranking-card card">
        <div class="ranking-header down">
          <span class="ranking-icon">
            <el-icon>
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6">
                <path d="M4 7 10 13 14 9 20 17" />
                <path d="M14 17h6v-6" />
              </svg>
            </el-icon>
          </span>
          <h3 class="ranking-title">跌幅榜单</h3>
          <el-tag size="small" type="success" class="count-tag">TOP {{ losers.length }}</el-tag>
        </div>

        <div v-if="losersLoading" class="ranking-loading">
          <el-skeleton :rows="8" animated />
        </div>
        <div v-else-if="losers.length === 0" class="ranking-empty">
          <el-empty description="暂无数据" :image-size="48" />
        </div>
        <div v-else class="ranking-list">
          <router-link
            v-for="item in losers"
            :key="item.assetId"
            :to="{ name: 'AssetDetail', params: { assetId: item.assetId } }"
            class="ranking-item"
            @mouseenter="preloadAssetDetailCharts"
            @mousedown="preloadAssetDetailCharts"
          >
            <span class="rank-badge" :class="getRankClass(item.rank)">{{ item.rank }}</span>
            <div class="asset-info">
              <span class="asset-code">{{ item.code }}</span>
              <span class="asset-name">{{ item.name }}</span>
            </div>
            <div class="quote-info">
              <span class="price down">{{ formatPrice(item.price) }}</span>
              <span class="change-pct down">{{ formatChangePct(item.changePct) }}</span>
            </div>
          </router-link>
        </div>
      </div>

      <!-- 活跃榜单-->
      <div class="ranking-card card">
        <div class="ranking-header active">
          <span class="ranking-icon">
            <el-icon>
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6">
                <path d="M12 3s2 2.5 2 5.5S12 14 12 14s-2-2-2-5.5S12 3 12 3Z" />
                <path d="M8.5 8.5C7 10 6 11.5 6 14a6 6 0 0 0 12 0c0-2.5-1-4-2.5-5.5" />
              </svg>
            </el-icon>
          </span>
          <h3 class="ranking-title">活跃榜单</h3>
          <el-tag size="small" type="warning" class="count-tag">TOP {{ actives.length }}</el-tag>
        </div>

        <div v-if="activesLoading" class="ranking-loading">
          <el-skeleton :rows="8" animated />
        </div>
        <div v-else-if="actives.length === 0" class="ranking-empty">
          <el-empty description="暂无数据" :image-size="48" />
        </div>
        <div v-else class="ranking-list">
          <router-link
            v-for="item in actives"
            :key="item.assetId"
            :to="{ name: 'AssetDetail', params: { assetId: item.assetId } }"
            class="ranking-item"
            @mouseenter="preloadAssetDetailCharts"
            @mousedown="preloadAssetDetailCharts"
          >
            <span class="rank-badge" :class="getRankClass(item.rank)">{{ item.rank }}</span>
            <div class="asset-info">
              <span class="asset-code">{{ item.code }}</span>
              <span class="asset-name">{{ item.name }}</span>
            </div>
            <div class="quote-info">
              <span class="price" :class="getChangePctClass(item.changePct)">{{ formatPrice(item.price) }}</span>
              <span class="change-pct" :class="getChangePctClass(item.changePct)">{{ formatChangePct(item.changePct) }}</span>
            </div>
          </router-link>
        </div>
      </div>
    </div>

    <!-- 免责声明 -->
    <div class="disclaimer">
      <el-icon><InfoFilled /></el-icon>
      榜单数据来源：Tushare，每日收市后更新，仅供学习参考，不构成投资建议。
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'
import { getMarketRankings } from '../api/market'
import type { MarketRankingItem } from '../types/market'
import { preloadAssetDetailCharts } from '../utils/preload'

const selectedMarket = ref('')

const gainers = ref<MarketRankingItem[]>([])
const losers = ref<MarketRankingItem[]>([])
const actives = ref<MarketRankingItem[]>([])
const gainersLoading = ref(false)
const losersLoading = ref(false)
const activesLoading = ref(false)

const loadGainers = async () => {
  gainersLoading.value = true
  try {
    const res = await getMarketRankings({
      type: 'gainers',
      limit: 12,
      market: selectedMarket.value as any || undefined
    })
    gainers.value = res.items
  } catch {
    gainers.value = []
  } finally {
    gainersLoading.value = false
  }
}

const loadLosers = async () => {
  losersLoading.value = true
  try {
    const res = await getMarketRankings({
      type: 'losers',
      limit: 12,
      market: selectedMarket.value as any || undefined
    })
    losers.value = res.items
  } catch {
    losers.value = []
  } finally {
    losersLoading.value = false
  }
}

const loadActives = async () => {
  activesLoading.value = true
  try {
    const res = await getMarketRankings({
      type: 'active',
      limit: 12,
      market: selectedMarket.value as any || undefined
    })
    actives.value = res.items
  } catch {
    actives.value = []
  } finally {
    activesLoading.value = false
  }
}

const loadAll = () => {
  loadGainers()
  loadLosers()
  loadActives()
}

// 格式化方法
const formatPrice = (val: number) => {
  if (val === null || val === undefined) return '--';
  return val.toFixed(2)
}

const formatChangePct = (val: number) => {
  if (val === null || val === undefined) return '--';
  const sign = val > 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}%`
}

const getChangePctClass = (val: number) => {
  if (val > 0) return 'up'
  if (val < 0) return 'down'
  return 'flat'
}

const getRankClass = (rank: number) => {
  if (rank === 1) return 'gold'
  if (rank === 2) return 'silver'
  if (rank === 3) return 'bronze'
  return ''
}

onMounted(() => {
  loadAll()
})
</script>

<style lang="scss" scoped>
.market-rankings-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.page-header {
  .header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .title-group {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .back-link {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #3B82F6;
    text-decoration: none;
    font-size: 0.85rem;

    &:hover {
      text-decoration: underline;
    }
  }

  .page-title {
    font-size: 1.375rem;
    font-weight: 700;
    color: #1F2937;
    margin: 0;
  }

  .market-select {
    width: 180px;

    :deep(.el-select__wrapper) {
      background: #FFFFFF;
      border-color: rgba(0, 0, 0, 0.12);
      color: #111827;
    }
  }
}

// 三列布局
.rankings-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
}

.card {
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
}

.ranking-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);

  .ranking-icon {
    font-size: 1.1rem;
  }

  .ranking-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #1F2937;
    margin: 0;
    flex: 1;
  }

  .count-tag {
    font-size: 0.7rem;
  }

  &.up {
    background: linear-gradient(135deg, rgba(245, 108, 108, 0.08) 0%, transparent 100%);
    border-bottom-color: rgba(245, 108, 108, 0.15);
  }

  &.down {
    background: linear-gradient(135deg, rgba(103, 194, 58, 0.08) 0%, transparent 100%);
    border-bottom-color: rgba(103, 194, 58, 0.15);
  }

  &.active {
    background: linear-gradient(135deg, rgba(230, 162, 60, 0.08) 0%, transparent 100%);
    border-bottom-color: rgba(230, 162, 60, 0.15);
  }
}

.ranking-loading, .ranking-empty {
  padding: 1.5rem 1.25rem;
}

.ranking-list {
  display: flex;
  flex-direction: column;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1.25rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  text-decoration: none;
  color: inherit;
  transition: background 0.15s;
  cursor: pointer;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: #F9FAFB;
  }
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
  background: rgba(15, 23, 42, 0.04);
  color: #6B7A99;

  &.gold {
    background: rgba(212, 175, 55, 0.3);
    color: #D4AF37;
  }

  &.silver {
    background: rgba(192, 192, 192, 0.2);
    color: #C0C0C0;
  }

  &.bronze {
    background: rgba(205, 127, 50, 0.2);
    color: #CD7F32;
  }
}

.asset-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;

  .asset-code {
    font-size: 0.8rem;
    font-weight: 600;
    color: #1F2937;
    white-space: nowrap;
  }

  .asset-name {
    font-size: 0.7rem;
    color: #6B7280;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.quote-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1px;

  .price {
    font-size: 0.85rem;
    font-weight: 700;
  }

  .change-pct {
    font-size: 0.75rem;
    font-weight: 600;
  }
}

.up { color: #f56c6c; }
.down { color: #67c23a; }
.flat { color: #909399; }

.disclaimer {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #6B7280;
  padding: 0.75rem 1rem;
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 8px;
  font-style: italic;
}
</style>


