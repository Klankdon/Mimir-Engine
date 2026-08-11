@echo off
setlocal enabledelayedexpansion
title Mimir Engine Launcher

echo ===================================================
echo               MIMIR ENGINE LAUNCHER               
echo ===================================================
echo.

:: 1. Auto-update repository
echo [1/4] Checking for Mimir Engine updates...
git pull origin main

:: 2. Python Virtual Environment Setup
echo [2/4] Verifying Python environment...
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
echo Installing/updating Python dependencies...
pip install -r requirements.txt --quiet

:: 3. Pre-compiled Frontend Check
echo [3/4] Checking Svelte dashboard build...
if not exist "mimir-desktop\dist" (
    echo Building frontend static assets for first-time run...
    cd mimir-desktop
    if not exist "node_modules" (
        call npm install
    )
    call npm run build
    cd ..
)

:: 4. Launch Backend & Open Browser
echo [4/4] Launching Mimir Engine Middleware...
start http://localhost:8000
python app.py

pause
