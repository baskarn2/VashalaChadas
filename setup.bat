@echo off
title Setup Vishalavrttavalih
cd /d "%~dp0"

echo ============================================================
echo   Installing Dependencies for Vishalavrttavalih
echo ============================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not found in your system PATH.
    echo Please install Python 3.8+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Creating virtual environment (.venv)...
python -m venv .venv

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing required packages...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pywebview

echo.
echo ============================================================
echo   Setup Complete! You can now double-click run.bat to start.
echo ============================================================
pause
