<template>
  <span class="quote-tag" :class="colorClass">
    <span class="price" v-if="price !== null">{{ formatPrice(price) }}</span>
    <span class="change-pct" v-if="changePct !== null">{{ formatChangePct(changePct) }}</span>
    <span class="loading" v-if="price === null && !noData">—</span>
    <span class="no-data" v-if="noData">暂无行情</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  price?: string | number | null
  changePct?: string | number | null
  noData?: boolean
}>()

const priceNum = computed(() => {
  if (props.price === null || props.price === undefined) return null
  return parseFloat(String(props.price))
})

const changePctNum = computed(() => {
  if (props.changePct === null || props.changePct === undefined) return null
  return parseFloat(String(props.changePct))
})

const colorClass = computed(() => {
  if (changePctNum.value === null) return 'flat'
  if (changePctNum.value > 0) return 'up'
  if (changePctNum.value < 0) return 'down'
  return 'flat'
})

const formatPrice = (val: string | number | null) => {
  if (val === null || val === undefined) return '—'
  return parseFloat(String(val)).toFixed(2)
}

const formatChangePct = (val: string | number | null) => {
  if (val === null || val === undefined) return ''
  const num = parseFloat(String(val))
  const sign = num > 0 ? '+' : ''
  return `${sign}${num.toFixed(2)}%`
}
</script>

<style lang="scss" scoped>
.quote-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.01em;

  &.up {
    color: #f56c6c;
    background: rgba(245, 108, 108, 0.1);
    border: 1px solid rgba(245, 108, 108, 0.2);
  }

  &.down {
    color: #67c23a;
    background: rgba(103, 194, 58, 0.1);
    border: 1px solid rgba(103, 194, 58, 0.2);
  }

  &.flat {
    color: #909399;
    background: rgba(144, 147, 153, 0.1);
    border: 1px solid rgba(144, 147, 153, 0.2);
  }

  .price {
    font-size: 0.8rem;
  }

  .change-pct {
    font-size: 0.7rem;
    opacity: 0.9;
  }

  .loading, .no-data {
    color: #909399;
    font-size: 0.7rem;
  }
}
</style>
