@echo off
echo 正在启动 InvestHub Frontend...
echo.

echo 检查依赖...
if not exist "node_modules" (
    echo 安装依赖中...
    npm install
)

echo.
echo 启动开发服务器...
npm run dev

pause