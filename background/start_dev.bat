@echo off
setlocal enabledelayedexpansion
echo 启动 Django 投研社区开发服务器
echo ================================

REM 检查虚拟环境（优先 .venv，其次 venv）
if exist ".venv\Scripts\activate.bat" (
    echo [1] 激活虚拟环境 .venv ...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [1] 激活虚拟环境 venv ...
    call venv\Scripts\activate.bat
) else (
    echo [1] 未找到虚拟环境，使用系统 Python
)

REM ── 加载 .env 文件中的环境变量 ──────────────────────────────────────────────
if exist ".env" (
    echo [2] 加载 .env 环境变量...
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        set "_line=%%A"
        if not "!_line!"=="" (
            set "_first=!_line:~0,1!"
            if not "!_first!"=="#" (
                set "%%A=%%B"
            )
        )
    )
    echo     .env 已加载（FINNHUB_API_KEY 已就绪）
) else (
    echo [警告] 未找到 .env 文件！
    echo        请在 background\ 目录创建 .env 文件，内容：
    echo        FINNHUB_API_KEY=你的Key
    echo        USE_REDIS=false
)

REM 检查依赖
echo [3] 检查依赖包...
pip show Django >nul 2>&1
if errorlevel 1 (
    echo ❌ Django 未安装，正在安装依赖...
    pip install -r requirements/dev.txt
)

REM 数据库迁移
echo [4] 检查数据库迁移...
python manage.py makemigrations
python manage.py migrate

REM 启动服务器
echo [5] 启动开发服务器...
echo.
echo 服务器地址:   http://127.0.0.1:8000/
echo 管理后台:     http://127.0.0.1:8000/admin/
echo 市场状态检测: http://127.0.0.1:8000/api/market/status/
echo 行情测试:     http://127.0.0.1:8000/api/assets/1/quote/
echo.
echo 按 Ctrl+C 停止服务器
echo ================================
python manage.py runserver

pause