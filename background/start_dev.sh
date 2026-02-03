#!/bin/bash

echo "🚀 启动 Django 投研社区开发服务器"
echo "================================"

# 检查虚拟环境
if [ -f "venv/bin/activate" ]; then
    echo "🔧 激活虚拟环境..."
    source venv/bin/activate
fi

# 检查依赖
echo "📦 检查依赖包..."
if ! python -c "import django" &> /dev/null; then
    echo "❌ Django 未安装，正在安装依赖..."
    pip install -r requirements.txt
fi

# 数据库迁移
echo "🗄️ 检查数据库迁移..."
python manage.py makemigrations
python manage.py migrate

# 启动服务器
echo "🌐 启动开发服务器..."
echo ""
echo "服务器地址: http://127.0.0.1:8000/"
echo "管理后台: http://127.0.0.1:8000/admin/"
echo "API 文档: http://127.0.0.1:8000/api/"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "================================"
python manage.py runserver