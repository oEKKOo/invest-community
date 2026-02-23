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
      <span class="data-source-hint">数据来源：Finnhub</span>
    </div>

    <!-- 加载状态 -->
    <div class="chart-loading" v-if="loading">
      <el-skeleton :rows="5" animated />
      <p class="loading-text" v-if="loadingTooLong">数据加载中...</p>
    </div>

    <!-- 错误状态 -->
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
      <v-chart
        ref="chartRef"
        class="kline-echart"
        :option="chartOption"
        :autoresize="true"
      />
    </div>

    <div class="chart-empty" v-else>
      <el-empty :image-size="60">
        <template #description>
          <span class="empty-title">暂无历史K线数据</span>
          <span class="empty-sub">
            历史K线需要 Finnhub 高级套餐，实时行情请查看上方价格卡片
          </span>
        </template>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CandlestickChart, BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  LegendComponent,
  MarkLineComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getAssetKline } from '../../api/market'
import type { AssetKlineItem } from '../../types/market'

use([
  CandlestickChart, BarChart, LineChart,
  TitleComponent, TooltipComponent, GridComponent,
  DataZoomComponent, LegendComponent, MarkLineComponent,
  CanvasRenderer
])

const props = withDefaults(defineProps<{
  assetId: number
  interval?: '1d' | '60m' | '15m'
  limit?: number
}>(), {
  interval: '1d',
  limit: 200
})

const currentInterval = ref(props.interval)
const klineData = ref<AssetKlineItem[]>([])
const loading = ref(false)
const error = ref(false)
const loadingTooLong = ref(false)
const chartRef = ref()
let loadingTimer: ReturnType<typeof setTimeout> | null = null

const intervalTabs = [
  { label: '日K', value: '1d' },
  { label: '时K', value: '60m' },
  { label: '15分', value: '15m' }
]

// 数字格式化
const formatVol = (val: number) => {
  if (val >= 1e8) return `${(val / 1e8).toFixed(2)}亿`
  if (val >= 1e4) return `${(val / 1e4).toFixed(2)}万`
  return String(val)
}

// ECharts 配置
const chartOption = computed(() => {
  const times = klineData.value.map(d => {
    const t = new Date(d.time)
    if (currentInterval.value === '1d') {
      return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`
    }
    return `${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')} ${String(t.getHours()).padStart(2, '0')}:${String(t.getMinutes()).padStart(2, '0')}`
  })

  const ohlcv = klineData.value.map(d => [
    parseFloat(String(d.open)),
    parseFloat(String(d.close)),
    parseFloat(String(d.low)),
    parseFloat(String(d.high))
  ])

  const volumes = klineData.value.map(d => d.volume || 0)
  const upColors = klineData.value.map((d, i) =>
    parseFloat(String(d.close)) >= parseFloat(String(d.open)) ? '#f56c6c' : '#67c23a'
  )

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(10, 14, 26, 0.95)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#A0AABF', fontSize: 12 },
      formatter: (params: any[]) => {
        if (!params || !params[0]) return ''
        const d = klineData.value[params[0].dataIndex]
        if (!d) return ''
        const o = parseFloat(String(d.open)).toFixed(2)
        const h = parseFloat(String(d.high)).toFixed(2)
        const l = parseFloat(String(d.low)).toFixed(2)
        const c = parseFloat(String(d.close)).toFixed(2)
        const v = formatVol(d.volume || 0)
        return `<div style="line-height:1.8">
          <div style="color:#F0F4FF;font-weight:600">${params[0].name}</div>
          <div>开：<span style="color:#A78BFA">${o}</span></div>
          <div>高：<span style="color:#f56c6c">${h}</span></div>
          <div>低：<span style="color:#67c23a">${l}</span></div>
          <div>收：<span style="color:#F0F4FF;font-weight:600">${c}</span></div>
          <div>量：<span style="color:#6B7A99">${v}</span></div>
        </div>`
      }
    },
    axisPointer: {
      link: [{ xAxisIndex: 'all' }]
    },
    grid: [
      { left: '8%', right: '3%', top: '5%', height: '60%' },
      { left: '8%', right: '3%', top: '70%', height: '20%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: times,
        gridIndex: 0,
        scale: true,
        boundaryGap: false,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        axisTick: { show: false },
        axisLabel: {
          color: '#6B7A99',
          fontSize: 11,
          interval: Math.floor(times.length / 8)
        },
        splitLine: { show: false }
      },
      {
        type: 'category',
        data: times,
        gridIndex: 1,
        scale: true,
        boundaryGap: false,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        axisTick: { show: false },
        axisLabel: { show: false },
        splitLine: { show: false }
      }
    ],
    yAxis: [
      {
        scale: true,
        gridIndex: 0,
        splitNumber: 5,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#6B7A99', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#6B7A99',
          fontSize: 10,
          formatter: (v: number) => formatVol(v)
        },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: Math.max(0, 100 - Math.round(60 / klineData.value.length * 100)),
        end: 100
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        start: Math.max(0, 100 - Math.round(60 / klineData.value.length * 100)),
        end: 100,
        top: '93%',
        height: 20,
        borderColor: 'rgba(255,255,255,0.1)',
        backgroundColor: 'rgba(255,255,255,0.03)',
        fillerColor: 'rgba(124,58,237,0.1)',
        handleStyle: { color: '#7C3AED' },
        textStyle: { color: '#6B7A99' }
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ohlcv,
        itemStyle: {
          color: '#f56c6c',
          color0: '#67c23a',
          borderColor: '#f56c6c',
          borderColor0: '#67c23a'
        }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: (params: any) => upColors[params.dataIndex] || '#6B7A99',
          opacity: 0.7
        }
      }
    ]
  }
})

const fetchKlineData = async () => {
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
    klineData.value = res.items
  } catch (e) {
    error.value = true
    klineData.value = []
  } finally {
    loading.value = false
    if (loadingTimer) clearTimeout(loadingTimer)
  }
}

const changeInterval = (interval: string) => {
  currentInterval.value = interval as any
  fetchKlineData()
}

watch(() => props.assetId, () => {
  fetchKlineData()
})

onMounted(() => {
  fetchKlineData()
})

onUnmounted(() => {
  if (loadingTimer) clearTimeout(loadingTimer)
})
</script>

<style lang="scss" scoped>
.kline-chart-wrapper {
  width: 100%;
}

.chart-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.interval-tabs {
  display: flex;
  gap: 4px;
}

.interval-btn {
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: transparent;
  color: #6B7A99;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.06);
    color: #A0AABF;
  }

  &.active {
    background: rgba(124, 58, 237, 0.2);
    border-color: rgba(124, 58, 237, 0.4);
    color: #A78BFA;
    font-weight: 600;
  }
}

.data-source-hint {
  font-size: 0.7rem;
  color: #6B7A99;
}

.chart-loading {
  padding: 16px;
}

.loading-text {
  text-align: center;
  color: #6B7A99;
  font-size: 0.8rem;
  margin-top: 8px;
}

.chart-container {
  width: 100%;
}

.kline-echart {
  width: 100%;
  height: 400px;
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
  color: #A0AABF;
  margin-bottom: 4px;
}

:deep(.empty-sub) {
  display: block;
  font-size: 0.75rem;
  color: #6B7A99;
  line-height: 1.5;
  max-width: 260px;
  text-align: center;
}
</style>
