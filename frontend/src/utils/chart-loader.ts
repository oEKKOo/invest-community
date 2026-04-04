import { defineAsyncComponent } from 'vue'

type VueEchartsModule = typeof import('vue-echarts')

let dashboardChartComponentPromise: Promise<VueEchartsModule['default']> | null = null
let portfoliosChartComponentPromise: Promise<VueEchartsModule['default']> | null = null
let portfolioDetailChartComponentPromise: Promise<VueEchartsModule['default']> | null = null
let holdingsChartComponentPromise: Promise<VueEchartsModule['default']> | null = null

const loadVueEchartsWithSetup = async (
  setup: () => void
): Promise<VueEchartsModule['default']> => {
  setup()
  const module = await import('vue-echarts')
  return module.default
}

export const loadDashboardChartComponent = () => {
  if (!dashboardChartComponentPromise) {
    dashboardChartComponentPromise = (async () => {
      const { setupDashboardEcharts } = await import('@/utils/echarts')
      return loadVueEchartsWithSetup(setupDashboardEcharts)
    })()
  }
  return dashboardChartComponentPromise
}

export const loadPortfoliosChartComponent = () => {
  if (!portfoliosChartComponentPromise) {
    portfoliosChartComponentPromise = (async () => {
      const { setupPortfoliosEcharts } = await import('@/utils/echarts')
      return loadVueEchartsWithSetup(setupPortfoliosEcharts)
    })()
  }
  return portfoliosChartComponentPromise
}

export const loadPortfolioDetailChartComponent = () => {
  if (!portfolioDetailChartComponentPromise) {
    portfolioDetailChartComponentPromise = (async () => {
      const { setupPortfolioDetailEcharts } = await import('@/utils/echarts')
      return loadVueEchartsWithSetup(setupPortfolioDetailEcharts)
    })()
  }
  return portfolioDetailChartComponentPromise
}

export const loadHoldingsChartComponent = () => {
  if (!holdingsChartComponentPromise) {
    holdingsChartComponentPromise = (async () => {
      const { setupHoldingsEcharts } = await import('@/utils/echarts')
      return loadVueEchartsWithSetup(setupHoldingsEcharts)
    })()
  }
  return holdingsChartComponentPromise
}

export const createLazyChartComponent = (loader: () => Promise<any>) =>
  defineAsyncComponent({
    loader,
    suspensible: false
  })
