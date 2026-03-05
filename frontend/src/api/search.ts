import { get } from './index'
import type { Post, Asset, Portfolio } from '../types'

export type GlobalSearchType = 'all' | 'post' | 'asset' | 'portfolio'

export interface GlobalSearchResultSection<T> {
  items: T[]
  total: number
}

export interface GlobalSearchResult {
  posts: GlobalSearchResultSection<Post>
  assets: GlobalSearchResultSection<Asset>
  portfolios: GlobalSearchResultSection<Portfolio>
}

export interface GlobalSearchParams {
  q: string
  type?: GlobalSearchType
}

export const globalSearch = (params: GlobalSearchParams) => {
  return get<GlobalSearchResult>('/search/', {
    params: {
      q: params.q,
      type: params.type || 'all'
    }
  })
}

