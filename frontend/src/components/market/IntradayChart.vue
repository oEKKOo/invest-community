<template>
  <div class="intraday-chart-wrapper">
    <div class="chart-loading" v-if="loading">
      <el-skeleton :rows="4" animated />
    </div>

    <div class="chart-error" v-else-if="error">
      <el-empty :image-size="60">
        <template #description>
          <span class="empty-title">分时数据加载失败</span>
          <span class="empty-sub">请检查网络连接后刷新重试</span>
        </template>
      </el-empty>
    </div>

    <div class="chart-container" v-else-if="items.length > 0">
      <div ref="chartRef" class="intraday-echart"></div>
    </div>

    <div class="chart-empty" v-else>
      <el-empty :image-size="60">
        <template #description>
          <span class="empty-title">暂无分时走势数据</span>
          <span class="empty-sub">
            分时图需 Tushare 高级套餐，实时行情请查看上方价格卡片
          </span>
        </template>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { getAssetIntraday } from '../../api/market'
import { loadLightweightCharts } from '@/utils/chart-loader'
import type { IntradayItem } from '../../types/market'

const props = defineProps<{
  assetId: number
  date?: string
}>()

const items = ref<IntradayItem[]>([])
const loading = ref(false)
const error = ref(false)
const chartRef = ref<HTMLDivElement | null>(null)
let chart: ReturnType<typeof createChart> | null = null
let resizeObserver: ResizeObserver | null = null
let priceSeries: any = null
let avgSeries: any = null
let requestSeq = 0
let lightweightCharts: Awaited<ReturnType<typeof loadLightweightCharts>> | null = null

const toUnixTime = (input: string) => Math.floor(new Date(input).getTime() / 1000)

const ensureChart = async (lineColor: string) => {
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
    rightPriceScale: { borderColor: 'rgba(0,0,0,0.08)' },
    timeScale: { borderColor: 'rgba(0,0,0,0.08)', timeVisible: true },
    width: chartRef.value.clientWidth || 600,
    height: 350
  })

  priceSeries = chart.addSeries(lightweightCharts.AreaSeries, {
    lineColor,
    topColor: lineColor === '#e85d5d' ? 'rgba(232,93,93,0.2)' : 'rgba(22,163,74,0.2)',
    bottomColor: 'rgba(255,255,255,0)',
    lineWidth: 2
  })

  avgSeries = chart.addSeries(lightweightCharts.LineSeries, {
    color: '#3B82F6',
    lineWidth: 1
  })
  resizeObserver = new ResizeObserver(() => {
    if (chart && chartRef.value) {
      chart.applyOptions({ width: chartRef.value.clientWidth || 600 })
    }
  })
  resizeObserver.observe(chartRef.value)
}

const renderChart = async () => {
  if (items.value.length === 0) return
  const firstPrice = Number(items.value[0]?.price || 0)
  const lastPrice = Number(items.value[items.value.length - 1]?.price || firstPrice)
  const lineColor = lastPrice >= firstPrice ? '#e85d5d' : '#16a34a'

  await ensureChart(lineColor)
  if (!chart || !priceSeries || !avgSeries) return

  // 根据涨跌更新主线颜色
  priceSeries.applyOptions({
    lineColor,
    topColor: lineColor === '#e85d5d' ? 'rgba(232,93,93,0.2)' : 'rgba(22,163,74,0.2)'
  })

  const priceData = new Array(items.value.length)
  const avgData = new Array(items.value.length)
  for (let i = 0; i < items.value.length; i++) {
    const item = items.value[i]
    const time = toUnixTime(item.time)
    const price = Number(item.price)
    priceData[i] = { time, value: price }
    avgData[i] = { time, value: Number(item.avgPrice || item.price) }
  }

  priceSeries.setData(priceData)
  avgSeries.setData(avgData)
  chart.timeScale().fitContent()
}

const fetchData = async () => {
  const seq = ++requestSeq
  loading.value = true
  error.value = false
  try {
    const res = await getAssetIntraday(props.assetId, props.date ? { date: props.date } : undefined)
    if (seq !== requestSeq) return
    items.value = res.items
  } catch (e) {
    if (seq !== requestSeq) return
    error.value = true
    items.value = []
  } finally {
    if (seq !== requestSeq) return
    loading.value = false
    if (!error.value && items.value.length > 0) {
      await nextTick()
      await renderChart()
    } else if (priceSeries && avgSeries) {
      priceSeries.setData([])
      avgSeries.setData([])
    }
  }
}

watch(() => props.assetId, fetchData)
watch(() => props.date, fetchData)
onMounted(fetchData)

onUnmounted(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  chart?.remove()
  priceSeries = null
  avgSeries = null
  chart = null
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.intraday-chart-wrapper {
  width: 100%;
  padding: $market-space-4 0;
}

.chart-loading {
  padding: $market-space-4;
}

.chart-container {
  width: 100%;
}

.intraday-echart {
  width: 100%;
  height: 350px;
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



