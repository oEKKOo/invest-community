<template>
  <div class="asset-select">
    <div class="selected-list" v-if="selectedAssets.length > 0">
      <div
        v-for="asset in selectedAssets"
        :key="asset.id"
        class="selected-tag"
      >
        <span class="tag-code">{{ asset.code }}</span>
        <span class="tag-name">{{ asset.name }}</span>
        <button class="remove-btn" @click="removeAsset(asset.id)" type="button">×</button>
      </div>
    </div>

    <el-select
      v-model="inputValue"
      filterable
      remote
      :remote-method="searchAssets"
      :loading="searching"
      placeholder="搜索并关联标的（代码/名称）..."
      value-key="id"
      clearable
      @change="handleSelect"
      class="search-select"
    >
      <el-option
        v-for="item in searchResults"
        :key="item.id"
        :label="`${item.code} ${item.name}`"
        :value="item"
      >
        <div class="option-item">
          <span class="opt-code">{{ item.code }}</span>
          <span class="opt-name">{{ item.name }}</span>
          <el-tag size="small" :type="getMarketTagType(item.market)" class="opt-market">
            {{ item.market || '—' }}
          </el-tag>
          <span class="opt-type">{{ item.asset_type }}</span>
        </div>
      </el-option>
      <template #empty>
        <div class="search-empty">
          <span v-if="searching">搜索中...</span>
          <span v-else-if="searchQuery.length > 0">未找到相关标的</span>
          <span v-else>输入代码或名称搜索</span>
        </div>
      </template>
    </el-select>

    <p class="asset-hint" v-if="maxCount > 0">
      最多关联 {{ maxCount }} 个标的（已选 {{ selectedAssets.length }}）
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { getAssetsWithQuote } from '../../api/market'
  
interface SimpleAsset {
  id: number
  code: string
  name: string
  asset_type: string
  market?: string
}

const props = withDefaults(defineProps<{
  modelValue: number[]
  maxCount?: number
}>(), {
  maxCount: 5
})

const emit = defineEmits<{
  (e: 'update:modelValue', ids: number[]): void
}>()

const inputValue = ref<SimpleAsset | null>(null)
const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref<SimpleAsset[]>([])
const selectedAssets = ref<SimpleAsset[]>([])

// 搜索资产
const searchAssets = async (query: string) => {
  searchQuery.value = query
  if (!query || query.length < 1) {
    searchResults.value = []
    return
  }
  searching.value = true
  try {
    const res = await getAssetsWithQuote({ q: query, pageSize: 10 })
    searchResults.value = res.items.map(item => ({
      id: item.id,
      code: item.code,
      name: item.name,
      asset_type: item.asset_type,
      market: item.market
    }))
  } catch {
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

// 选择资产
const handleSelect = (asset: SimpleAsset | null) => {
  if (!asset) return

  // 检查是否已存在
  if (selectedAssets.value.some(a => a.id === asset.id)) {
    inputValue.value = null
    return
  }

  // 检查上限
  if (props.maxCount > 0 && selectedAssets.value.length >= props.maxCount) {
    inputValue.value = null
    return
  }

  selectedAssets.value.push(asset)
  emit('update:modelValue', selectedAssets.value.map(a => a.id))
  inputValue.value = null
  searchResults.value = []
}

// 移除资产
const removeAsset = (id: number) => {
  selectedAssets.value = selectedAssets.value.filter(a => a.id !== id)
  emit('update:modelValue', selectedAssets.value.map(a => a.id))
}

const getMarketTagType = (market?: string) => {
  const m = market?.toUpperCase()
  if (m === 'SH' || m === 'SZ') return 'danger'
  if (m === 'HK') return 'warning'
  if (m === 'US') return 'primary'
  return 'info'
}

// 同步外部 modelValue（例如重置时）
watch(() => props.modelValue, (ids) => {
  if (ids.length === 0) {
    selectedAssets.value = []
  }
})
</script>

<style lang="scss" scoped>
.asset-select {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.selected-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.selected-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px 4px 10px;
  background: rgba(124, 58, 237, 0.15);
  border: 1px solid rgba(124, 58, 237, 0.3);
  border-radius: 8px;
  font-size: 0.8rem;

  .tag-code {
    font-weight: 700;
    color: #A78BFA;
  }

  .tag-name {
    color: #A0AABF;
  }

  .remove-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: #6B7A99;
    font-size: 1rem;
    line-height: 1;
    padding: 0 0 0 2px;
    transition: color 0.2s;

    &:hover {
      color: #f56c6c;
    }
  }
}

.search-select {
  width: 100%;

  :deep(.el-select__wrapper) {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.1);
    color: #F0F4FF;
  }

  :deep(.el-select__placeholder) {
    color: #6B7A99;
  }
}

.option-item {
  display: flex;
  align-items: center;
  gap: 8px;

  .opt-code {
    font-weight: 700;
    color: #E2E8F0;
    font-size: 0.875rem;
    min-width: 60px;
  }

  .opt-name {
    flex: 1;
    color: #A0AABF;
    font-size: 0.8rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .opt-market {
    font-size: 0.65rem;
    padding: 1px 4px;
  }

  .opt-type {
    font-size: 0.7rem;
    color: #6B7A99;
  }
}

.search-empty {
  padding: 1rem;
  text-align: center;
  color: #6B7A99;
  font-size: 0.85rem;
}

.asset-hint {
  font-size: 0.72rem;
  color: #6B7A99;
  margin: 0;
}
</style>
