# InvestHub 投研社区 · 后端（Django + DRF）

基于 **Django 4.2** 与 **Django REST Framework** 的股票/基金投资社区后端：用户与认证、UGC 内容（帖子/评论/板块）、投资组合与持仓、通知与私信、群组、举报与运营报表，以及 **A 股行情**（Tushare / Finnhub 接入、K 线、榜单、SSE 推送等）。

本目录为仓库中的 **`background/`** 子项目，与前端（如 `frontend/`）通过 REST API + JWT 对接。

---

## 目录

- [功能与业务模块](#功能与业务模块)
- [技术栈](#技术栈)
- [工程结构](#工程结构)
- [架构说明](#架构说明)
- [环境要求](#环境要求)
- [配置与环境变量](#配置与环境变量)
- [快速开始](#快速开始)
- [Celery 定时任务（可选）](#celery-定时任务可选)
- [A 股数据与常用管理命令](#a-股数据与常用管理命令)
- [API 与文档](#api-与文档)
- [数据库与模型](#数据库与模型)
- [权限与安全](#权限与安全)
- [开发与观测](#开发与观测)
- [生产部署要点](#生产部署要点)
- [故障排查](#故障排查)

---

## 功能与业务模块

| Django App | 职责概要 |
|------------|----------|
| **accounts** | 用户模型扩展、注册/登录/JWT 刷新与黑名单退出、个人资料、关注与 Feed、OAuth（微信/微博等）、KYC/风险测评、投资偏好；管理员用户治理路由在 `admin_urls` |
| **content** | 帖子/长文、评论与楼中楼、点赞收藏、话题与板块、附件与缩略图、搜索辅助、内容审核与风控字段、浏览量缓冲（可选 Redis） |
| **portfolios** | 投资组合、持仓、组合评论与更新日志、持仓日级快照（与行情 K 线联动） |
| **market_data** | 标的（Asset）元数据、行情快照、K 线/分时、批量报价、榜单、SSE、数据任务状态与触发接口；Tushare/Finnhub 服务层 |
| **notifications** | 站内通知；含与社区相关的异步/定时任务封装 |
| **reports** | 用户举报、运营侧报表与指标重建命令 |
| **messages** | 站内私信会话与消息 |
| **groups** | 小组、邀请、审核员等社群结构 |

项目级能力：**统一异常处理**（`invest_backend.exception_handler`）、**JWT**（access 约 1h、refresh 7d、轮换后黑名单）、**CORS**、**可选 Redis 缓存**、**可选 Celery Beat 调度**（行情与快照类任务）。

---

## 技术栈

| 层级 | 选型 |
|------|------|
| 语言 / 运行时 | Python 3.8+（建议 3.10+） |
| Web 框架 | Django 4.2 |
| API | Django REST Framework 3.14 |
| 认证 | djangorestframework-simplejwt（JWT + Token 黑名单） |
| 数据库 | MySQL 8.x（`utf8mb4`） |
| MySQL 驱动 | 默认 `mysqlclient`；`invest_backend/__init__.py` 中可选 **PyMySQL** 兜底（需自行 `pip install PyMySQL`） |
| 跨域 | django-cors-headers |
| 缓存 | 默认 LocMem；`USE_REDIS=true` 时使用 django-redis |
| 外部数据 | Tushare（A 股列表/K 线等）、Finnhub（视配置）、HTTP `requests` |
| 异步任务（可选） | Celery（未写入 `requirements/base.txt`，需按需安装并与 Redis 联调） |
| 图片 | Pillow |

依赖文件：

- **`requirements.txt`**：默认指向 **开发依赖**（`requirements/dev.txt` → `base.txt` + debug toolbar）。
- **`requirements/prod.txt`**：生产安装（`base.txt`，无 debug-toolbar）。

---

## 工程结构

```
background/
├── manage.py                      # Django 入口；默认 DJANGO_SETTINGS_MODULE=invest_backend.settings.dev
├── requirements.txt               # 默认 dev 依赖入口
├── requirements/
│   ├── base.txt                   # 核心依赖
│   ├── dev.txt                    # 开发（含 django-debug-toolbar）
│   └── prod.txt                   # 生产
├── start_dev.bat / start_dev.sh   # 本地启动脚本（迁移 + runserver）
├── invest_backend/                # 项目包
│   ├── settings/
│   │   ├── base.py                # 公共配置（DB/JWT/缓存/日志/Celery 调度等）
│   │   ├── dev.py                 # 本地开发（DEBUG、默认 CORS、Debug Toolbar）
│   │   └── prod.py                # 生产（强制 ALLOWED_HOSTS、安全 Cookie/HSTS 等）
│   ├── settings.py                # 兼容入口 → 当前 re-export dev
│   ├── urls.py                    # 根路由：admin、api、静态媒体（DEBUG）
│   ├── wsgi.py / asgi.py
│   ├── celery.py                  # Celery 应用（可选；未安装 celery 时不影响启动）
│   ├── exception_handler.py       # DRF 统一异常处理
│   ├── api_exceptions.py / api_response.py
│   └── permissions.py
├── accounts/                      # 用户与认证
├── content/                       # UGC 内容
├── portfolios/                    # 组合与持仓
├── market_data/                   # 行情与资产
├── notifications/
├── reports/
├── messages/
├── groups/
├── media/                         # 用户上传（开发环境本地）
└── staticfiles/                   # collectstatic 输出（部署）
```

---

## 架构说明

- **前后端分离**：浏览器或 `frontend/` 通过 HTTPS 调用 `/api/...`，使用 **Bearer JWT**。
- **路由聚合**：`invest_backend/urls.py` 将各业务 App 的 `urls.py` 挂载到 `api/`、`api/auth/`、`api/users/`、`api/admin/`、`api/feed/` 等前缀（与 `接口文档.mdc` 一致）。
- **行情路由**：`market_data` 与 `content` 下资产相关路径通过 **不同后缀** 区分（如 `assets/<id>/` 与 `assets/<id>/quote/`）。
- **设置拆分**：`base` 放共享配置；**开发**用 `invest_backend.settings.dev`；**生产**应使用 `invest_backend.settings.prod` 并设置环境变量（见下文）。
- **缓存策略**：单机开发可用 LocMem；**多 Gunicorn worker / 多机** 建议 `USE_REDIS=true`，否则缓存与部分行情逻辑无法在进程间共享。
- **浏览量**：可选 `VIEW_COUNT_USE_REDIS_BUFFER`（依赖 Redis），通过 `flush_view_count_buffer` 合并回 MySQL，减轻高频 UPDATE。

---

## 环境要求

- **Python** 3.8+
- **MySQL** 8.0+，字符集建议 `utf8mb4_unicode_ci`
- **pip** / **venv**（推荐）
- 可选：**Redis**（缓存、浏览量缓冲、Celery Broker）
- 可选：**Tushare Token**、**Finnhub API Key**（行情与导入脚本）

---

## 配置与环境变量

在 `background/` 下放置 **`.env`**（纯 `KEY=VALUE` 格式）。`settings/base.py` 会优先尝试 `python-dotenv` 加载；未安装时使用内置简易解析。

### Django 与安全

| 变量 | 说明 |
|------|------|
| `DJANGO_SECRET_KEY` | 生产必须替换随机密钥 |
| `DJANGO_DEBUG` | `true`/`false`；生产务必 `false` |
| `DJANGO_ALLOWED_HOSTS` | 逗号分隔，生产 **必填**（`prod.py` 会校验） |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | 含协议与域名，HTTPS 前端源 |
| `DJANGO_SETTINGS_MODULE` | 本地默认 `invest_backend.settings.dev`；生产建议 `invest_backend.settings.prod` |
| `DJANGO_ENABLE_FILE_LOG` | 是否写入 `django.log`（路径见 `DJANGO_LOG_DIR`） |
| `DJANGO_LOG_LEVEL` | 如 `INFO`、`DEBUG` |
| `DJANGO_API_TIMING_LOG` | 接口耗时日志开关（见下文「开发与观测」） |

### 数据库

支持两套命名（优先 `DJANGO_DB_*`，否则回退 `DB_*`）：

| 变量 | 默认（base） |
|------|----------------|
| `DJANGO_DB_NAME` / `DB_NAME` | `community_db` |
| `DJANGO_DB_USER` / `DB_USER` | `root` |
| `DJANGO_DB_PASSWORD` / `DB_PASSWORD` | 空 |
| `DJANGO_DB_HOST` / `DB_HOST` | `127.0.0.1` |
| `DJANGO_DB_PORT` / `DB_PORT` | `3306` |

### CORS

| 变量 | 说明 |
|------|------|
| `CORS_ALLOWED_ORIGINS` | 逗号分隔，如 `http://localhost:5173` |
| `CORS_ALLOW_CREDENTIALS` | 默认 `true` |

### Redis 与缓存

| 变量 | 说明 |
|------|------|
| `USE_REDIS` | `true` 启用 django-redis |
| `REDIS_URL` | 默认 `redis://127.0.0.1:6379/1` |
| `VIEW_COUNT_USE_REDIS_BUFFER` | 需 `USE_REDIS=true`；帖子浏览量 Redis 缓冲 |

### 行情与业务 TTL（节选，均可选覆盖）

| 变量 | 含义 |
|------|------|
| `FINNHUB_API_KEY` | Finnhub 密钥（未配置时部分能力降级） |
| `TUSHARE_API_TOKEN` | Tushare Token（A 股导入/日更） |
| `TUSHARE_REQUEST_DELAY` | 请求间隔，默认 `0.4` 秒 |
| `DASHBOARD_OVERVIEW_CACHE_TTL` / `MARKET_RANKINGS_CACHE_TTL` / `KLINE_API_CACHE_TTL` 等 | 各接口短缓存秒数 |
| `GLOBAL_SEARCH_CACHE_TTL` / `ADMIN_STATS_CACHE_TTL` / `BOARD_TREE_CACHE_TTL` | 搜索、管理统计、板块树缓存 |

### 邮件与短信（找回密码/验证码等）

`EMAIL_*`、`SMS_PROVIDER`、`TWILIO_*` 等见 `settings/base.py`。

### OAuth

`WECHAT_*`、`WEIBO_*` 等见 `settings/base.py`。

### Celery

| 变量 | 说明 |
|------|------|
| `CELERY_BROKER_URL` | 默认 `redis://127.0.0.1:6379/0` |
| `CELERY_RESULT_BACKEND` | 默认与 Broker 相同 |
| `CELERY_TASK_ALWAYS_EAGER` | `true` 时同步执行（测试用） |

**`.env` 最小示例（本地）**：

```env
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=dev-only-change-me

DB_NAME=community_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306

USE_REDIS=false
FINNHUB_API_KEY=
TUSHARE_API_TOKEN=
```

---

## 快速开始

### 1. 创建数据库

```sql
CREATE DATABASE community_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 虚拟环境与依赖

```bash
cd background
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
# 生产: pip install -r requirements/prod.txt
```

### 3. 环境文件

在 `background/.env` 中配置数据库与密钥（见上节）。仓库根目录若未提供 `.env.example`，可直接复制上文模板。

### 4. 迁移与管理账号

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. 启动开发服务器

```bash
python manage.py runserver
```

或使用脚本：

- **Windows**：`start_dev.bat`（会尝试加载 `.venv`/`venv`、读取 `.env`、安装依赖、迁移、启动）
- **Linux/macOS**：`chmod +x start_dev.sh && ./start_dev.sh`

### 常用地址

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:8000/admin/ | Django Admin |
| http://127.0.0.1:8000/api/ | API 前缀（各子路径见各 app `urls.py`） |
| http://127.0.0.1:8000/__debug__/ | Django Debug Toolbar（DEBUG 且已安装 dev 依赖时） |
| http://127.0.0.1:8000/api/market/status/ | 行情任务/状态检测（示例） |

**PowerShell 临时环境变量示例**（未使用 `.env` 时）：

```powershell
cd D:\invest\background
$env:FINNHUB_API_KEY="your_key"
$env:USE_REDIS="false"
python manage.py runserver
```

---

## Celery 定时任务（可选）

`invest_backend/celery.py` 在已安装 **Celery** 时注册应用，并自动发现 `market_data.celery_tasks`、`notifications.community_tasks` 等。`settings/base.py` 中 `CELERY_BEAT_SCHEDULE` 包含示例节拍：热门报价刷新、日 K 同步、持仓快照填充、行情快照清理等。

```bash
# 需自行: pip install celery
# 并确保 Redis 与 CELERY_BROKER_URL 可用

celery -A invest_backend worker -l info
celery -A invest_backend beat -l info
```

未安装 Celery 时，仍可用 **管理命令**完成同类数据任务（见下节）。

---

## A 股数据与常用管理命令

> 依赖 **`TUSHARE_API_TOKEN`**（`.env`）。日 K 一般在 A 股收盘后落库，日更建议 **16:30 后**执行。

### 阶段一：首次初始化（新环境一次）

```bash
python manage.py import_cn_stocks --kline --quote --days 365
python manage.py fill_holding_snapshots --days 365
```

### 阶段二：每日收盘后

```bash
python manage.py import_cn_stocks --kline-only --days 1
python manage.py fill_holding_snapshots --days 1
```

### 阶段三：补缺 / 异常修复

```bash
python manage.py import_cn_stocks --kline-only --days 30
python manage.py fill_holding_snapshots --days 30
```

### 其他实用命令

| 命令 | 说明 |
|------|------|
| `flush_view_count_buffer` | 将 Redis 中缓冲的帖子浏览量写回 DB（需开启 `VIEW_COUNT_USE_REDIS_BUFFER`） |
| `import_cn_stocks --codes 600519,000858 --kline --quote` | 指定代码测试 |
| `import_cn_stocks --quote-only` | 仅刷新行情快照 |
| `fill_holding_snapshots --user-id N --force` | 指定用户强制重建快照 |
| `run_daily_market_jobs` | 封装日常行情相关作业（见命令帮助） |
| `rebuild_follow_feed` / `rebuild_user_levels` | 账户侧 Feed 与用户等级 |
| `rebuild_community_metrics` / `rebuild_behavior_daily` / `refresh_topic_metrics` | 报表与话题指标 |
| `seed_realistic` | 生成较真实测试数据（开发用） |
| `db_explain_hot_paths` | SQL 热点路径自检（content） |

更完整的参数说明见各命令 `python manage.py <command> --help`。

---

## API 与文档

- **线上联调**：以仓库内维护的接口说明为准：  
  `background/.cursor/rules/接口文档.mdc`  
  （含认证、用户、帖子、资产与行情、组合、通知、举报、管理端等章节。）
- **URL 入口**：`invest_backend/urls.py`  
  - `api/auth/` … 注册登录 OAuth KYC 等  
  - `api/users/`、`api/feed/`、`api/admin/`  
  - `api/` 下 content / portfolios / notifications / reports / messages / groups / market_data 等

**market_data 示例路径**（与 `market_data/urls.py` 一致）：

- `GET /api/assets/<id>/quote/`、`kline/`、`intraday/`
- `POST /api/assets/quotes/`（批量）
- `GET /api/assets/<id>/quote/stream/`（SSE）
- `GET /api/market/rankings/`、`GET /api/market/status/`

---

## 数据库与模型

- 自定义用户：**`AUTH_USER_MODEL = accounts.User`**
- 核心业务表分布在各 App 的 `models.py`；表清单与关系说明见维护文档：  
  `background/.cursor/rules/数据库.mdc`

迁移：

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 权限与安全

- **默认 DRF 权限**：`IsAuthenticated`（匿名可访问的接口在各自 View 上显式放开）。
- **JWT**：Access + Refresh；轮换后旧 Refresh 进黑名单（`rest_framework_simplejwt.token_blacklist`）。
- **角色与治理**：普通用户与管理员能力分路由与权限类控制（如 `api/admin/`、内容审核、举报处置）。
- **生产**：务必使用 **`invest_backend.settings.prod`**，配置 `DJANGO_ALLOWED_HOSTS`、`DJANGO_SECRET_KEY`、HTTPS 相关安全项（见 `settings/prod.py`）。

---

## 开发与观测

- **Django Debug Toolbar**：`DEBUG=True` 且安装 `requirements/dev.txt` 时，访问 `/__debug__/`
- **接口耗时**：Logger `investhub.api_timing`；`DEBUG=True` 时默认启用细节见代码，生产可用 `DJANGO_API_TIMING_LOG` 控制
- **行情表索引**：说明与 `EXPLAIN` 思路见仓库 **`docs/mysql_quote_snapshot_indexes.md`**
- **数据库热点**：`python manage.py db_explain_hot_paths`（content）

---

## 生产部署要点

1. `export DJANGO_SETTINGS_MODULE=invest_backend.settings.prod`（或在 systemd/supervisor 环境中等价配置）
2. `DJANGO_DEBUG=false`、`DJANGO_ALLOWED_HOSTS`、`DJANGO_SECRET_KEY`、数据库与 `CORS_ALLOWED_ORIGINS`
3. `pip install -r requirements/prod.txt`
4. `python manage.py collectstatic`
5. 使用 **Gunicorn + Nginx**（或同类）托管 WSGI，配置反向代理与 TLS
6. 建议 **`USE_REDIS=true`**，并按需开启 **Celery Beat** 做行情与日终任务
7. 媒体文件使用对象存储或 Nginx 直出 `MEDIA_ROOT`（按规模选择）

`wsgi.py` 默认仍指向 `invest_backend.settings.dev`，生产环境务必通过 **环境变量** 覆盖 `DJANGO_SETTINGS_MODULE`。

---

## 故障排查

| 现象 | 建议 |
|------|------|
| 无法连接数据库 | 检查 `DB_*` / `DJANGO_DB_*`、MySQL 监听、用户权限、防火墙 |
| `mysqlclient` 安装失败 | Windows 可尝试预编译 wheel；或使用 **PyMySQL**（`pip install PyMySQL`，与 `invest_backend/__init__.py` 逻辑一致） |
| 跨域失败 | 配置 `CORS_ALLOWED_ORIGINS`，与前端实际 origin 完全一致（含协议与端口） |
| 多进程缓存不一致 | 开发外务必将 `USE_REDIS=true` |
| 行情全为空 | 检查 `TUSHARE_API_TOKEN` / `FINNHUB_API_KEY` 是否配置；是否已执行 `import_cn_stocks` |
| 生产启动报 `ALLOWED_HOSTS` | `prod` 设置要求显式配置 `DJANGO_ALLOWED_HOSTS` |

---

## 许可证与说明

本后端为毕业设计/投研社区工程的一部分：**Django + DRF + MySQL + JWT**，可扩展 **Redis、Celery、第三方行情**。若你维护公开 GitHub 仓库，可将本 README 作为 **`background/`** 目录的展示页；更细的接口字段与示例以 **`接口文档.mdc`** 为准。
