# -*- coding: utf-8 -*-
"""生成 启动反谋财害命器.bat

两个坑（都踩过）：
1. cmd 在中文 Windows 上按 **GBK** 解析 .bat；文件若是 UTF-8，中文行会把后面的命令拆断
   （典型报错：'ythonw.exe" goto RUN' 不是内部或外部命令）→ 必须用 GBK 写盘。
2. `py -3` 在有 Python 3.14 的机器上可能报 "No suitable Python runtime found"，
   不能只靠它 → 逐个候选尝试，并用 `-c import sys` 真跑一次验证。
"""
from pathlib import Path

BAT = r'''@echo off
title FangMou
cd /d "%~dp0"

rem ================= 1) 免安装版优先：目录里有 exe 就直接跑
for %%F in (*.exe) do (
    start "" "%%~fF"
    exit /b 0
)

rem ================= 2) 源码版：已有 .venv 就用它
if exist ".venv\Scripts\pythonw.exe" goto RUN
if exist ".venv\Scripts\python.exe" goto RUNPY

rem ================= 3) 源码版：找一个能用的 Python
echo ==============================================
echo   首次运行，正在准备运行环境（只需一次，约 1-3 分钟）
echo ==============================================
echo.
set "PY="
call :TRY  py -3.11
if defined PY goto MAKEVENV
call :TRY  py -3
if defined PY goto MAKEVENV
call :TRY  python
if defined PY goto MAKEVENV
call :TRY  python3
if defined PY goto MAKEVENV
goto NOPY

:TRY
if defined PY exit /b 0
%~1 -c "import sys" >nul 2>nul
if not errorlevel 1 set "PY=%~1"
exit /b 0

:MAKEVENV
echo 使用 Python 命令：%PY%
%PY% -m venv .venv
if errorlevel 1 goto NOPY
if not exist ".venv\Scripts\python.exe" goto NOPY

echo 正在安装依赖（PySide6-Essentials、requests）...
".venv\Scripts\python.exe" -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 goto PIPFAIL
echo.
echo 环境就绪，正在启动...

:RUN
start "" ".venv\Scripts\pythonw.exe" "%~dp0souti.py"
exit /b 0

:RUNPY
start "" ".venv\Scripts\python.exe" "%~dp0souti.py"
exit /b 0

:PIPFAIL
echo.
echo [X] 依赖安装失败。请检查网络后重试，或手动执行：
echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
pause
exit /b 1

:NOPY
echo.
echo [X] 没有找到可用的 Python（3.10 或更高版本）。
echo.
echo 两个办法，任选其一：
echo   1) 用免安装版：解压后直接双击目录里的 exe，完全不需要 Python（推荐）
echo   2) 装 Python 3.11/3.12：https://www.python.org/downloads/
echo      安装时勾选 "Add python.exe to PATH"，装完重新双击本文件即可
echo.
echo 当前目录里没有 exe 的话，请从下载页重新下载「免安装版」：
echo   https://hanlinbachelor.github.io/fhcmd/
echo.
pause
exit /b 1
'''

out = Path(r"D:\hermes\261020搜题浮窗\启动反谋财害命器.bat")
data = BAT.replace("\n", "\r\n").encode("gbk", errors="replace")
out.write_bytes(data)
print(f"已写入 GBK 版 bat：{len(data)} 字节")
