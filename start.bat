@echo off
TITLE Mimir Engine Launcher
COLOR 0A

echo ===================================================
echo               MIMIR ENGINE LAUNCHER               
echo ===================================================
echo.

:: 1. Auto-update repository
echo [1/4] Checking for Mimir Engine updates...
git pull origin main

:: 2. Python Virtual Environment Setup
echo.
echo [2/4] Verifying Python environment...
if not exist "venv\Scripts\activate.bat" (
    echo Creating clean Python virtual environment...
    if exist venv rmdir /s /q venv
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH.
        pause
        exit /b 1
    )
)

echo Installing/updating Python dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

:: 3. Pre-compiled Frontend Check
echo.
echo [3/4] Checking Svelte dashboard build...
if not exist "mimir-desktop\dist" (
    where npm >nul 2>nul
    if errorlevel 1 (
        echo WARNING: Node.js/npm is not installed.
        echo Please install Node.js v22+ to compile the Svelte UI.
    ) else (
        echo Building frontend static assets...
        cd mimir-desktop
        if not exist "node_modules" call npm install
        call npm run build
        cd ..
    )
)

:: 4. Launch Backend & Open Browser
echo.
echo [4/4] Launching Mimir Engine Middleware Proxy...
start http://localhost:8000
python app.py

pause
