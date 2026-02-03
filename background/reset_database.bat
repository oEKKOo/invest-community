@echo off
chcp 65001 >nul
echo 🗄️ Django 数据库完全重置工具
echo ================================
echo 此工具将完全清理数据库和迁移历史
echo ⚠️  警告：这将删除所有数据！
echo ================================

set /p confirm="确认要继续吗？这将删除所有数据 (y/n): "
if /i not "%confirm%"=="y" (
    echo 操作已取消
    goto end
)

echo.
echo 第1步：清理迁移文件...
if exist "accounts\migrations\0*.py" del /f /q "accounts\migrations\0*.py"
if exist "content\migrations\0*.py" del /f /q "content\migrations\0*.py"
if exist "portfolios\migrations\0*.py" del /f /q "portfolios\migrations\0*.py"
if exist "notifications\migrations\0*.py" del /f /q "notifications\migrations\0*.py"
if exist "reports\migrations\0*.py" del /f /q "reports\migrations\0*.py"
echo ✅ 迁移文件清理完成

echo.
echo 第2步：清理数据库表和迁移历史...
echo 需要MySQL密码来清理数据库
set /p mysql_password="请输入MySQL密码: "

echo 正在连接数据库并清理表...
mysql -u root -p%mysql_password% -e "USE community_db; SET FOREIGN_KEY_CHECKS = 0; DROP TABLE IF EXISTS django_migrations; SHOW TABLES;" > temp_tables.txt 2>nul

if errorlevel 1 (
    echo ❌ 数据库连接失败，请检查密码
    del temp_tables.txt 2>nul
    goto error
)

echo 正在删除所有表...
mysql -u root -p%mysql_password% -e "USE community_db; SET FOREIGN_KEY_CHECKS = 0; DROP DATABASE community_db; CREATE DATABASE community_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

if errorlevel 1 (
    echo ❌ 数据库重建失败
    goto error
)

del temp_tables.txt 2>nul
echo ✅ 数据库完全清理完成

echo.
echo 第3步：重新生成所有迁移文件...

echo 正在为 accounts 创建迁移...
python manage.py makemigrations accounts
if errorlevel 1 goto error

echo 正在为 content 创建迁移...
python manage.py makemigrations content
if errorlevel 1 goto error

echo 正在为 portfolios 创建迁移...
python manage.py makemigrations portfolios
if errorlevel 1 goto error

echo 正在为 notifications 创建迁移...
python manage.py makemigrations notifications
if errorlevel 1 goto error

echo 正在为 reports 创建迁移...
python manage.py makemigrations reports
if errorlevel 1 goto error

echo ✅ 所有迁移文件创建完成

echo.
echo 第4步：应用所有迁移...
python manage.py migrate
if errorlevel 1 goto error

echo ✅ 数据库迁移完成

echo.
echo 第5步：创建超级用户...
set /p choice="是否创建超级用户？(y/n): "
if /i "%choice%"=="y" (
    python manage.py createsuperuser
)

echo.
echo ================================
echo 🎉 数据库重置完成！
echo ================================
echo.
echo 下一步操作：
echo 1. 运行 'python manage.py runserver' 启动服务器
echo 2. 访问 http://127.0.0.1:8000/admin/ 测试管理后台
echo 3. 测试用户注册和登录功能
echo.
goto end

:error
echo ❌ 执行过程中出现错误，请检查上面的错误信息
echo 💡 如果问题持续，请尝试手动执行以下步骤：
echo 1. 登录MySQL: mysql -u root -p
echo 2. 执行: DROP DATABASE community_db; CREATE DATABASE community_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
echo 3. 重新运行此脚本

:end
pause