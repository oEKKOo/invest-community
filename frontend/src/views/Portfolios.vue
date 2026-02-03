<template>
  <div class="portfolios">
    <div class="portfolios-header">
      <h2 class="page-title">投资组合</h2>
      <el-button 
        type="primary" 
        size="large"
        @click="showCreatePortfolio = true"
        :icon="Plus"
        class="create-btn"
      >
        创建我的组合
      </el-button>
    </div>

    <!-- 创建组合对话框 -->
    <el-dialog
      v-model="showCreatePortfolio"
      title="构建投资策略"
      width="700px"
      class="create-portfolio-dialog"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="80px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="组合名称" prop="title">
              <el-input
                v-model="createForm.title"
                placeholder="给你的组合起个名字"
              />
            </el-form-item>

            <el-form-item label="组合描述" prop="description">
              <el-input
                v-model="createForm.description"
                type="textarea"
                :rows="3"
                placeholder="描述你的投资策略..."
              />
            </el-form-item>

            <el-form-item label="风险等级" prop="riskLevel">
              <el-select v-model="createForm.riskLevel" placeholder="选择风险等级">
                <el-option label="低风险" value="Low" />
                <el-option label="中等风险" value="Medium" />
                <el-option label="高风险" value="High" />
              </el-select>
            </el-form-item>

            <el-form-item label="是否公开">
              <el-switch
                v-model="createForm.isPublic"
                active-text="公开"
                inactive-text="私有"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <div class="assets-section">
              <h4 class="assets-title">资产配置</h4>
              
              <div class="add-asset">
                <el-input
                  v-model="assetForm.symbol"
                  placeholder="代码"
                  size="small"
                  style="width: 80px"
                />
                <el-input
                  v-model="assetForm.name"
                  placeholder="名称"
                  size="small"
                  style="width: 120px"
                />
                <el-input
                  v-model.number="assetForm.allocation"
                  placeholder="比例%"
                  size="small"
                  style="width: 70px"
                  type="number"
                />
                <el-button
                  size="small"
                  @click="addAsset"
                  :disabled="!canAddAsset"
                >
                  添加
                </el-button>
              </div>

              <div class="assets-list">
                <div 
                  v-for="(asset, index) in createForm.assets"
                  :key="index"
                  class="asset-item"
                >
                  <span class="asset-symbol">{{ asset.symbol }}</span>
                  <span class="asset-allocation">{{ asset.allocation }}%</span>
                  <el-button
                    size="small"
                    type="text"
                    @click="removeAsset(index)"
                    class="remove-btn"
                  >
                    删除
                  </el-button>
                </div>
              </div>

              <div class="allocation-summary">
                总配置比例: {{ totalAllocation }}%
              </div>
            </div>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreatePortfolio = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleCreatePortfolio" 
            :loading="creating"
            :disabled="totalAllocation > 100"
          >
            发布组合
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 组合列表 -->
    <div class="portfolios-grid">
      <div v-if="portfoliosStore.loading" class="loading-grid">
        <div v-for="i in 6" :key="i" class="portfolio-skeleton">
          <el-skeleton :rows="4" animated />
        </div>
      </div>

      <div v-else-if="portfoliosStore.portfolios.length === 0" class="empty-state">
        <el-empty 
          description="暂无投资组合"
          :image-size="120"
        >
          <el-button type="primary" @click="showCreatePortfolio = true">
            创建第一个组合
          </el-button>
        </el-empty>
      </div>

      <div
        v-else
        v-for="portfolio in portfoliosStore.portfolios"
        :key="portfolio.id"
        class="portfolio-card"
        @click="$router.push(`/portfolios/${portfolio.id}`)"
      >
        <div class="portfolio-header">
          <h3 class="portfolio-title">{{ portfolio.title }}</h3>
          <el-tag
            :type="getRiskLevelType(portfolio.riskLevel)"
            size="small"
            class="risk-tag"
          >
            {{ portfolio.riskLevel }} 风险
          </el-tag>
        </div>

        <p class="portfolio-description">{{ portfolio.description }}</p>

        <!-- 资产配置图表 -->
        <div class="chart-container">
          <v-chart 
            class="pie-chart" 
            :option="getPieChartOption(portfolio.assets)"
            v-if="portfolio.assets?.length"
          />
        </div>

        <div class="portfolio-stats">
          <div class="stat-row">
            <span class="stat-label">主要配置</span>
            <span class="stat-label">年化收益</span>
          </div>
          <div class="stat-row">
            <span class="stat-value">{{ portfolio.assets[0]?.symbol || 'N/A' }}</span>
            <span class="stat-value positive">+{{ portfolio.returnsYTD }}%</span>
          </div>
        </div>

        <div class="portfolio-footer">
          <div class="portfolio-author">
            <el-avatar :size="32" :src="getAvatarUrl(portfolio.id)">
              {{ portfolio.userName[0] }}
            </el-avatar>
            <span class="author-name">{{ portfolio.userName }}</span>
          </div>
          <el-button
            type="text"
            :class="{ liked: portfolio.isLiked }"
            @click.stop="handleLike(portfolio.id)"
            class="like-btn"
          >
            <el-icon><Star /></el-icon>
            <span>{{ portfolio.likes }}</span>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="portfoliosStore.portfolios.length > 0">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :total="portfoliosStore.pagination.total"
        layout="prev, pager, next, total"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted, computed } from 'vue'
