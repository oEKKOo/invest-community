# 投研社区后端项目

这是一个基于 Django + Django REST Framework 的投研社区后端项目，提供用户管理、内容发布、投资组合分享等功能。

## 🏗️ 项目结构

```
background/
├── invest_backend/          # Django 项目配置
│   ├── settings.py         # 项目设置
│   ├── urls.py            # 主路由配置
│   └── ...
├── accounts/               # 用户管理应用
├── content/               # 内容管理应用
├── portfolios/            # 投资组合应用
├── notifications/         # 通知系统应用
├── reports/               # 举报系统应用
├── requirements.txt       # Python 依赖
├── setup.py              # 项目初始化脚本
├── start_dev.bat         # Windows 启动脚本
├── start_dev.sh          # Linux/Mac 启动脚本
└── README.md             # 项目说明
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 8.0+
- pip

### 1. 数据库准备

```sql
CREATE DATABASE community_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 环境配置

1. 复制环境变量文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，配置数据库信息：
   ```
   DB_NAME=invest_db
   DB_USER=root
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=3306
   ```

### 3. 自动初始化（推荐）

**Windows:**
```bash
python setup.py
```

**或者使用启动脚本:**
```bash
# Windows
start_dev.bat

# Linux/Mac
chmod +x start_dev.sh
./start_dev.sh
```

### 4. 手动初始化

```bash
# ── Step 1：安装依赖 ─────────────────────────────────────────────
pip install -r requirements.txt

# ── Step 2：数据库迁移 ───────────────────────────────────────────
python manage.py makemigrations
python manage.py migrate

# ── Step 3：创建超级用户 ─────────────────────────────────────────
python manage.py createsuperuser

# ── Step 4：启动开发服务器 ───────────────────────────────────────
python manage.py runserver
```

> **Windows PowerShell 每次启动前需设置环境变量：**
> ```powershell
> cd D:\invest\background
> $env:FINNHUB_API_KEY="your_finnhub_key_here"
> $env:USE_REDIS="false"
> ```

---

## 📊 A股数据初始化命令（按顺序执行）

> **说明**：以下命令用于首次初始化或全量回补行情数据，依赖 Tushare API Token（在 `.env` 中配置 `TUSHARE_API_TOKEN`）。

### 🔰 阶段一：首次初始化（全新部署时执行一次）

```bash
# Step 1：导入全部上市A股列表（约5500只）+ 同步近一年日线K线 + 刷新行情快照
python manage.py import_cn_stocks --kline --quote --days 365

# Step 2：为所有用户持仓生成历史每日快照（基于已导入的K线）
python manage.py fill_holding_snapshots --days 365
```

---

### 🔄 阶段二：每日收盘后定时更新（16:30 之后执行）

> Tushare 日K数据在 A 股收盘后（约16:00）才落库，建议每日 **16:30** 后执行。

```bash
# Step 1：更新A股日K线（只补今天新增的1根K线，跳过重新导入股票列表）
python manage.py import_cn_stocks --kline-only --days 1

# Step 2：从最新K线生成用户持仓每日快照（补缺模式，已有快照不重复写）
python manage.py fill_holding_snapshots --days 1
```

> **注意**：若当天为非交易日（周末/节假日），Tushare 不返回数据，两条命令均会自动跳过，不会报错。

---

### 🔧 阶段三：服务重启 / 补缺历史数据

```bash
# 补近30天K线（服务中断后补缺）
python manage.py import_cn_stocks --kline-only --days 30
python manage.py fill_holding_snapshots --days 30

# 全量重新回补近一年（数据异常时使用）
python manage.py import_cn_stocks --kline-only --days 365
python manage.py fill_holding_snapshots --days 365
```

---

### 🎯 其他常用管理命令

```bash
# 只导入指定股票的K线+行情（快速测试用）
python manage.py import_cn_stocks --codes 600519,000858,300750 --kline --quote

# 只刷新行情快照（不更新K线）
python manage.py import_cn_stocks --quote-only

# 强制重建指定用户的持仓快照
python manage.py fill_holding_snapshots --user-id 1 --force

# 调试单条持仓快照生成
python manage.py fill_holding_snapshots --holding-id 5
```

---

### 📋 命令参数速查表

| 命令 | 关键参数 | 说明 |
|---|---|---|
| `import_cn_stocks` | _(无)_ | 仅导入股票列表，不同步K线/行情 |
| `import_cn_stocks` | `--kline --days N` | 导入列表 + 同步最近N天K线 |
| `import_cn_stocks` | `--quote` | 导入列表 + 刷新行情快照 |
| `import_cn_stocks` | `--kline --quote --days N` | 导入列表 + K线 + 行情（初始化一步到位） |
| `import_cn_stocks` | `--kline-only --days N` | **跳过导入**，只同步K线 ✅ 每日更新用 |
| `import_cn_stocks` | `--quote-only` | **跳过导入**，只刷新行情快照 |
| `import_cn_stocks` | `--codes A,B --kline --quote` | 指定代码同步 |
| `fill_holding_snapshots` | `--days N` | 补全最近N天持仓快照（补缺模式） |
| `fill_holding_snapshots` | `--user-id N` | 只处理指定用户 |
| `fill_holding_snapshots` | `--holding-id N` | 只处理指定持仓记录（调试用） |
| `fill_holding_snapshots` | `--force` | 强制重建（先删后补） |

