<template>
  <span 
    class="asset-chip"
    :class="[marketClass, { clickable: !!assetId }]"
    @click="handleClick"
  >
    <span class="chip-market" v-if="market">{{ marketLabel }}</span>
    <span class="chip-code">{{ code }}</span>
    <span class="chip-name" v-if="name">{{ name }}</span>
    <QuoteTag
      v-if="showQuote && (price !== undefined || changePct !== undefined)"
      :price="price"
      :changePct="changePct"
      class="chip-quote"
    />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import * as QuoteTag from './QuoteTag.vue'

const props = defineProps<{
  assetId?: number
  code: string
  name?: string
  market?: string
  assetType?: string
  price?: string | number | null
  changePct?: string | number | null
  showQuote?: boolean
}>()

const router = useRouter()

const marketLabel = computed(() => {
  const map: Record<string, string> = {
    SH: 'A股', SZ: 'A股', HK: '港股', US: '美股',
    'A股': 'A股', '港股': '港股', '美股': '美股'
  }
  return props.market ? (map[props.market] || props.market) : ''
})

const marketClass = computed(() => {
  const m = props.market?.toUpperCase()
  if (m === 'SH' || m === 'SZ') return 'market-a'
  if (m === 'HK') return 'market-hk'
  if (m === 'US') return 'market-us'
  return ''
})

const handleClick = () => {
  if (props.assetId) {
    router.push(`/assets/${props.assetId}`)
  }
}
</script>

<style lang="scss" scoped>
.asset-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #A0AABF;
  transition: all 0.2s ease;
  cursor: default;

  &.clickable {
    cursor: pointer;

    &:hover {
      background: rgba(124, 58, 237, 0.12);
      border-color: rgba(124, 58, 237, 0.3);
      color: #A78BFA;
    }
  }

  &.market-a {
    .chip-market {
      color: #f56c6c;
      background: rgba(245, 108, 108, 0.1);
    }
  }

  &.market-hk {
    .chip-market {
      color: #F59E0B;
      background: rgba(245, 158, 11, 0.1);
    }
  }

  &.market-us {
    .chip-market {
      color: #60A5FA;
      background: rgba(96, 165, 250, 0.1);
    }
  }

  .chip-market {
    font-size: 0.65rem;
    font-weight: 600;
    padding: 1px 4px;
    border-radius: 3px;
    line-height: 1.2;
  }

  .chip-code {
    font-weight: 600;
    color: #E2E8F0;
  }

  .chip-name {
    color: #A0AABF;
    max-width: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chip-quote {
    margin-left: 2px;
  }
}
</style>
