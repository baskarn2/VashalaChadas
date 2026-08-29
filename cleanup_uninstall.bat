@echo off
title Vishalavrttavalih - Cleaner and Uninstaller
cd /d "%~dp0"

echo ============================================================
echo   विशालवृत्तावलिः (Viśālavṛttāvaliḥ) - Cleaner / Uninstaller
echo ============================================================
echo.
echo This utility will:
echo   1. Stop any running Vishalavrttavalih processes
echo   2. Remove temporary files, caches, and upload history
echo   3. Optionally remove the entire application folder
echo.
echo ============================================================
echo.

:: 1. Terminate running process if any
echo [1/3] Closing any active application instances...
taskkill /F /IM Vishalavrttavalih.exe >nul 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Vishalavrttavalih*" >nul 2>nul

:: 2. Clean local temp folders and caches
echo [2/3] Cleaning temporary files and caches...
if exist "tmp" (
    echo  - Removing tmp directory...
    rd /s /q "tmp" >nul 2>nul
)
if exist "__pycache__" (
    rd /s /q "__pycache__" >nul 2>nul
)
if exist "core\__pycache__" (
    rd /s /q "core\__pycache__" >nul 2>nul
)

:: Clean PyInstaller appdata caches if present
if exist "%LOCALAPPDATA%\pyinstaller" rd /s /q "%LOCALAPPDATA%\pyinstaller" >nul 2>nul
if exist "%APPDATA%\pyinstaller" rd /s /q "%APPDATA%\pyinstaller" >nul 2>nul

:: Clean optional .venv if in source mode
if exist ".venv" (
    echo.
    echo Found local virtual environment (.venv).
    choice /C YN /M "Do you want to remove the Python .venv environment as well?"
    if errorlevel 2 goto skip_venv
    rd /s /q ".venv"
    echo  - .venv removed.
:skip_venv
)

echo.
echo ============================================================
echo   Temporary caches and previous session data cleaned!
echo ============================================================
echo.

choice /C YN /M "Do you want to COMPLETELY uninstall and delete this folder from your PC?"
if errorlevel 2 (
    echo.
    echo Cleaning complete. The application folder was kept.
    echo Press any key to exit.
    pause >nul
    exit /b 0
)

echo.
echo [3/3] Removing entire application folder...
cd ..
set "TARGET_DIR=%~dp0"
set "TARGET_DIR=%TARGET_DIR:~0,-1%"

start /b "" cmd /c "timeout /t 2 /nobreak >nul & rd /s /q \"%TARGET_DIR%\""
echo.
echo Vishalavrttavalih has been uninstalled successfully.
timeout /t 3 >nul
exit /b 0
