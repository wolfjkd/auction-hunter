' 集合竞价猎手启动器
' 双击运行，自动启动服务并打开浏览器

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 获取脚本所在目录
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath

' 检查端口是否已被占用
Set objExec = WshShell.Exec("cmd /c netstat -ano | findstr "":5001"" | findstr ""LISTENING""")
strOutput = objExec.StdOut.ReadAll()

If Len(strOutput) > 0 Then
    ' 服务已在运行
    WshShell.Run "http://localhost:5001"
    WScript.Quit
End If

' 启动服务（隐藏窗口）
WshShell.Run "cmd /c pythonw web/app.py", 0, False

' 等待服务启动
WScript.Sleep 3000

' 打开浏览器
WshShell.Run "http://localhost:5001"

' 显示提示
WScript.Echo "集合竞价猎手已启动！" & vbCrLf & vbCrLf & "访问地址: http://localhost:5001"