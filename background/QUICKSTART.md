# 🚀 投研社区后端快速启动指南

## 📋 环境准备检查清单

在开始之前，请确保已安装以下软件：

- ✅ Python 3.8+ 
- ✅ MySQL 8.0+
- ✅ Git（可选）

## 🗄️ 数据库准备

### 1. 登录 MySQL 并创建数据库

```sql
-- 登录 MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE invest_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建专用用户（可选，建议）
CREATE USER 'invest_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON invest_db.* TO 'invest_user'@'localhost';
FLUSH PRIVILEGES;

-- 退出 MySQL
EXIT;
```

## ⚡ 一键启动（推荐）

### Windows 用户

```cmd
# 进入项目目录
cd d:\invest\background

# 运行启动脚本（自动完成所有配置）
start_dev.bat
```

### Linux/Mac 用户

```bash
# 进入项目目录
cd /path/to/invest/background

# 给脚本执行权限并运行
chmod +x start_dev.sh
./start_dev.sh
```

## 🛠️ 手动配置步骤

如果一键启动遇到问题，可以按以下步骤手动配置：

### 1. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. 安装依赖

```bash
# 安装 Python 依赖包
pip install -r requirements.txt

# 如果遇到 mysqlclient 安装问题（Windows）：
# 下载对应版本的 whl 文件安装
# 或者使用 PyMySQL 替代：pip install PyMySQL
```

### 3. 配置环境变量

```bash
# 复制环境配置文件
copy .env.example .env     # Windows
cp .env.example .env       # Linux/Mac

# 编辑 .env 文件，配置数据库连接：
DB_NAME=invest_db
DB_USER=root               # 或你的 MySQL 用户名
DB_PASSWORD=your_password  # 你的 MySQL 密码
DB_HOST=localhost
DB_PORT=3306
```

### 4. 数据库初始化

```bash
# 创建数据库迁移文件
python manage.py makemigrations

# 执行数据库迁移
python manage.py migrate

# 创建超级用户账号
python manage.py createsuperuser
```

### 5. 启动开发服务器

```bash
# 启动 Django 开发服务器
python manage.py runserver

# 服务器将在以下地址启动：
# http://127.0.0.1:8000/
```

## 🌐 访问地址

服务器启动成功后，可以访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| **API 根路径** | http://127.0.0.1:8000/api/ | REST API 接口 |
| **管理后台** | http://127.0.0.1:8000/admin/ | Django Admin 界面 |
| **用户注册** | http://127.0.0.1:8000/api/auth/register/ | POST 请求注册 |
| **用户登录** | http://127.0.0.1:8000/api/auth/login/ | POST 请求登录 |

## 🔧 常见问题解决

### 1. MySQL 连接问题

```bash
# 检查 MySQL 服务是否启动
# Windows: 服务管理器中检查 MySQL 服务
# Linux: systemctl status mysql

# 测试数据库连接
mysql -u root -p -h localhost
```

### 2. mysqlclient 安装失败（Windows）

```bash
# 方案1：安装预编译包
pip install https://download.lfd.uci.edu/pythonlibs/archived/mysqlclient-2.1.1-cp39-cp39-win_amd64.whl

# 方案2：使用 PyMySQL 替代
pip install PyMySQL
# 然后在 invest_backend/__init__.py 中添加：
# import pymysql
# pymysql.install_as_MySQLdb()
```

### 3. 端口占用问题

```bash
# 检查端口占用
netstat -ano | findstr :8000     # Windows
lsof -i :8000                    # Linux/Mac

# 使用其他端口启动
python manage.py runserver 8001
```

### 4. 权限问题

```bash
# 确保对项目文件夹有写权限
# Windows: 右键项目文件夹 -> 属性 -> 安全
# Linux: chmod -R 755 /path/to/project
```

## 📊 验证安装

### 1. 测试 API 接口

使用 curl 或 Postman 测试：

```bash
# 测试用户注册接口
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123","password_confirm":"testpass123"}'

# 测试登录接口
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

### 2. 访问管理后台

1. 打开浏览器访问 http://127.0.0.1:8000/admin/
2. 使用创建的超级用户账号登录
3. 可以查看和管理所有数据模型

## 🎯 下一步操作

1. **配置前端项目**：确保前端能正确连接到后端 API
2. **添加测试数据**：通过 Admin 界面或 API 添加一些测试内容
3. **API 测试**：使用 Postman 或类似工具测试各个 API 端点
4. **阅读 API 文档**：查看 `README.md` 中的 API 接口说明

## 🆘 获取帮助

如果遇到问题：

1. 检查终端错误信息
2. 查看 Django 日志输出
3. 确认数据库连接配置
4. 检查防火墙和端口设置

---

**🎉 恭喜！投研社区后端环境配置完成！**