let assetDetailChartsPrefetched = false

export const preloadAssetDetailCharts = () => {
  if (assetDetailChartsPrefetched) return
  assetDetailChartsPrefetched = true

  void import('@/views/AssetDetail.vue')

  const preloadCharts = async () => {
    const { loadLightweightCharts } = await import('@/utils/chart-loader')
    void Promise.all([
      import('@/components/market/KlineChart.vue'),
      import('@/components/market/IntradayChart.vue'),
      loadLightweightCharts()
    ])
  }

  if ('requestIdleCallback' in window) {
    ;(window as any).requestIdleCallback(preloadCharts, { timeout: 1500 })
  } else {
    globalThis.setTimeout(preloadCharts, 200)
  }
}
