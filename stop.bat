@echo off
taskkill /F /IM pythonw.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
echo Stopped.
