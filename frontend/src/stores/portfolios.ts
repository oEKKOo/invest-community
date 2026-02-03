import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Portfolio, PaginatedResponse } from '@/types'
import * as portfoliosApi from '@/api/portfolios'
import * as likesApi from '@/api/likes'

export const usePortfoliosStore = defineStore('portfolios', () => {
  // State
  const portfolios = ref<Portfolio[]>([])
  const currentPortfolio = ref<Portfolio | null>(null)
  const topPortfolios = ref<Portfolio[]>([])
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    pageSize: 20,
    total: 0
  })

  // Actions
  const fetchPortfolios = async (params?: portfoliosApi.GetPortfoliosParams) => {
    loading.value = true
    try {
      const response = await portfoliosApi.getPortfolios(params)
      portfolios.value = response.items
      pagination.value = {
        page: response.page,
        pageSize: response.pageSize,
        total: response.total
      }
      return response
    } catch (error) {
      console.error('Failed to fetch portfolios:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchTopPortfolios = async (limit?: number) => {
    try {
      const response = await portfoliosApi.getTopPortfolios(limit)
      topPortfolios.value = response.items
      return response
    } catch (error) {
      console.error('Failed to fetch top portfolios:', error)
      throw error
    }
  }

  const fetchPortfolio = async (id: number) => {
    loading.value = true
    try {
      const portfolio = await portfoliosApi.getPortfolio(id)
      currentPortfolio.value = portfolio
      return portfolio
    } catch (error) {
      console.error('Failed to fetch portfolio:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const createPortfolio = async (params: portfoliosApi.CreatePortfolioParams) => {
    try {
      const newPortfolio = await portfoliosApi.createPortfolio(params)
      portfolios.value.unshift(newPortfolio)
      return newPortfolio
    } catch (error) {
      console.error('Failed to create portfolio:', error)
      throw error
    }
  }

  const updatePortfolio = async (id: number, params: Partial<portfoliosApi.CreatePortfolioParams>) => {
    try {
      const updatedPortfolio = await portfoliosApi.updatePortfolio(id, params)
      const index = portfolios.value.findIndex(p => p.id === id)
      if (index !== -1) {
        portfolios.value[index] = updatedPortfolio
      }
      if (currentPortfolio.value?.id === id) {
        currentPortfolio.value = updatedPortfolio
      }
      return updatedPortfolio
    } catch (error) {
      console.error('Failed to update portfolio:', error)
      throw error
    }
  }

  const deletePortfolio = async (id: number) => {
    try {
      await portfoliosApi.deletePortfolio(id)
      portfolios.value = portfolios.value.filter(p => p.id !== id)
      if (currentPortfolio.value?.id === id) {
        currentPortfolio.value = null
      }
    } catch (error) {
      console.error('Failed to delete portfolio:', error)
      throw error
    }
  }

  const toggleLike = async (portfolioId: number) => {
    const portfolio = portfolios.value.find(p => p.id === portfolioId) || 
                    topPortfolios.value.find(p => p.id === portfolioId) ||
                    currentPortfolio.value
    if (!portfolio) return

    const wasLiked = portfolio.isLiked

    try {
      if (wasLiked) {
        await likesApi.unlike({ targetType: 'PORTFOLIO', targetId: portfolioId })
        portfolio.likes--
        portfolio.isLiked = false
      } else {
        await likesApi.like({ targetType: 'PORTFOLIO', targetId: portfolioId })
        portfolio.likes++
        portfolio.isLiked = true
      }
    } catch (error) {
      // 回滚状态
      portfolio.isLiked = wasLiked
      portfolio.likes += wasLiked ? 1 : -1
      throw error
    }
  }

  return {
    // State
    portfolios,
    currentPortfolio,
    topPortfolios,
    loading,
    pagination,
    
    // Actions
    fetchPortfolios,
    fetchTopPortfolios,
    fetchPortfolio,
    createPortfolio,
    updatePortfolio,
    deletePortfolio,
    toggleLike
  }
})