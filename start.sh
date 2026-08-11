#!/usr/bin/env bash

echo "==================================================="
echo "              MIMIR ENGINE LAUNCHER               "
echo "==================================================="
echo ""

# 1. Auto-update repository
echo "[1/4] Checking for Mimir Engine updates..."
git pull origin main

# 2. Python Virtual Environment Setup
echo "[2/4] Verifying Python environment..."
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "Installing/updating Python dependencies..."
pip install -r requirements.txt --quiet

# 3. Pre-compiled Frontend Check
echo "[3/4] Checking Svelte dashboard build..."
if [ ! -d "mimir-desktop/dist" ]; then
    echo "Building frontend static assets for first-time run..."
    cd mimir-desktop
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run build
    cd ..
fi

# 4. Launch Backend & Open Browser
echo "[4/4] Launching Mimir Engine Middleware..."
(sleep 2 && (open http://localhost:8000 2>/dev/null || xdg-open http://localhost:8000 2>/dev/null)) &
python3 app.py
