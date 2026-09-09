#!/usr/bin/env bash

echo "==================================================="
echo "              MIMIR ENGINE LAUNCHER               "
echo "==================================================="
echo ""

# 1. Auto-update repository
echo "[1/5] Checking for Mimir Engine updates..."
git pull origin main 2>/dev/null || true

# 2. Database Sanity Check
echo ""
echo "[2/5] Verifying PostgreSQL (pgvector) is running..."
if ! docker ps | grep -q "mimir"; then
    echo "WARNING: Mimir Database container not found running in Docker."
    echo "Please ensure 'docker compose up -d mimir-db' has been run."
    read -p "Press enter to continue anyway or Ctrl+C to abort..."
fi

# 3. Python Virtual Environment Setup
echo ""
echo "[3/5] Verifying Python environment..."
if [ ! -f "venv/bin/pip" ]; then
    echo "Creating clean Python virtual environment..."
    rm -rf venv
    python3 -m venv venv || { echo "ERROR: python3-venv is missing. Run: sudo apt install python3-venv python3-full"; exit 1; }
fi

echo "Installing/updating Python dependencies..."
./venv/bin/pip install -r requirements.txt --quiet

:: 4. Pre-compiled Frontend Check
echo.
echo [4/5] Checking Svelte 5 dashboard build...
if not exist "dist\index.html" (
    where npm >nul 2>nul
    if errorlevel 1 (
        echo WARNING: Node.js/npm is not installed. Skipping UI build.
    ) else (
        echo Building frontend static assets...
        cd mimir-desktop
        if not exist "node_modules" call npm install
        call npm run build
        cd ..
        echo Copying built dashboard to root...
        xcopy /s /e /y "mimir-desktop\dist" "dist\" >nul
    )
)