import { usePortfoliosStore } from '../stores/portfolios'
import { useAuthStore } from '../stores/auth'
import type { PortfolioAsset } from '../types'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import {
  Plus,
  Star
} from '@element-plus/icons-vue'

use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent])

const portfoliosStore = usePortfoliosStore()
const authStore = useAuthStore()

// 状态
const showCreatePortfolio = ref(false)
const creating = ref(false)
const currentPage = ref(1)
const pageSize = ref(12)

// 表单
const createFormRef = ref<FormInstance>()
const createForm = ref({
  title: '',
  description: '',
  riskLevel: 'Medium' as 'Low' | 'Medium' | 'High',
  isPublic: true,
  assets: [] as PortfolioAsset[]
})

const assetForm = ref({
  symbol: '',
  name: '',
  allocation: 0
})

const createRules: FormRules = {
  title: [
    { required: true, message: '请输入组合名称', trigger: 'blur' },
    { min: 2, max: 50, message: '组合名称长度应在2-50字符之间', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过200字符', trigger: 'blur' }
  ],
  riskLevel: [
    { required: true, message: '请选择风险等级', trigger: 'change' }
  ]
}

// 图表颜色
const CHART_COLORS = ['#2563eb', '#7c3aed', '#db2777', '#ea580c', '#16a34a', '#4b5563']

// 计算属性
const totalAllocation = computed(() => {
  return createForm.value.assets.reduce((sum, asset) => sum + asset.allocation, 0)
})

const canAddAsset = computed(() => {
  return assetForm.value.symbol && 
         assetForm.value.name && 
         assetForm.value.allocation > 0 &&
         totalAllocation.value + assetForm.value.allocation <= 100
})

// 方法
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchPortfolios()
}

const fetchPortfolios = async () => {
  try {
    await portfoliosStore.fetchPortfolios({
      page: currentPage.value,
      pageSize: pageSize.value,
      sortBy: 'returnsYTD'
    })
  } catch (error) {
    ElMessage.error('获取投资组合失败')
  }
}

const addAsset = () => {
  if (!canAddAsset.value) return

  createForm.value.assets.push({
    symbol: assetForm.value.symbol,
    name: assetForm.value.name,
    allocation: assetForm.value.allocation
  })

  assetForm.value = {
    symbol: '',
    name: '',
    allocation: 0
  }
}

const removeAsset = (index: number) => {
  createForm.value.assets.splice(index, 1)
}

