@echo off
title Mimir Engine Launcher
echo ===================================================
echo               MIMIR ENGINE LAUNCHER               
echo ===================================================
echo.

:: 1. Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

:: 2. Pull updates (Optional)
echo [*] Pulling latest changes from git...
git pull origin main

:: 3. Launch Docker Compose stack
echo [*] Starting Mimir Engine services...
docker compose up -d --build

echo.
echo ===================================================
echo  Mimir Engine is running at http://localhost:59056
echo ===================================================
echo.
pause
