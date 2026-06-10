# -*- coding: utf-8 -*-
"""集合竞价猎手启动器 - 双击运行"""

import subprocess
import time
import webbrowser
import os
import sys
import socket

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    # 切换到脚本所在目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    port = 5001
    url = f"http://localhost:{port}"
    
    # 检查是否已在运行
    if is_port_in_use(port):
        print(f"服务已在运行，打开浏览器: {url}")
        webbrowser.open(url)
        return
    
    print("正在启动集合竞价猎手...")
    
    # 启动Flask服务（后台运行）
    if sys.platform == 'win32':
        # Windows下用pythonw隐藏窗口
        subprocess.Popen(
            [sys.executable.replace('python.exe', 'pythonw.exe'), 'web/app.py'],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        subprocess.Popen([sys.executable, 'web/app.py'])
    
    # 等待服务启动
    print("等待服务启动...")
    for i in range(10):
        time.sleep(1)
        if is_port_in_use(port):
            print(f"启动成功！打开浏览器: {url}")
            webbrowser.open(url)
            return
    
    print("启动超时，请检查日志: server.log")

if __name__ == '__main__':
    main()