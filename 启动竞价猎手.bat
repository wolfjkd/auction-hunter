@echo off
chcp 65001 >nul
title 集合竞价猎手
echo ==============================
echo    集合竞价猎手 v1.0.0
echo ==============================
echo.
echo 正在启动...
echo.

cd /d "%~dp0"

:: 检查是否已有进程在运行
netstat -ano | findstr "5001" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [提示] 服务已在运行，正在打开浏览器...
    start http://localhost:5001
    pause
    exit
)

:: 启动服务
start /b python web/app.py > server.log 2>&1

:: 等待服务启动
echo 等待服务启动...
timeout /t 3 /nobreak >nul

:: 打开浏览器
echo 启动成功！正在打开浏览器...
start http://localhost:5001

echo.
echo ==============================
echo 服务已启动，关闭此窗口不影响运行
echo 如需停止服务，请运行"停止竞价猎手.bat"
echo ==============================
echo.
pause