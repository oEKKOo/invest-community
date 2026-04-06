<template>
  <div class="search-page">
    <div class="search-header">
      <h2>全局搜索</h2>
      <p class="subtitle">搜索帖子、资产和投资组合</p>

      <div class="search-input-wrap">
        <el-input
          v-model="keyword"
          placeholder="输入关键词，按回车搜索"
          clearable
          @keyup.enter.native="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <div class="search-meta">
        <div class="tabs">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            class="tab-btn"
            :class="{ active: currentType === tab.value }"
            @click="changeType(tab.value)"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="hot-keywords" v-if="hotKeywords.length">
          <span class="label">热门搜索：</span>
          <button
            v-for="item in hotKeywords"
            :key="item"
            class="hot-chip"
            @click="useHotKeyword(item)"
          >
            {{ item }}
          </button>
        </div>
      </div>
    </div>

    <div class="search-body">
      <el-empty
        v-if="!loading && !keyword"
        description="请输入关键词开始搜索"
      />

      <el-skeleton v-else-if="loading" :rows="4" animated />

      <template v-else>
        <!-- 全部 / 帖子结果 -->
        <section v-if="showSection('post')" class="result-section">
          <div class="section-header">
            <h3>帖子</h3>
            <span class="count" v-if="results.posts.total">
              共 {{ results.posts.total }} 条
            </span>
          </div>

          <el-empty
            v-if="!results.posts.items.length"
            description="暂无相关帖子"
          />

          <div v-else class="post-list">
            <div
              v-for="post in results.posts.items"
              :key="post.id"
              class="post-card"
              @click="goPost(post.id)"
            >
              <h4 class="title">{{ post.title }}</h4>
              <div v-if="post.thumbUrl" class="post-thumb">
                <img :src="post.thumbUrl" alt="" loading="lazy" decoding="async" />
              </div>
              <p class="excerpt">
                {{ post.excerpt || post.content }}
              </p>
              <div class="meta">
                <span class="author">{{ post.authorName }}</span>
                <span class="dot">·</span>
                <span class="time">{{ formatDate(post.createdAt) }}</span>
                <span class="dot">·</span>
                <span class="stat">👍 {{ post.likes }}</span>
                <span class="dot">·</span>
                <span class="stat">💬 {{ post.comments }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 全部 / 资产结果 -->
        <section v-if="showSection('asset')" class="result-section">
          <div class="section-header">
            <h3>资产</h3>
            <span class="count" v-if="results.assets.total">
              共 {{ results.assets.total }} 条
            </span>
          </div>

          <el-empty
            v-if="!results.assets.items.length"
            description="暂无相关资产"
          />

          <div v-else class="asset-list">
            <div
              v-for="asset in results.assets.items"
              :key="asset.id"
              class="asset-row"
              @click="goAsset(asset.id)"
            >
              <div class="asset-main">
                <span class="code">{{ asset.code }}</span>
                <span class="name">{{ asset.name }}</span>
              </div>
              <div class="asset-tags">
                <el-tag size="small" type="info">
                  {{ asset.asset_type }}
                </el-tag>
                <el-tag
                  v-if="asset.market"
                  size="small"
                  class="market-tag"
                >
                  {{ asset.market }}
                </el-tag>
              </div>
            </div>
          </div>
        </section>

        <!-- 全部 / 组合结果 -->
        <section v-if="showSection('portfolio')" class="result-section">
          <div class="section-header">
            <h3>投资组合</h3>
            <span class="count" v-if="results.portfolios.total">
              共 {{ results.portfolios.total }} 条
            </span>
          </div>

          <el-empty
            v-if="!results.portfolios.items.length"
            description="暂无相关组合"
          />

          <div v-else class="portfolio-list">
            <div
              v-for="p in results.portfolios.items"
              :key="p.id"
              class="portfolio-card"
              @click="goPortfolio(p.id)"
            >
              <h4 class="title">{{ p.title }}</h4>
              <p class="owner">{{ p.userName }}</p>
              <p class="desc">
                {{ p.description }}
              </p>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { globalSearch, type GlobalSearchType, type GlobalSearchResult } from '../api/search'
import { preloadAssetDetailCharts } from '../utils/preload'

const route = useRoute()
const router = useRouter()

const keyword = ref<string>((route.query.q as string) || '')
const currentType = ref<GlobalSearchType>((route.query.type as GlobalSearchType) || 'all')
const loading = ref(false)

const results = reactive<GlobalSearchResult>({
  posts: { items: [], total: 0 },
  assets: { items: [], total: 0 },
  portfolios: { items: [], total: 0 }
})

const tabs: { label: string; value: GlobalSearchType }[] = [
  { label: '全部', value: 'all' },
  { label: '帖子', value: 'post' },
  { label: '资产', value: 'asset' },
  { label: '组合', value: 'portfolio' }
]

// 简单热门搜索（静态示例，可后续接后台埋点）
const hotKeywords = ref<string[]>(['AAPL', '平安银行', '科技ETF', '价值投资'])

const fetchData = async () => {
  const q = keyword.value.trim()
  if (!q) {
    results.posts = { items: [], total: 0 }
    results.assets = { items: [], total: 0 }
    results.portfolios = { items: [], total: 0 }
    return
  }

  loading.value = true
  try {
    const data = await globalSearch({ q, type: currentType.value })
    results.posts = data.posts
    results.assets = data.assets
    results.portfolios = data.portfolios
  } catch (e) {
    results.posts = { items: [], total: 0 }
    results.assets = { items: [], total: 0 }
    results.portfolios = { items: [], total: 0 }
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  router.replace({
    name: 'Search',
    query: {
      q: keyword.value.trim(),
      type: currentType.value
    }
  })
  fetchData()
}

const changeType = (type: GlobalSearchType) => {
  if (currentType.value === type) return
  currentType.value = type
  handleSearch()
}

const useHotKeyword = (word: string) => {
  keyword.value = word
  handleSearch()
}

const showSection = (section: GlobalSearchType) => {
  if (currentType.value === 'all') return true
  return currentType.value === section
}

const goPost = (id: number) => {
  router.push({ name: 'PostDetail', params: { id } })
}

const goAsset = (id: number) => {
  preloadAssetDetailCharts()
  router.push({ name: 'AssetDetail', params: { assetId: String(id) } })
}

const goPortfolio = (id: number) => {
  router.push({ name: 'PortfolioDetail', params: { id } })
}

const formatDate = (iso: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

// 当路由参数变化时，同步关键字与类型
watch(
  () => route.query,
  (q) => {
    if (typeof q.q === 'string') {
      keyword.value = q.q
    }
    if (typeof q.type === 'string') {
      currentType.value = q.type as GlobalSearchType
    }
  }
)

onMounted(() => {
  if (keyword.value.trim()) {
    fetchData()
  }
})
</script>

<style scoped lang="scss">
.search-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.search-header {
  padding: 1rem 1.25rem 0.5rem;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);

  h2 {
    margin: 0;
    font-size: 1.3rem;
    font-weight: 600;
    color: #111827;
  }

  .subtitle {
    margin: 0.25rem 0 0.75rem;
    font-size: 0.85rem;
    color: #6b7280;
  }
}

.search-input-wrap {
  max-width: 520px;
}

.search-meta {
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.tabs {
  display: flex;
  gap: 0.4rem;
}

.tab-btn {
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  padding: 0.18rem 0.75rem;
  font-size: 0.8rem;
  background: #f9fafb;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.15s ease;

  &.active {
    background: #1d4ed8;
    color: #ffffff;
    border-color: #1d4ed8;
    box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.35);
  }

  &:hover:not(.active) {
    background: #eef2ff;
    border-color: #c7d2fe;
  }
}

.hot-keywords {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.3rem;

  .label {
    font-size: 0.76rem;
    color: #9ca3af;
  }
}

.hot-chip {
  border-radius: 999px;
  border: none;
  padding: 0.12rem 0.6rem;
  font-size: 0.78rem;
  background: #f3f4f6;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #e5e7eb;
  }
}

.search-body {
  padding: 0 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.result-section {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 1rem 1.25rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;

  h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: #111827;
  }

  .count {
    font-size: 0.78rem;
    color: #9ca3af;
  }
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.post-card {
  padding: 0.75rem 0.5rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #f9fafb;
  }

  .title {
    margin: 0 0 0.25rem;
    font-size: 0.95rem;
    font-weight: 600;
    color: #111827;
  }

  .post-thumb {
    margin: 0.35rem 0 0.4rem;
    border-radius: 8px;
    overflow: hidden;
    max-height: 140px;
    background: #f3f4f6;

    img {
      width: 100%;
      display: block;
      object-fit: cover;
      max-height: 140px;
    }
  }

  .excerpt {
    margin: 0;
    font-size: 0.82rem;
    color: #6b7280;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .meta {
    margin-top: 0.35rem;
    font-size: 0.75rem;
    color: #9ca3af;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .author {
    color: #4b5563;
  }

  .dot {
    color: #d1d5db;
  }

  .stat {
    color: #6b7280;
  }
}

.asset-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.asset-row {
  padding: 0.55rem 0.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #f9fafb;
  }
}

.asset-main {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;

  .code {
    font-weight: 600;
    color: #111827;
    font-size: 0.9rem;
  }

  .name {
    font-size: 0.82rem;
    color: #6b7280;
  }
}

.asset-tags {
  display: flex;
  gap: 0.25rem;
}

.market-tag {
  text-transform: uppercase;
}

.portfolio-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.portfolio-card {
  padding: 0.75rem 0.5rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #f9fafb;
  }

  .title {
    margin: 0 0 0.25rem;
    font-size: 0.95rem;
    font-weight: 600;
    color: #111827;
  }

  .owner {
    margin: 0 0 0.25rem;
    font-size: 0.82rem;
    color: #6b7280;
  }

  .desc {
    margin: 0;
    font-size: 0.8rem;
    color: #6b7280;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}
</style>

