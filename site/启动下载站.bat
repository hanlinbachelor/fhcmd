@echo off
chcp 65001 >nul
title 反谋财害命器 · 版本下载站
cd /d "%~dp0"

set "PY=..\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo 正在启动下载站（默认 80 端口，地址不用带端口号）...
start "" http://127.0.0.1/
"%PY%" serve.py
echo.
echo 服务已停止。按任意键关闭窗口。
pause >nul
