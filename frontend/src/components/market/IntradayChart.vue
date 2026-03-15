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
      <v-chart class="intraday-echart" :option="chartOption" :autoresize="true" />
    </div>

    <div class="chart-empty" v-else>
      <el-empty :image-size="60">
        <template #description>
          <span class="empty-title">暂无分时走势数据</span>
          <span class="empty-sub">
            分时图需 Finnhub 高级套餐，实时行情请查看上方价格卡片
          </span>
        </template>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import {
  TooltipComponent,
  GridComponent,
  DataZoomComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getAssetIntraday } from '../../api/market'
import type { IntradayItem } from '../../types/market'

use([LineChart, BarChart, TooltipComponent, GridComponent, DataZoomComponent, CanvasRenderer])

const props = defineProps<{
  assetId: number
  date?: string
}>()

const items = ref<IntradayItem[]>([])
const loading = ref(false)
const error = ref(false)

const chartOption = computed(() => {
  const times = items.value.map(d => d.time)
  const prices = items.value.map(d => d.price)
  const avgPrices = items.value.map(d => d.avgPrice)

  // 判断涨跌
  const firstPrice = prices[0] || 0
  const lastPrice = prices[prices.length - 1] || firstPrice
  const lineColor = lastPrice >= firstPrice ? '#e85d5d' : '#16a34a'

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: 'rgba(0,0,0,0.08)',
      borderWidth: 1,
      borderRadius: 8,
      padding: [8, 12],
      textStyle: { color: '#1d1d1f', fontSize: 12, fontFamily: 'Inter, sans-serif' },
      boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
      formatter: (params: any[]) => {
        if (!params?.length) return ''
        const p = params[0]
        const avg = items.value[p.dataIndex]?.avgPrice?.toFixed(2)
        return `<div>
          <div style="color:#1F2937;font-weight:600">${p.name}</div>
          <div>价格：<span style="color:${lineColor};font-weight:600">${p.value?.toFixed(2)}</span></div>
          ${avg ? `<div>均价：<span style="color:#3B82F6">${avg}</span></div>` : ''}
        </div>`
      }
    },
    grid: { left: '10%', right: '4%', top: '8%', bottom: '15%' },
    xAxis: {
      type: 'category',
      data: times,
      boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(0,0,0,0.05)' } },
      axisTick: { show: false },
      axisLabel: { color: '#8e8e93', fontSize: 11, interval: Math.floor(times.length / 6) },
      splitLine: { show: false }
    },
    yAxis: {
      scale: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#8e8e93', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,0,0,0.03)', type: 'dashed' } }
    },
    dataZoom: [{
      type: 'inside',
      start: 0,
      end: 100
    }],
    series: [
      {
        name: '价格',
        type: 'line',
        data: prices,
        smooth: true,
        lineStyle: { color: lineColor, width: 2 },
        itemStyle: { color: lineColor },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: lineColor.replace(')', ', 0.3)').replace('rgb', 'rgba') },
              { offset: 1, color: lineColor.replace(')', ', 0)').replace('rgb', 'rgba') }
            ]
          }
        },
        showSymbol: false
      },
      {
        name: '均价',
        type: 'line',
        data: avgPrices,
        smooth: true,
        lineStyle: { color: '#3B82F6', width: 1, type: 'dashed' },
        itemStyle: { color: '#3B82F6' },
        showSymbol: false
      }
    ]
  }
})

const fetchData = async () => {
  loading.value = true
  error.value = false
  try {
    const res = await getAssetIntraday(props.assetId, props.date ? { date: props.date } : undefined)
    items.value = res.items
  } catch (e) {
    error.value = true
    items.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.assetId, fetchData)
onMounted(fetchData)
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



