#!/usr/bin/env bash

echo "==================================================="
echo "              MIMIR ENGINE LAUNCHER               "
echo "==================================================="
echo ""

# 1. Auto-update repository
echo "[1/4] Checking for Mimir Engine updates..."
git pull origin main 2>/dev/null || true

# 2. Python Virtual Environment Setup
echo "[2/4] Verifying Python environment..."
if [ ! -f "venv/bin/pip" ]; then
    echo "Creating clean Python virtual environment..."
    rm -rf venv
    python3 -m venv venv || { echo "ERROR: python3-venv is missing. Run: sudo apt install python3-venv python3-full"; exit 1; }
fi

echo "Installing/updating Python dependencies..."
./venv/bin/pip install -r requirements.txt --quiet

# 3. Pre-compiled Frontend Check
echo "[3/4] Checking Svelte dashboard build..."
if [ ! -d "dist" ]; then
    if [ ! -d "mimir-desktop/dist" ]; then
        if ! command -v npm &> /dev/null; then
            echo "WARNING: 'npm' is not installed. Skipping frontend build."
            echo "To build the UI, install Node.js: sudo apt install nodejs npm"
        else
            echo "Building frontend static assets for first-time run..."
            cd mimir-desktop
            if [ ! -d "node_modules" ]; then
                npm install
            fi
            npm run build
            cd ..
        fi
    fi

    if [ -d "mimir-desktop/dist" ]; then
        echo "Copying built dashboard to root..."
        cp -r mimir-desktop/dist ./dist
    fi
fi

# 4. Launch Backend & Open Browser
echo "[4/4] Launching Mimir Engine Middleware..."
(sleep 2 && (open http://localhost:8000 2>/dev/null || xdg-open http://localhost:8000 2>/dev/null)) &
./venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
