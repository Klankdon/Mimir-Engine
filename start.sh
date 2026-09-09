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

# 4. Pre-compiled Frontend Check
echo ""
echo "[4/5] Checking Svelte 5 dashboard build..."
if [ ! -f "dist/index.html" ]; then
    if ! command -v npm &> /dev/null; then
        echo "WARNING: 'npm' is not installed. Skipping frontend build."
        echo "To build the UI, install Node.js: sudo apt install nodejs npm"
    else
        echo "Building frontend static assets in root directory..."
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        npm run build
    fi
fi

# 5. Launch Backend & Open Browser
echo ""
echo "[5/5] Launching Mimir Engine Middleware..."
(sleep 2 && (open http://127.0.0.1:59056 2>/dev/null || xdg-open http://127.0.0.1:59056 2>/dev/null)) &
./venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 59056 --reload
