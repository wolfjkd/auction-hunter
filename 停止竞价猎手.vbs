' 集合竞价猎手停止器
' 双击运行，停止服务

Set WshShell = CreateObject("WScript.Shell")

' 停止占用5001端口的进程
WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr "":5001"" ^| findstr ""LISTENING""') do taskkill /F /PID %a", 0, True

' 停止所有pythonw进程
WshShell.Run "cmd /c taskkill /F /IM pythonw.exe", 0, True

WScript.Echo "集合竞价猎手已停止！"