const handleCreatePortfolio = async () => {
  if (!createFormRef.value) return

  try {
    await createFormRef.value.validate()

    if (createForm.value.assets.length === 0) {
      ElMessage.warning('请至少添加一个资产配置')
      return
    }

    if (totalAllocation.value > 100) {
      ElMessage.warning('总配置比例不能超过100%')
      return
    }

    creating.value = true

    await portfoliosStore.createPortfolio(createForm.value)

    ElMessage.success('投资组合创建成功')
    showCreatePortfolio.value = false
    resetCreateForm()
    fetchPortfolios()
  } catch (error: any) {
    if (error.fields) return // 表单验证错误
    ElMessage.error('创建失败，请稍后重试')
  } finally {
    creating.value = false
  }
}

const resetCreateForm = () => {
  createForm.value = {
    title: '',
    description: '',
    riskLevel: 'Medium',
    isPublic: true,
    assets: []
  }
  assetForm.value = {
    symbol: '',
    name: '',
    allocation: 0
  }
  createFormRef.value?.clearValidate()
}

const handleLike = async (portfolioId: number) => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }

  try {
    await portfoliosStore.toggleLike(portfolioId)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const getRiskLevelType = (riskLevel: string) => {
  switch (riskLevel) {
    case 'High': return 'danger'
    case 'Medium': return 'warning'
    case 'Low': return 'success'
    default: return 'info'
  }
}

const getPieChartOption = (assets: PortfolioAsset[]) => {
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    series: [
      {
        name: '资产配置',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        data: assets.map((asset, index) => ({
          value: asset.allocation,
          name: asset.symbol,
          itemStyle: {
            color: CHART_COLORS[index % CHART_COLORS.length]
          }
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
}

const getAvatarUrl = (id: number) => {
  return `https://picsum.photos/seed/${id}/40/40`
}

onMounted(() => {
  fetchPortfolios()
})
</script>

<style lang="scss" scoped>
.portfolios {
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.3s ease-out;
}

.portfolios-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;

  @media (max-width: 640px) {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
}

.page-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0;
}

.create-btn {
  background: #4f46e5;
  border-color: #4f46e5;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);

  &:hover {
    background: #4338ca;
    border-color: #4338ca;
  }
}

.create-portfolio-dialog {
  :deep(.el-dialog) {
    border-radius: 1rem;
  }

  :deep(.el-dialog__header) {
    padding: 1.5rem 1.5rem 1rem;
    border-bottom: 1px solid #f3f4f6;
  }

  :deep(.el-dialog__body) {
    padding: 1.5rem;
  }
}

.assets-section {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1rem;
}

.assets-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.75rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.add-asset {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.assets-list {
  max-height: 150px;
  overflow-y: auto;
  margin-bottom: 0.75rem;
}

.asset-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: white;
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.asset-symbol {
  font-weight: 600;
  color: #1f2937;
}

.asset-allocation {
  color: #4f46e5;
  font-weight: 600;
}

.remove-btn {
  color: #ef4444;
}

.allocation-summary {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  text-align: right;
}

.dialog-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.portfolios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.loading-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.portfolio-skeleton {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  background: white;
  border-radius: 1rem;
  border: 1px solid #f3f4f6;
}

.portfolio-card {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  display: flex;
  flex-direction: column;

  &:hover {
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    transform: translateY(-4px);
  }
}

.portfolio-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.portfolio-title {
  font-size: 1.125rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0;
  flex: 1;
  line-height: 1.4;
}

.risk-tag {
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 0.75rem;
}

.portfolio-description {
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
  margin: 0 0 1rem 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
  min-height: 40px;
}

.chart-container {
  height: 160px;
  margin-bottom: 1rem;
}

.pie-chart {
  width: 100%;
  height: 100%;
}

.portfolio-stats {
  margin-bottom: 1rem;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.25rem;

  &:last-child {
    margin-bottom: 0;
  }
}

.stat-label {
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 0.875rem;
  font-weight: bold;
  color: #1f2937;

  &.positive {
    color: #059669;
  }
}

.portfolio-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid #f3f4f6;
  margin-top: auto;
}

.portfolio-author {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.author-name {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.like-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: #9ca3af;
  transition: color 0.2s ease-in-out;

  &:hover {
    color: #ef4444;
  }

  &.liked {
    color: #ef4444;
  }
}

.pagination-container {
  display: flex;
  justify-content: center;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>