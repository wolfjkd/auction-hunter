@echo off
cd /d "%~dp0"
start "" "C:\Users\wolfj\.workbuddy\binaries\python\versions\3.13.12\pythonw.exe" web/app.py
ping -n 4 127.0.0.1 >nul
start http://localhost:5001
