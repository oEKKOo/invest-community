import { use } from 'echarts/core'
import { LineChart, BarChart, CandlestickChart, PieChart } from 'echarts/charts'
import {
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  LegendComponent,
  MarkLineComponent,
  GraphicComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

const registryState: Record<string, boolean> = {
  asset: false,
  dashboard: false,
  portfolios: false,
  portfolioDetail: false,
  holdings: false
}

export const setupAssetEcharts = () => {
  if (registryState.asset) return

  use([
    CandlestickChart,
    LineChart,
    BarChart,
    TooltipComponent,
    GridComponent,
    DataZoomComponent,
    CanvasRenderer
  ])

  registryState.asset = true
}

export const setupDashboardEcharts = () => {
  if (registryState.dashboard) return

  use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])
  registryState.dashboard = true
}

export const setupPortfoliosEcharts = () => {
  if (registryState.portfolios) return

  use([PieChart, TooltipComponent, LegendComponent, GraphicComponent, CanvasRenderer])
  registryState.portfolios = true
}

export const setupPortfolioDetailEcharts = () => {
  if (registryState.portfolioDetail) return

  use([PieChart, LineChart, TooltipComponent, LegendComponent, GridComponent, MarkLineComponent, CanvasRenderer])
  registryState.portfolioDetail = true
}

export const setupHoldingsEcharts = () => {
  if (registryState.holdings) return

  use([LineChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, CanvasRenderer])
  registryState.holdings = true
}
