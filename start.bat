@echo off
TITLE Mimir Engine Launcher
COLOR 0A

echo ===================================================
echo               MIMIR ENGINE LAUNCHER               
echo ===================================================
echo.

:: 1. Auto-update repository
echo [1/5] Checking for Mimir Engine updates...
git pull origin main

:: 2. Database Sanity Check
echo.
echo [2/5] Verifying PostgreSQL (pgvector) is running...
docker ps | findstr "mimir" >nul 2>nul
if errorlevel 1 (
    echo WARNING: Mimir Database container not found running in Docker.
    echo Please ensure 'docker compose up -d mimir-db' has been run.
    pause
)

:: 3. Python Virtual Environment Setup
echo.
echo [3/5] Verifying Python environment...
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

:: 4. Pre-compiled Frontend Check
echo.
echo [4/5] Checking Svelte 5 dashboard build...
if not exist "dist\index.html" (
    where npm >nul 2>nul
    if errorlevel 1 (
        echo WARNING: Node.js/npm is not installed.
        echo Please install Node.js v22+ to compile the Svelte UI.
    ) else (
        echo Building frontend static assets in root...
        if not exist "node_modules" call npm install
        call npm run build
    )
)

:: 5. Launch Backend & Open Browser
echo.
echo [5/5] Launching Mimir Engine Middleware Proxy...
start http://127.0.0.1:59056
python -m uvicorn app:app --host 0.0.0.0 --port 59056 --reload
pause
