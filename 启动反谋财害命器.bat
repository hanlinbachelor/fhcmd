@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo [X] venv not found: %~dp0.venv
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "%~dp0souti.py"
