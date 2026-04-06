<template>
  <div class="kline-chart-wrapper">
    <!-- 周期切换 -->
    <div class="chart-toolbar">
      <div class="interval-tabs">
        <button
          v-for="tab in intervalTabs"
          :key="tab.value"
          class="interval-btn"
          :class="{ active: currentInterval === tab.value }"
          @click="changeInterval(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>
      <span class="data-source-hint">数据来源：Tushare</span>
    </div>

    <!-- 加载状态-->
    <div class="chart-loading" v-if="loading">
      <el-skeleton :rows="5" animated />
      <p class="loading-text" v-if="loadingTooLong">数据加载中...</p>
    </div>

    <!-- 错误状态-->  
    <div class="chart-error" v-else-if="error">
      <el-empty :image-size="60">
        <template #image>
          <svg width="60" height="60" viewBox="0 0 24 24" fill="none">
            <path d="M3 17l4-8 4 4 4-6 4 10" stroke="#909399" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </template>
        <template #description>
          <span class="empty-title">K线数据加载失败</span>
          <span class="empty-sub">请检查网络连接后刷新重试</span>
        </template>
      </el-empty>
    </div>

    <!-- K线图 -->
    <div class="chart-container" v-else-if="klineData.length > 0">
      <div ref="chartRef" class="kline-echart"></div>
    </div>

    <div class="chart-empty" v-else>
      <el-empty :image-size="60">
        <template #description>
          <span class="empty-title">暂无历史K线数据</span>
          <span class="empty-sub">
            历史K线需 Tushare 高级套餐，实时行情请查看上方价格卡片
          </span>
        </template>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { getAssetKline } from '../../api/market'
import { loadLightweightCharts } from '@/utils/lightweight-charts-loader'
import type { AssetKlineItem } from '../../types/market'

interface KlineChartProps {
  assetId: number
  interval?: '1d' | '60m' | '15m'
  limit?: number
}

const props = withDefaults(defineProps<KlineChartProps>(), {
  interval: '1d',
  limit: 90
})

const currentInterval = ref(props.interval)
const klineData = ref<AssetKlineItem[]>([])
const loading = ref(false)
const error = ref(false)
const loadingTooLong = ref(false)
const chartRef = ref<HTMLDivElement | null>(null)
let loadingTimer: ReturnType<typeof setTimeout> | null = null
let resizeObserver: ResizeObserver | null = null
let chart: ReturnType<typeof createChart> | null = null
let candlesSeries: any = null
let volumesSeries: any = null
let requestSeq = 0
let lightweightCharts: Awaited<ReturnType<typeof loadLightweightCharts>> | null = null

const intervalTabs = [
  { label: '日K', value: '1d' },
  { label: '时K', value: '60m' },
  { label: '15m', value: '15m' }
]

const toUnixTime = (input: string) => {
  return Math.floor(new Date(input).getTime() / 1000)
}

const ensureChart = async () => {
  if (chart || !chartRef.value) return
  await nextTick()
  if (!chartRef.value) return
  lightweightCharts = lightweightCharts || await loadLightweightCharts()
  chart = lightweightCharts.createChart(chartRef.value, {
    layout: {
      background: { type: lightweightCharts.ColorType.Solid, color: 'transparent' },
      textColor: '#8e8e93'
    },
    grid: {
      vertLines: { color: 'rgba(0,0,0,0.03)' },
      horzLines: { color: 'rgba(0,0,0,0.03)' }
    },
    rightPriceScale: {
      borderColor: 'rgba(0,0,0,0.08)'
    },
    timeScale: {
      borderColor: 'rgba(0,0,0,0.08)',
      timeVisible: currentInterval.value !== '1d'
    },
    width: chartRef.value.clientWidth || 600,
    height: 450
  })

  candlesSeries = chart.addSeries(lightweightCharts.CandlestickSeries, {
    upColor: '#e85d5d',
    downColor: '#16a34a',
    borderVisible: false,
    wickUpColor: '#e85d5d',
    wickDownColor: '#16a34a'
  })

  volumesSeries = chart.addSeries(lightweightCharts.HistogramSeries, {
    color: 'rgba(59,130,246,0.4)',
    priceFormat: { type: 'volume' },
    priceScaleId: ''
  })
  volumesSeries.priceScale().applyOptions({
    scaleMargins: { top: 0.8, bottom: 0 }
  })

  resizeObserver = new ResizeObserver(() => {
    if (chart && chartRef.value) {
      chart.applyOptions({ width: chartRef.value.clientWidth || 600 })
    }
  })
  resizeObserver.observe(chartRef.value)
}

