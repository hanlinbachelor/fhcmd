@echo off
chcp 65001 >nul
title 反谋财害命器 · 公网隧道（关掉就断）
cd /d "%~dp0"

set "PY=..\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo 正在准备公网地址…
echo.
"%PY%" tunnel.py
echo.
echo 隧道已结束。按任意键关闭窗口。
pause >nul
