@echo off
echo 🛠️ Django 数据库修复工具
echo ================================
echo 此工具将解决 'Unknown column user.password' 错误

echo.
echo 第1步：清理旧的迁移文件...
if exist "accounts\migrations\0*.py" del /f /q "accounts\migrations\0*.py"
if exist "content\migrations\0*.py" del /f /q "content\migrations\0*.py"
if exist "portfolios\migrations\0*.py" del /f /q "portfolios\migrations\0*.py"
if exist "notifications\migrations\0*.py" del /f /q "notifications\migrations\0*.py"
if exist "reports\migrations\0*.py" del /f /q "reports\migrations\0*.py"
echo ✅ 迁移文件清理完成

echo.
echo 第2步：重新生成迁移文件...
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
echo 第3步：应用数据库迁移...
python manage.py migrate
if errorlevel 1 goto error

echo ✅ 数据库迁移完成

echo.
echo 第4步：创建超级用户...
set /p choice="是否创建超级用户？(y/n): "
if /i "%choice%"=="y" (
    python manage.py createsuperuser
)

echo.
echo ================================
echo 🎉 修复完成！
echo ================================
echo.
echo 下一步操作：
echo 1. 运行 'python manage.py runserver' 启动服务器
echo 2. 访问 http://127.0.0.1:8000/admin/ 测试管理后台
echo 3. 测试用户注册和登录功能
echo.
pause
goto end

:error
echo ❌ 执行过程中出现错误，请检查上面的错误信息
pause

:end