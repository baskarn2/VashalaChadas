@echo off
title Vishalavrttavalih - Sanskrit Prosody Suite
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Starting Vishalavrttavalih (विशालवृत्तावलिः)...
"%PYTHON_EXE%" desktop.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred. If this is your first time, please run setup.bat first.
    pause
)
