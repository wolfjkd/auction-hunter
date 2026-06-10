@echo off
chcp 65001 >nul
title 集合竞价猎手 v1.0.0
color 0A

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║       集合竞价猎手 v1.0.0             ║
echo  ╚═══════════════════════════════════════╝
echo.

cd /d "%~dp0"
echo [信息] 工作目录: %cd%
echo.

:: 检查Python是否可用
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请确保已安装Python并添加到PATH
    echo.
    pause
    exit /b 1
)

:: 检查是否已有进程在运行
netstat -ano | findstr ":5001" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [提示] 服务已在运行中！
    echo.
    echo 正在打开浏览器...
    start http://localhost:5001
    echo.
    echo 按任意键关闭此窗口...
    pause >nul
    exit
)

:: 启动服务
echo [启动] 正在启动竞价猎手服务...
echo [启动] 请稍候，首次启动可能需要几秒...
echo.

start "集合竞价猎手服务" /min python web/app.py

:: 等待服务启动
echo [等待] 等待服务启动...
timeout /t 5 /nobreak >nul

:: 检查服务是否启动成功
netstat -ano | findstr ":5001" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo.
    echo  ╔═══════════════════════════════════════╗
    echo  ║          启动成功！                   ║
    echo  ╠═══════════════════════════════════════╣
    echo  ║  访问地址: http://localhost:5001      ║
    echo  ╚═══════════════════════════════════════╝
    echo.
    echo 正在打开浏览器...
    start http://localhost:5001
) else (
    echo.
    echo  ╔═══════════════════════════════════════╗
    echo  ║          启动失败！                   ║
    echo  ╠═══════════════════════════════════════╣
    echo  ║  请检查server.log查看错误信息         ║
    echo  ╚═══════════════════════════════════════╝
    echo.
    if exist server.log (
        echo 最后几行日志:
        echo ----------------------------------------
        powershell -Command "Get-Content server.log -Tail 10"
        echo ----------------------------------------
    )
)

echo.
echo ┌───────────────────────────────────────┐
echo │  提示:                                 │
echo │  - 关闭此窗口不影响服务运行            │
echo │  - 停止服务请运行"停止竞价猎手.bat"    │
echo └───────────────────────────────────────┘
echo.
pause