# InvestHub Frontend

InvestHub Community 投资社区前端应用，基于Vue 3 + Element Plus + TypeScript开发。

## 🚀 技术栈

- **Vue 3** - 渐进式前端框架
- **TypeScript** - 类型安全的JavaScript超集
- **Element Plus** - 基于Vue 3的组件库
- **Vue Router** - Vue.js官方路由管理器
- **Pinia** - Vue状态管理库
- **Axios** - HTTP客户端
- **ECharts** - 数据可视化图表库
- **Vite** - 现代前端构建工具
- **SCSS** - CSS预处理器

## 📦 安装依赖

```bash
npm install
```

## 🛠 开发

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint
```

## 🏗️ 项目结构

```
src/
├── api/           # API接口服务
├── components/    # 公共组件
│   └── layout/    # 布局组件
├── router/        # 路由配置
├── stores/        # 状态管理
├── styles/        # 全局样式
├── types/         # TypeScript类型定义
├── views/         # 页面组件
└── main.ts        # 应用入口
```

## 📱 功能特性

### 🔐 用户认证
- 用户注册/登录
- JWT Token管理
- 自动Token刷新
- 权限控制

### 🏠 Dashboard
- 市场情绪图表
- 热门讨论展示
- 顶级投资组合
- 社区统计数据

### 💬 社区论坛
- 帖子发布与编辑
- 内容状态管理（草稿/待审核/已发布）
- 点赞和收藏功能
- 标签分类系统

### 📊 投资组合
- 创建和管理投资组合
- 资产配置可视化
- 风险等级分类
- 收益率展示

### 🔧 管理后台
- 内容审核队列
- 用户举报处理
- 统计数据展示
- 社区治理工具

### 👤 个人中心
- 用户资料管理
- 活动记录展示
- 账户安全设置
- 邀请好友功能

## 🎨 设计系统

### 配色方案
- 主色调：蓝色 (#2563eb)
- 辅助色：紫色 (#6366f1)
- 成功色：绿色 (#10b981)
- 警告色：橙色 (#f59e0b)
- 错误色：红色 (#ef4444)

### UI特点
- 现代化圆角设计
- 阴影层次感
- 流畅的过渡动画
- 响应式布局
- 移动端适配

## 🔌 API集成

项目使用Axios进行HTTP请求，支持：

- 请求/响应拦截器
- 自动Token注入
- 统一错误处理
- 请求重试机制

### API模块
- `auth.ts` - 用户认证
- `posts.ts` - 帖子管理
- `portfolios.ts` - 投资组合
- `likes.ts` - 点赞功能
- `admin.ts` - 管理功能
- `dashboard.ts` - Dashboard数据

## 🏃‍♂️ 开发指南

### 环境变量

创建 `.env.local` 文件：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_APP_TITLE=InvestHub Community
```

### 代码规范

- 使用TypeScript进行类型检查
- 组件使用Composition API
- 样式采用SCSS + 工具类
- 遵循Vue 3最佳实践

### 状态管理

使用Pinia进行状态管理，主要Store包括：

- `useAuthStore` - 用户认证状态
- `usePostsStore` - 帖子数据管理
- `usePortfoliosStore` - 投资组合管理
- `useDashboardStore` - Dashboard数据

### 路由配置

- 支持权限控制
- 懒加载页面组件
- 嵌套路由结构
- 路由守卫验证

## 🚀 部署

### 构建生产版本
```bash
npm run build
```

### 部署到Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend-server:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来帮助改进项目。

## 📞 联系方式

如有问题，请通过Issue联系我们。