const renderChart = async () => {
  if (klineData.value.length === 0) return
  await ensureChart()
  if (!chart || !candlesSeries || !volumesSeries) return

  const candlesData = new Array(klineData.value.length)
  const volumesData = new Array(klineData.value.length)
  for (let i = 0; i < klineData.value.length; i++) {
    const item = klineData.value[i]
    const time = toUnixTime(item.time)
    const open = Number(item.open)
    const close = Number(item.close)
    candlesData[i] = {
      time,
      open,
      high: Number(item.high),
      low: Number(item.low),
      close
    }
    volumesData[i] = {
      time,
      value: Number(item.volume || 0),
      color: close >= open ? 'rgba(232,93,93,0.45)' : 'rgba(22,163,74,0.45)'
    }
  }

  chart.applyOptions({
    timeScale: {
      borderColor: 'rgba(0,0,0,0.08)',
      timeVisible: currentInterval.value !== '1d'
    }
  })
  candlesSeries.setData(candlesData)
  volumesSeries.setData(volumesData)
  chart.timeScale().fitContent()
}

const fetchKlineData = async () => {
  const seq = ++requestSeq
  loading.value = true
  error.value = false
  loadingTooLong.value = false

  if (loadingTimer) clearTimeout(loadingTimer)
  loadingTimer = setTimeout(() => {
    if (loading.value) loadingTooLong.value = true
  }, 3000)

  try {
    const res = await getAssetKline(props.assetId, {
      interval: currentInterval.value as any,
      limit: props.limit
    })
    if (seq !== requestSeq) return
    klineData.value = res.items
  } catch (e) {
    if (seq !== requestSeq) return
    error.value = true
    klineData.value = []
  } finally {
    if (seq !== requestSeq) return
    loading.value = false
    if (loadingTimer) clearTimeout(loadingTimer)
    if (!error.value && klineData.value.length > 0) {
      await nextTick()
      await renderChart()
    } else if (candlesSeries && volumesSeries) {
      candlesSeries.setData([])
      volumesSeries.setData([])
    }
  }
}

const changeInterval = (interval: string) => {
  currentInterval.value = interval as any
  fetchKlineData()
}

watch(() => props.assetId, () => {
  fetchKlineData()
})

watch(
  () => props.interval,
  (nextInterval) => {
    if (nextInterval && nextInterval !== currentInterval.value) {
      currentInterval.value = nextInterval
      fetchKlineData()
    }
  }
)

onMounted(() => {
  fetchKlineData()
})

onUnmounted(() => {
  if (loadingTimer) clearTimeout(loadingTimer)
  resizeObserver?.disconnect()
  resizeObserver = null
  chart?.remove()
  candlesSeries = null
  volumesSeries = null
  chart = null
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.kline-chart-wrapper {
  width: 100%;
  padding: $market-space-4 0;
}

.chart-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $market-space-4;
  padding: 0 $market-space-2;
}

.interval-tabs {
  display: flex;
  gap: $market-space-2;
  background: rgba(0, 0, 0, 0.02);
  padding: 4px;
  border-radius: $market-radius-segmented;
}

.interval-btn {
  padding: 6px 16px;
  border-radius: $market-radius-segmented-item;
  border: none;
  background: transparent;
  color: $market-text-secondary;
  font-size: $market-font-caption;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: rgba(0, 0, 0, 0.04);
    color: $market-text-primary;
  }

  &.active {
    background: $market-bg-soft;
    color: $market-accent;
    font-weight: 600;
    box-shadow: $market-shadow-sm;
  }
}

.data-source-hint {
  font-size: $market-font-mini;
  color: $market-text-tertiary;
  font-style: italic;
}

.chart-loading {
  padding: 16px;
}

.loading-text {
  text-align: center;
  color: #6B7280;
  font-size: 0.8rem;
  margin-top: 8px;
}

.chart-container {
  width: 100%;
}

.kline-echart {
  width: 100%;
  height: 450px;
  padding: $market-space-4;
}

.chart-error,
.chart-empty {
  padding: 40px;
  display: flex;
  justify-content: center;
}

:deep(.empty-title) {
  display: block;
  font-size: 0.875rem;
  color: #6B7280;
  margin-bottom: 4px;
}

:deep(.empty-sub) {
  display: block;
  font-size: 0.75rem;
  color: #9CA3AF;
  line-height: 1.5;
  max-width: 260px;
  text-align: center;
}
</style>




