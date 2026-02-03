#!/usr/bin/env python
"""
数据库修复脚本 - 解决用户表结构问题
"""

import os
import sys
import subprocess
import mysql.connector
from mysql.connector import Error
import shutil
from pathlib import Path

def run_command(command, description):
    """执行命令并显示结果"""
    print(f"\n{'='*50}")
    print(f"正在执行: {description}")
    print(f"命令: {command}")
    print('='*50)
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode == 0:
        print(f"✅ {description} - 成功")
        if result.stdout:
            print(result.stdout)
        return True
    else:
        print(f"❌ {description} - 失败")
        if result.stderr:
            print(result.stderr)
        if result.stdout:
            print(result.stdout)
        return False

def clean_migration_files():
    """清理旧的迁移文件"""
    print("\n🧹 清理旧的迁移文件...")
    
    apps = ['accounts', 'content', 'portfolios', 'notifications', 'reports']
    
    for app in apps:
        migrations_dir = Path(app) / 'migrations'
        if migrations_dir.exists():
            # 保留 __init__.py，删除其他迁移文件
            for file in migrations_dir.glob('0*.py'):
                try:
                    file.unlink()
                    print(f"删除: {file}")
                except Exception as e:
                    print(f"删除失败 {file}: {e}")

def clean_database_tables():
    """清理数据库表"""
    print("\n🗄️ 清理数据库表...")
    
    # 从用户获取数据库配置
    db_password = input("请输入MySQL密码: ").strip()
    
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password=db_password,
            database='community_db'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 获取所有表名
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            if tables:
                print("找到以下表，将被删除:")
                for table in tables:
                    print(f"  - {table[0]}")
                
                confirm = input("\n确认删除所有表？(y/n): ").lower()
                if confirm in ['y', 'yes']:
                    # 禁用外键检查
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                    
                    # 删除所有表
                    for table in tables:
                        cursor.execute(f"DROP TABLE IF EXISTS `{table[0]}`")
                        print(f"✅ 删除表: {table[0]}")
                    
                    # 恢复外键检查
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                    connection.commit()
                    print("✅ 所有表删除完成")
                else:
                    print("❌ 用户取消操作")
                    return False
            else:
                print("✅ 数据库中没有表需要删除")
            
            return True
            
    except Error as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def main():
    print("🛠️ Django 数据库修复工具")
    print("="*60)
    print("此工具将解决 'Unknown column user.password' 错误")
    print("="*60)
    
    # 第一步：清理迁移文件
    clean_migration_files()
    
    # 第二步：清理数据库表
    if not clean_database_tables():
        print("❌ 数据库清理失败，请手动清理后重试")
        return
    
    # 第三步：重新生成迁移文件
    apps = ['accounts', 'content', 'portfolios', 'notifications', 'reports']
    
    for app in apps:
        if not run_command(f"python manage.py makemigrations {app}", f"为 {app} 创建迁移文件"):
            print(f"❌ {app} 迁移文件创建失败")
            return
    
    # 第四步：应用迁移
    if not run_command("python manage.py migrate", "应用数据库迁移"):
        print("❌ 数据库迁移失败")
        return
    
    # 第五步：创建超级用户
    print("\n" + "="*50)
    create_superuser = input("是否创建超级用户？(y/n): ").lower()
    if create_superuser in ['y', 'yes']:
        run_command("python manage.py createsuperuser", "创建超级用户")
    
    print("\n" + "="*60)
    print("🎉 数据库修复完成！")
    print("\n📝 下一步操作：")
    print("1. 运行 'python manage.py runserver' 启动服务器")
    print("2. 访问 http://127.0.0.1:8000/admin/ 测试管理后台")
    print("3. 测试用户注册和登录功能")

if __name__ == "__main__":
    main()