<template>
  <div class="quote-mini" v-if="quote">
    <span class="price" :class="colorClass">{{ formatPrice(quote.price) }}</span>
    <span class="change-pct" :class="colorClass">{{ formatChangePct(quote.changePct) }}</span>
    <span class="quote-time" v-if="showTime">{{ formatTime(quote.quoteTime) }}</span>
    <el-tag v-if="quote.isStale" size="small" type="warning" class="stale-tag">数据可能不是最新</el-tag>
  </div>
  <div class="quote-mini empty" v-else>
    <span class="no-data">暂无行情</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AssetQuote } from '../../types/market'

const props = defineProps<{
  quote?: AssetQuote | null
  showTime?: boolean
}>()

const changePctNum = computed(() => {
  if (!props.quote?.changePct) return null
  return parseFloat(String(props.quote.changePct))
})

const colorClass = computed(() => {
  if (changePctNum.value === null) return 'flat'
  if (changePctNum.value > 0) return 'up'
  if (changePctNum.value < 0) return 'down'
  return 'flat'
})

const formatPrice = (val: string | number | null | undefined) => {
  if (val === null || val === undefined) return '—'
  return parseFloat(String(val)).toFixed(2)
}

const formatChangePct = (val: string | number | null | undefined) => {
  if (val === null || val === undefined) return ''
  const num = parseFloat(String(val))
  const sign = num > 0 ? '+' : ''
  return `${sign}${num.toFixed(2)}%`
}

const formatTime = (timeStr: string | null | undefined) => {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${min}`
}
</script>

<style lang="scss" scoped>
.quote-mini {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;

  &.empty {
    .no-data {
      color: #909399;
      font-size: 0.75rem;
    }
  }

  .price {
    font-weight: 600;
  }

  .change-pct {
    font-size: 0.75rem;
    font-weight: 500;
  }

  .up { color: #f56c6c; }
  .down { color: #67c23a; }
  .flat { color: #909399; }

  .quote-time {
    font-size: 0.7rem;
    color: #6B7A99;
  }

  .stale-tag {
    font-size: 0.65rem;
  }
}
</style>
