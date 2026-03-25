import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// 导入页面组件
const MainLayout = () => import('../components/layout/MainLayout.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const Community = () => import('../views/Community.vue')
const Portfolios = () => import('../views/Portfolios.vue')
const AdminPanel = () => import('../views/AdminPanel.vue')
const Profile = () => import('../views/Profile.vue')
const SearchView = () => import('../views/Search.vue')
const Login = () => import('../views/Login.vue')
const OAuthCallback = () => import('../views/auth/OAuthCallback.vue')
const PostDetail = () => import('../views/PostDetail.vue')
const PortfolioDetail = () => import('../views/PortfolioDetail.vue')
// 新增页面
const AssetDetail = () => import('../views/AssetDetail.vue')
const MarketList = () => import('../views/MarketList.vue')
const MarketRankings = () => import('../views/MarketRankings.vue')
const DataMonitor = () => import('../views/admin/DataMonitor.vue')
const MyHoldings = () => import('../views/MyHoldings.vue')
const Messages = () => import('../views/Messages.vue')
const VerifyChannel = () => import('../views/auth/VerifyChannel.vue')
const RealNameAuth = () => import('../views/auth/RealNameAuth.vue')
const ProfessionalAuth = () => import('../views/auth/ProfessionalAuth.vue')
const RiskAssessment = () => import('../views/auth/RiskAssessment.vue')

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/auth/callback/:provider',
    name: 'OAuthCallback',
    component: OAuthCallback,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: 'Dashboard' }
      },
      {
        path: '/search',
        name: 'Search',
        component: SearchView,
        meta: { title: '搜索' }
      },
      {
        path: '/community',
        name: 'Community',
        component: Community,
        meta: { title: 'Community' }
      },
      {
        path: '/portfolios',
        name: 'Portfolios',
        component: Portfolios,
        meta: { title: 'Portfolios' }
      },
      {
        path: '/admin',
        name: 'AdminPanel',
        component: AdminPanel,
        meta: { 
          title: 'Admin Panel',
          requiresAdmin: true
        }
      },
      {
        path: '/admin/data-monitor',
        name: 'DataMonitor',
        component: DataMonitor,
        meta: {
          title: '数据监控',
          requiresAdmin: true
        }
      },
      {
        path: '/profile',
        name: 'Profile',
        component: Profile,
        meta: { title: 'My Profile' }
      },
      {
        path: '/users/:userId',
        name: 'UserProfile',
        component: Profile,
        meta: { title: 'User Profile' },
        props: true
      },
      {
        path: '/posts/:id',
        name: 'PostDetail',
        component: PostDetail,
        meta: { title: 'Post Detail' },
        props: true
      },
      {
        path: '/portfolios/:id',
        name: 'PortfolioDetail',
        component: PortfolioDetail,
        meta: { title: 'Portfolio Detail' },
        props: true
      },
      // 个人持仓
      {
        path: '/holdings',
        name: 'MyHoldings',
        component: MyHoldings,
        meta: { title: '我的持仓', requiresAuth: true }
      },
      {
        path: '/messages',
        name: 'Messages',
        component: Messages,
        meta: { title: '私信会话', requiresAuth: true }
      },
      {
        path: '/auth/verify',
        name: 'VerifyChannel',
        component: VerifyChannel,
        meta: { title: '基础认证', requiresAuth: true }
      },
      {
        path: '/auth/real-name',
        name: 'RealNameAuth',
        component: RealNameAuth,
        meta: { title: '实名认证', requiresAuth: true }
      },
      {
        path: '/auth/professional',
        name: 'ProfessionalAuth',
        component: ProfessionalAuth,
        meta: { title: '专业认证', requiresAuth: true }
      },
      {
        path: '/auth/risk',
        name: 'RiskAssessment',
        component: RiskAssessment,
        meta: { title: '风险评估', requiresAuth: true }
      },
      // 新增路由
      {
        path: '/assets/:assetId',
        name: 'AssetDetail',
        component: AssetDetail,
        meta: { title: '个股详情', requiresAuth: false },
        props: true
      },
      {
        path: '/market',
        name: 'MarketList',
        component: MarketList,
        meta: { title: '行情列表' }
      },
      {
        path: '/market/rankings',
        name: 'MarketRankings',
        component: MarketRankings,
        meta: { title: '涨跌幅榜单' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 检查是否需要认证
  if (to.meta.requiresAuth !== false && !authStore.isLoggedIn) {
    next('/login')
    return
  }
  
  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/')
    return
  }
  
  // 如果已登录访问登录页，重定向到首页
  if (to.name === 'Login' && authStore.isLoggedIn) {
    next('/')
    return
  }
  
  next()
})

export default router
