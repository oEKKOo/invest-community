#!/usr/bin/env python
"""
Django 项目初始化脚本
用于创建数据库、迁移模型和创建超级用户
"""

import os
import sys
import subprocess

def run_command(command, description):
    """执行命令并显示描述"""
    print(f"\n{'='*50}")
    print(f"正在执行: {description}")
    print(f"命令: {command}")
    print('='*50)
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - 成功")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ {description} - 失败")
        if result.stderr:
            print(result.stderr)
        return False
    return True

def main():
    print("🚀 Django 投研社区后端项目初始化")
    print("="*60)
    
    # 检查 Python 和 Django
    if not run_command("python --version", "检查 Python 版本"):
        print("请先安装 Python")
        return
    
    # 安装依赖
    if not run_command("pip install -r requirements.txt", "安装 Python 依赖包"):
        print("请检查 requirements.txt 文件")
        return
    
    # 数据库迁移
    if not run_command("python manage.py makemigrations", "创建数据库迁移文件"):
        return
    
    if not run_command("python manage.py migrate", "执行数据库迁移"):
        print("请检查数据库连接配置")
        return
    
    # 创建超级用户（可选）
    print("\n" + "="*50)
    create_superuser = input("是否创建超级用户账号？(y/n): ").lower()
    if create_superuser in ['y', 'yes']:
        run_command("python manage.py createsuperuser", "创建超级用户")
    
    # 收集静态文件（生产环境）
    if input("\n是否收集静态文件？(y/n): ").lower() in ['y', 'yes']:
        run_command("python manage.py collectstatic --noinput", "收集静态文件")
    
    print("\n" + "="*60)
    print("🎉 项目初始化完成！")
    print("\n📝 下一步操作：")
    print("1. 复制 .env.example 为 .env 并配置数据库信息")
    print("2. 运行 'python manage.py runserver' 启动开发服务器")
    print("3. 访问 http://127.0.0.1:8000/admin/ 进入管理后台")
    print("4. 访问 http://127.0.0.1:8000/api/ 测试 API 接口")

if __name__ == "__main__":
    main()