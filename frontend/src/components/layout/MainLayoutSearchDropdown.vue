<template>
  <div class="search-dropdown">
    <div class="search-dropdown-section search-primary-action" @mousedown.prevent="$emit('primarySearch')">
      <span class="primary-label">搜索</span>
      <span class="primary-keyword">“{{ searchQuery }}”</span>
    </div>

    <div v-if="searchLoading" class="search-dropdown-loading">
      正在为你查找相关内容...
    </div>

    <template v-else>
      <div
        v-if="hotKeywords.length && !searchQuery.trim()"
        class="search-dropdown-section"
      >
        <div class="section-title">热门搜索</div>
        <div class="hot-list">
          <button
            v-for="word in hotKeywords"
            :key="word"
            class="hot-item"
            @mousedown.prevent="$emit('hotKeyword', word)"
          >
            {{ word }}
          </button>
        </div>
      </div>

      <div
        v-if="searchResults.posts.items.length"
        class="search-dropdown-section"
      >
        <div class="section-title">
          帖子
          <span class="count">共 {{ searchResults.posts.total }} 条</span>
        </div>
        <ul class="suggest-list">
          <li
            v-for="post in searchResults.posts.items"
            :key="post.id"
            class="suggest-item"
            @mousedown.prevent="$emit('goPost', post.id)"
          >
            <div class="suggest-main">
              <span class="suggest-title">{{ post.title }}</span>
              <span class="suggest-meta">{{ post.authorName }}</span>
            </div>
          </li>
        </ul>
      </div>

      <div
        v-if="searchResults.assets.items.length"
        class="search-dropdown-section"
      >
        <div class="section-title">
          资产
          <span class="count">共 {{ searchResults.assets.total }} 条</span>
        </div>
        <ul class="suggest-list">
          <li
            v-for="asset in searchResults.assets.items"
            :key="asset.id"
            class="suggest-item"
            @mousedown.prevent="$emit('goAsset', asset.id)"
          >
            <div class="suggest-main">
              <span class="suggest-title">{{ asset.code }}</span>
              <span class="suggest-meta">{{ asset.name }}</span>
            </div>
          </li>
        </ul>
      </div>

      <div
        v-if="searchResults.portfolios.items.length"
        class="search-dropdown-section"
      >
        <div class="section-title">
          组合
          <span class="count">共 {{ searchResults.portfolios.total }} 条</span>
        </div>
        <ul class="suggest-list">
          <li
            v-for="p in searchResults.portfolios.items"
            :key="p.id"
            class="suggest-item"
            @mousedown.prevent="$emit('goPortfolio', p.id)"
          >
            <div class="suggest-main">
              <span class="suggest-title">{{ p.title }}</span>
              <span class="suggest-meta">{{ p.userName }}</span>
            </div>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { GlobalSearchResult } from '@/api/search'

defineProps<{
  searchQuery: string
  searchLoading: boolean
  hotKeywords: string[]
  searchResults: GlobalSearchResult
}>()

defineEmits<{
  primarySearch: []
  hotKeyword: [word: string]
  goPost: [id: number]
  goAsset: [id: number]
  goPortfolio: [id: number]
}>()
</script>

<style lang="scss" scoped>
.search-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: $apple-bg-soft;
  backdrop-filter: $apple-glass-blur;
  -webkit-backdrop-filter: $apple-glass-blur;
  border-radius: $apple-radius-md;
  border: 1px solid $apple-border-light;
  box-shadow: $apple-shadow-lg;
  padding: $apple-space-3;
  z-index: 20;
}

.search-dropdown-section {
  padding: 0.35rem 0.25rem;

  & + & {
    border-top: 1px solid #f3f4f6;
  }
}

.search-primary-action {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    background: #f3f4ff;
  }
}

.primary-label {
  font-size: 0.78rem;
  color: #6b7280;
}

.primary-keyword {
  font-size: 0.8rem;
  color: #111827;
  font-weight: 500;
}

.search-dropdown-loading {
  padding: 0.4rem 0.6rem;
  font-size: 0.78rem;
  color: #9ca3af;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.78rem;
  color: #6b7280;
  margin-bottom: 0.25rem;

  .count {
    font-size: 0.72rem;
    color: #9ca3af;
  }
}

.hot-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.hot-item {
  border-radius: 999px;
  border: none;
  padding: 0.12rem 0.6rem;
  font-size: 0.78rem;
  background: #f3f4f6;
  color: #4b5563;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    background: #e5e7eb;
  }
}

.suggest-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.suggest-item {
  padding: 0.3rem 0.4rem;
  border-radius: 6px;
  cursor: pointer;
  transition: $transition-all;

  &:hover {
    background: #f3f4ff;
  }
}

.suggest-main {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}

.suggest-title {
  font-size: 0.8rem;
  color: #111827;
  font-weight: 500;
}

.suggest-meta {
  font-size: 0.72rem;
  color: #9ca3af;
}
</style>
