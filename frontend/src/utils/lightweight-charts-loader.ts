/** 仅加载 TradingView Lightweight Charts，避免与 chart-loader / vue-echarts 共用模块造成打包交叉依赖。 */
let lightweightChartsPromise: Promise<typeof import('lightweight-charts')> | null = null

export const loadLightweightCharts = () => {
  if (!lightweightChartsPromise) {
    lightweightChartsPromise = import('lightweight-charts')
  }
  return lightweightChartsPromise
}
