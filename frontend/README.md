# InvestHub Frontend

InvestHub 投资社区主站前端：**Vue 3 + TypeScript + Vite**，UI 为 **Element Plus**。与仓库内 Django 后端（`background/`）通过 REST API 联调，认证采用 **JWT**（Access + Refresh，请求拦截器内自动刷新）。

---

## 功能概览

| 模块 | 说明 |
|------|------|
| **首页 / Dashboard** | 市场概览、榜单、社区与组合信息流、ECharts 可视化 |
| **行情** | 行情列表、涨跌幅榜；个股详情（K 线 / 分时，lightweight-charts） |
| **社区** | 帖子流、发帖与编辑、详情与评论（楼中楼）、点赞 / 收藏 / 举报 |
| **投资组合** | 组合列表与详情、公开策略展示与互动 |
| **我的持仓** | 个人持仓与收益相关视图 |
| **搜索** | 全站搜索入口（帖子 / 标的 / 组合等，与后端约定一致） |
| **用户与资料** | 登录 / 注册相关页、个人主页（含 `/users/:userId`） |
| **认证与合规流程** | 基础认证、实名、专业认证、风险评估等引导页（需登录） |
| **私信** | 会话列表与消息（需登录） |
| **群组** | 群组列表、详情、邀请与入群审核 |
| **管理后台** | 总览入口；数据监控、内容审核队列、用户风险中心、运营数据分析（需管理员角色） |

游客可访问部分页面（如登录、OAuth 回调、部分行情与资产页）；主布局下多数路由默认 **需要登录**，管理类路由额外校验 **管理员**。

---

## 技术栈

- **框架**：Vue 3（Composition API）、TypeScript  
- **构建**：Vite 6  
- **UI**：Element Plus、`@element-plus/icons-vue`  
- **路由 / 状态**：Vue Router 4、Pinia  
- **HTTP**：Axios（统一 `code === 0` 业务成功约定、401 刷新 Token）  
- **图表**：ECharts、`vue-echarts`；**lightweight-charts**（K 线 / 分时）  
- **工具**：Day.js、`@vueuse/core`  
- **工程化**：`unplugin-auto-import`、`unplugin-vue-components`（Element Plus 按需解析）、Sass、`vite-plugin-compression`（构建产出 `.gz` / `.br`）、`rollup-plugin-visualizer`（`analyze` 模式）

---

## 环境要求

- **Node.js**：建议 **18.x 或 20.x LTS**（与 Vite 6 生态兼容）  
- **包管理**：本仓库使用 **npm**（见 `package-lock.json`）  
- **后端**：本地开发时后端默认 `http://127.0.0.1:8000`（与 Vite 代理一致）

---

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 环境变量

复制示例文件并按需修改：

```bash
cp env.example .env.local
```

