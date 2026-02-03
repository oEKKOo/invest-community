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
# 1. 安装依赖
pip install -r requirements.txt

# 2. 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 3. 创建超级用户
python manage.py createsuperuser

# 4. 启动服务器
python manage.py runserver
```

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