## 📡 API 接口

项目启动后，可以访问以下地址：

- **开发服务器**: http://127.0.0.1:8000/
- **管理后台**: http://127.0.0.1:8000/admin/
- **API 根路径**: http://127.0.0.1:8000/api/

### 主要 API 端点

#### 用户认证
- `POST /api/auth/register/` - 用户注册
- `POST /api/auth/login/` - 用户登录
- `POST /api/auth/refresh/` - 刷新 Token

#### 用户管理
- `GET /api/users/me/` - 获取当前用户信息
- `PATCH /api/users/me/profile/` - 更新用户资料
- `POST /api/users/{id}/follow/` - 关注用户

#### 内容管理
- `GET /api/posts/` - 获取帖子列表
- `POST /api/posts/` - 创建帖子
- `GET /api/posts/{id}/` - 获取帖子详情
- `POST /api/posts/{id}/comments/` - 发表评论

#### 投资组合
- `GET /api/portfolios/` - 获取组合列表
- `POST /api/portfolios/` - 创建组合
- `GET /api/portfolios/top/` - 获取热门组合

#### 其他功能
- `POST /api/likes/` - 点赞/取消点赞
- `POST /api/reports/` - 举报内容
- `GET /api/notifications/` - 获取通知列表

## 🗄️ 数据库设计

项目包含以下核心数据表：

- **用户表 (user)** - 用户基本信息和权限
- **用户投资偏好表 (user_invest_profile)** - 用户投资偏好设置
- **内容表 (content)** - 帖子和文章内容
- **评论表 (comment)** - 评论和回复
- **投资组合表 (portfolio)** - 用户创建的投资组合
- **组合资产表 (portfolio_asset)** - 组合中的资产配置
- **点赞表 (like)** - 统一的点赞记录
- **收藏表 (favorite)** - 用户收藏的内容
- **举报表 (report)** - 用户举报记录
- **通知表 (notification)** - 系统通知

## 🔐 权限系统

项目实现了基于角色的权限控制：

- **USER** - 普通用户，可以发布内容、创建组合、参与互动
- **MODERATOR** - 管理员，可以审核内容、处理举报
- **ADMIN** - 超级管理员，拥有所有权限

## 🛠️ 开发工具

项目集成了以下开发工具：

- **Django Admin** - Web 管理界面
- **DRF API** - RESTful API 框架
- **JWT 认证** - 无状态身份认证
- **CORS 支持** - 跨域资源共享
- **MySQL 数据库** - 关系型数据存储

## 📝 开发说明

### 新增 API 端点

1. 在对应应用的 `views.py` 中添加视图函数或类
2. 在应用的 `urls.py` 中添加路由配置
3. 根据需要创建或修改序列化器

### 数据库变更

```bash
# 创建迁移文件
python manage.py makemigrations

# 应用迁移
python manage.py migrate
```

### 测试数据

可以通过 Django Admin 界面或 API 接口添加测试数据。

## API 性能观测（可选）

- **Django Debug Toolbar**：`DEBUG=True` 时启用，访问 `http://127.0.0.1:8000/__debug__/` 侧栏查看 SQL。依赖已列入 `requirements.txt`（`django-debug-toolbar`）。
- **接口耗时日志**：Logger `investhub.api_timing`，在 `asset_detail`、`asset_kline`、`asset_contents` 及 `get_or_refresh_quote` 中输出 `endpoint=… duration_ms=…`。默认在 `DEBUG=True` 时写入；生产环境可设置环境变量 `DJANGO_API_TIMING_LOG=true` 开启（或设为 `false` 强制关闭）。
- **行情榜单慢查询**：`asset_quote_snapshot` 上为 `change_pct`、`volume` 增加了降序索引（迁移 `market_data.0003`），并按 `created_at` 补充了 `(asset_id, created_at DESC)` 索引（迁移 `market_data.0004`）。说明与 `EXPLAIN` 自检见仓库 `docs/mysql_quote_snapshot_indexes.md`。
- **高频只读短缓存**（默认走 `CACHES` 配置的 Redis 或 LocMem）：全局搜索 `GET /api/search/`（`GLOBAL_SEARCH_CACHE_TTL`，默认 20s）、管理台统计 `admin_stats`（`ADMIN_STATS_CACHE_TTL`，默认 45s）、前台板块树根无筛选参数时（`BOARD_TREE_CACHE_TTL`，默认 90s）。可通过环境变量覆盖同名设置项。

## 🚀 部署

生产环境部署建议：

1. 设置 `DEBUG = False`
2. 配置 `ALLOWED_HOSTS`
3. 使用 PostgreSQL 或 MySQL 数据库
4. 配置 Nginx + Gunicorn
5. 启用 HTTPS
6. 配置 Redis 缓存

## 📞 技术支持

如有问题，请检查：
1. Python 和 Django 版本是否符合要求
2. 数据库连接是否正确配置
3. 依赖包是否完整安装
4. 端口是否被占用

---

**项目特点**: 投研社区 + 投顾组合一体化 Web 应用
**技术栈**: Django + DRF + MySQL + JWT
**功能**: 用户管理、内容发布、投资组合、社区互动、管理审核