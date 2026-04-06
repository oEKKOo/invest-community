let assetDetailChartsPrefetched = false
/** 合并为单次 idle 任务，避免多处连续调用重复排队 import() */
let chartsPreloadIdleScheduled = false

export const preloadAssetDetailCharts = () => {
  if (assetDetailChartsPrefetched) return
  assetDetailChartsPrefetched = true

  if (chartsPreloadIdleScheduled) return
  chartsPreloadIdleScheduled = true

  const run = async () => {
    try {
      const { loadLightweightCharts } = await import('@/utils/lightweight-charts-loader')
      await Promise.all([
        import('@/components/market/KlineChart.vue'),
        import('@/components/market/IntradayChart.vue'),
        loadLightweightCharts()
      ])
    } catch {
      // 预加载失败不影响导航
    }
  }

  // 先等一帧 paint，再进 idle，减轻与首屏 JS/CSS/接口 争用
  const schedule = () => {
    if ('requestIdleCallback' in window) {
      ;(window as any).requestIdleCallback(run, { timeout: 2800 })
    } else {
      globalThis.setTimeout(run, 400)
    }
  }
  if (typeof requestAnimationFrame === 'function') {
    requestAnimationFrame(() => schedule())
  } else {
    schedule()
  }
}
