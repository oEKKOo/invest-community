#!/usr/bin/env python
"""
数据库连接测试和初始化脚本
"""

import os
import sys
import subprocess
import mysql.connector
from mysql.connector import Error

def test_database_connection():
    """测试数据库连接"""
    print("🔍 正在测试数据库连接...")
    
    try:
        # 从用户输入获取数据库配置
        db_user = input("请输入MySQL用户名 (默认: root): ").strip() or 'root'
        db_password = input("请输入MySQL密码: ").strip()
        db_host = input("请输入MySQL主机地址 (默认: localhost): ").strip() or 'localhost'
        db_port = input("请输入MySQL端口号 (默认: 3306): ").strip() or '3306'
        db_name = 'community_db'
        
        # 测试连接
        connection = mysql.connector.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            database=db_name
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✅ 成功连接到MySQL服务器版本: {db_info}")
            print(f"✅ 成功连接到数据库: {db_name}")
            
            # 更新 Django settings.py 中的数据库配置
            update_django_settings(db_user, db_password, db_host, db_port, db_name)
            
            return True
            
    except Error as e:
        print(f"❌ 数据库连接失败: {e}")
        
        if "Unknown database" in str(e):
            print("\n💡 建议操作:")
            print("1. 登录MySQL: mysql -u root -p")
            print("2. 创建数据库: CREATE DATABASE community_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print("3. 重新运行此脚本")
            
        return False
        
    finally:
        if connection and connection.is_connected():
            connection.close()

def update_django_settings(user, password, host, port, db_name):
    """更新Django settings.py中的数据库配置"""
    settings_file = 'invest_backend/settings.py'
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换数据库配置
        old_config = """DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'community_db',  # 修改为您创建的数据库名
        'USER': 'root',
        'PASSWORD': 'password',  # 请修改为您的MySQL密码
        'HOST': 'localhost',
        'PORT': '3306',"""
        
        new_config = f"""DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '{db_name}',
        'USER': '{user}',
        'PASSWORD': '{password}',
        'HOST': '{host}',
        'PORT': '{port}',"""
        
        if old_config in content:
            content = content.replace(old_config, new_config)
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"✅ 已更新 {settings_file} 中的数据库配置")
        else:
            print(f"⚠️ 未找到预期的数据库配置格式，请手动修改 {settings_file}")
            
    except Exception as e:
        print(f"❌ 更新配置文件失败: {e}")

def run_django_migrations():
    """执行Django数据库迁移"""
    print("\n🗄️ 正在执行数据库迁移...")
    
    commands = [
        ("python manage.py makemigrations", "创建迁移文件"),
        ("python manage.py migrate", "执行数据库迁移"),
    ]
    
    for command, description in commands:
        print(f"\n执行: {description}")
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
    print("🚀 Django 项目数据库配置工具")
    print("="*50)
    
    # 测试数据库连接
    if not test_database_connection():
        return
    
    # 执行数据库迁移
    if not run_django_migrations():
        return
    
    # 询问是否创建超级用户
    create_superuser = input("\n是否创建管理员账号？(y/n): ").lower()
    if create_superuser in ['y', 'yes']:
        print("\n👤 创建管理员账号:")
        subprocess.run("python manage.py createsuperuser", shell=True)
    
    print("\n" + "="*50)
    print("🎉 数据库配置完成！")
    print("\n📝 下一步操作：")
    print("1. 运行 'python manage.py runserver' 启动服务器")
    print("2. 访问 http://127.0.0.1:8000/admin/ 进入管理后台")
    print("3. 访问 http://127.0.0.1:8000/api/ 测试API接口")

if __name__ == "__main__":
    main()