@echo off
chcp 65001 >nul
title 停止集合竞价猎手
echo ==============================
echo    停止集合竞价猎手
echo ==============================
echo.

:: 查找并终止占用5001端口的进程
echo 正在停止服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "5001" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 终止所有python web/app.py进程
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *web/app*" >nul 2>&1

echo.
echo 服务已停止！
echo.
pause