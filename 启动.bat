@echo off
cd /d "%~dp0"
start pythonw web.app
timeout /t 3
start http://localhost:5001