变量说明见下文 [环境变量](#环境变量)。

### 3. 启动开发服务

```bash
npm run dev
```

- 开发服务器默认 **http://localhost:3000**（见 `vite.config.ts`）  
- 请求路径 **`/api`** 会代理到 **`http://127.0.0.1:8000`**，因此若使用代理，可将 `VITE_API_BASE_URL` 设为 **`/api`**；若直接请求完整后端地址，则设为 **`http://127.0.0.1:8000/api`** 等。

**Windows** 也可双击项目内 `start.bat`（自动检测 `node_modules` 并执行 `npm run dev`）。

### 4. 同时启动后端

在仓库 `background/` 中按该目录文档启动 Django（例如 `runserver` 监听 `8000`），否则除静态页外接口将失败。

---

## 环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `VITE_API_BASE_URL` | Axios `baseURL`；未设置时代码侧回退为 **`/api`** | `http://127.0.0.1:8000/api` 或 `/api` |
| `VITE_APP_TITLE` | 应用标题（若业务中有使用） | `InvestHub Community` |

模板文件：[env.example](./env.example)。本地覆盖请使用 **`.env.local`**（勿提交密钥；Vite 仅暴露 `VITE_` 前缀变量）。

开发与生产默认还可分别使用仓库内 **[`.env.development`](./.env.development)**（`VITE_API_BASE_URL=/api`，配合 Vite 代理）、**[`.env.production`](./.env.production)**（占位 Render 地址；线上以构建环境变量为准）。

### Cloudflare Pages 部署

本仓库为 monorepo，前端在 **`frontend/`** 子目录。

| 配置项 | 值 |
|--------|-----|
| **Root directory** | `frontend` |
| **Build command** | `npm run build` |
| **Build output directory** | `dist` |

在 Pages 项目 **Settings → Environment variables** 中至少设置：

- **`VITE_API_BASE_URL`**：生产环境填完整后端 API 基址，例如 `https://<你的服务>.onrender.com/api`（须与 Django 的 `/api` 前缀一致）。
- **`NODE_VERSION`**：建议 **`20`**（或 `22`），避免默认 Node 过旧导致 Vite 6 构建失败。

`public/_redirects` 已配置 **`/*` → `/index.html` 200**，用于 Vue Router **history** 模式刷新子路径不 404。推送绑定分支后会自动重新构建部署。

Cloudflare 构建阶段使用 **`npm ci`**（等价于 clean-install），依赖 **`package-lock.json` 与 `package.json` 同步提交**。`eslint` 为 **9.x**，与 `@vue/eslint-config-typescript` 14.x 的 peer 要求一致，无需 `legacy-peer-deps`。

---

## 常用脚本

| 命令 | 作用 |
|------|------|
| `npm run dev` | 启动开发服务器 |
| `npm run build` | `vue-tsc` 类型检查 + 生产构建，输出 `dist/` |
| `npm run preview` | 本地预览生产构建 |
| `npm run analyze` | 构建 `analyze` 模式，生成 `dist/stats.html` 体积分析报告 |
| `npm run lint` | ESLint 9（flat config，见 `eslint.config.mjs`）检查并尝试修复 |

生产构建默认 **移除 `console` / `debugger`**，并生成 **gzip / brotli** 侧车文件（`*.gz` / `*.br`），便于 Nginx `gzip_static` 等配置。

---

## 目录结构

```
frontend/
├── env.example              # 环境变量示例
├── eslint.config.mjs        # ESLint 9 flat config（Vue + TS）
├── index.html
├── package.json
├── package-lock.json
├── tsconfig.json
├── vite.config.ts           # Vite、代理、分包、压缩、analyze 插件
├── start.bat                # Windows 一键安装依赖并 dev
├── src/
│   ├── api/                 # 按领域拆分的接口封装（见下表）
│   ├── components/          # 布局、行情图表、举报弹窗等
│   ├── composables/         # 组合式函数（如行情流）
│   ├── router/              # 路由与全局前置守卫（登录 / 管理员）
│   ├── stores/              # Pinia stores
│   ├── styles/              # 全局 SCSS、设计变量 variables.scss
│   ├── types/               # TypeScript 类型
│   ├── utils/               # 图表懒加载、通知、日期等工具
│   ├── views/               # 页面级组件（含 admin/、auth/ 子目录）
│   ├── App.vue
│   └── main.ts
├── auto-imports.d.ts        # unplugin-auto-import 生成
└── components.d.ts          # unplugin-vue-components 生成
```

### `src/api/` 模块

| 文件 | 职责 |
|------|------|
| `index.ts` | Axios 实例、拦截器、`get/post/patch/del` 封装 |
| `auth-token.ts` | Token 读写与刷新（供拦截器使用） |
| `auth.ts` | 注册、登录等认证接口 |
| `users.ts` | 用户资料与相关接口 |
| `posts.ts` | 帖子与评论 |
| `likes.ts` | 点赞 |
| `portfolios.ts` | 投资组合 |
| `holdings.ts` | 持仓 |
| `market.ts` | 行情、K 线、榜单等 |
| `dashboard.ts` | 首页聚合数据 |
| `search.ts` | 搜索 |
| `notifications.ts` | 通知 |
| `reports.ts` | 举报 |
| `admin.ts` | 管理端接口 |
| `groups.ts` | 群组 |
| `messages.ts` | 私信 |

### `src/stores/` 模块

包含：`auth`、`dashboard`、`posts`、`portfolios`、`market`、`notifications`、`messages`、`groups`，以及管理相关 `adminModeration`、`adminAnalytics` 等，与页面和 `api/` 分层对应。

### 关键页面路由（摘录）

- `/` Dashboard  
- `/login`、`/auth/callback/:provider`  
- `/community`、`/posts/:id`  
- `/market`、`/market/rankings`、`/assets/:assetId`  
- `/portfolios`、`/portfolios/:id`  
- `/holdings`、`/profile`、`/users/:userId`  
- `/search`、`/messages`  
- `/groups`、`/groups/:groupId`、`/groups/invites`、`/groups/:groupId/requests`  
- `/auth/verify`、`/auth/real-name`、`/auth/professional`、`/auth/risk`  
- `/admin` 及子路由：`/admin/data-monitor`、`/admin/moderation-queue`、`/admin/user-risk`、`/admin/analytics`  

路由均为懒加载；行情列表与涨跌幅榜进入时会按需预加载个股图表相关资源（见 `router/index.ts` 中 `meta.preload`）。

---

## 设计与样式

- 全局样式入口：`src/styles/index.scss`  
- 设计变量（主色、语义色、圆角、阴影等）：`src/styles/variables.scss`  
- 主布局：`src/components/layout/MainLayout.vue`（侧栏 + 顶栏 + 内容区）  
- 涨跌等展示在业务页面中遵循统一红涨 / 绿跌语义（与 A 股习惯一致处已在样式与页面中体现）；含行情的页面应保留「仅供参考、不构成投资建议」类说明（与后端数据来源说明一致）

---

## API 与联调说明

- 后端成功响应约定：`{ code: 0, data: ... }`（`code !== 0` 时前端会提示 `message` 并 reject）  
- 需登录接口在请求头携带：`Authorization: Bearer <access_token>`  
- **401** 时尝试 Refresh；失败则清理本地认证并跳转 `/login`  
- 开发环境推荐使用 Vite **`/api` 代理** 避免 CORS；生产环境通常由 **Nginx 反代** `/api` 到后端

---

## 性能与构建（摘要）

- **路由级懒加载**；图表库（ECharts、lightweight-charts）异步加载与缓存，避免重复初始化  
- **Rollup `manualChunks`**：拆分 `vendor-vue`、`vendor-echarts`、`vendor-lightweight-chart`、Element 相关块等，控制首包体积  
- **`npm run analyze`** 生成 `dist/stats.html` 查看各 chunk gzip/brotli 体积  

历史体积快照（仅供参考，以当前构建为准）：

- Dashboard、AssetDetail 等页面 chunk 体积较小；`vendor-echarts`、`vendor-lightweight-chart` 已独立于首屏主包  

---

## 生产部署

### 构建

```bash
npm run build
```

将 `dist/` 部署到静态资源服务器；**SPA** 需将所有路由回退到 `index.html`。

### Nginx 示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

若已部署构建时生成的 **`.gz` / `.br`** 文件，可启用 `gzip_static`（及环境支持的 brotli 静态模块）以减少 CPU 实时压缩开销；否则使用 `gzip on` / `brotli on` 在线压缩亦可。

静态资源长缓存示例：

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|svg|woff2)$ {
    expires 30d;
    add_header Cache-Control "public, max-age=2592000, immutable";
}
```

---

## 仓库与文档

- 本目录为 monorepo 中的 **前端子项目**；后端与 API 细节见仓库 `background/` 及根目录 `docs/`。  
- 接口契约以后端实现与 `background` 下文档为准；前端 `src/api/*` 为调用封装层。

---

## 许可证

MIT License

## 贡献与反馈

欢迎通过 Issue / Pull Request 提交问题与改进。若联调失败，请优先检查：**后端是否启动**、**`.env.local` 中 `VITE_API_BASE_URL`** 是否与代理/跨域策略一致、**JWT 是否过期**。
