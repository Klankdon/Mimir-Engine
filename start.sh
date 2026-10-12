#!/usr/bin/env bash
set -e

echo "==================================================="
echo "              MIMIR ENGINE LAUNCHER               "
echo "==================================================="
echo ""

# 1. Verify Docker daemon
if ! docker info >/dev/null 2>&1; then
    echo "[!] Error: Docker daemon is not running."
    exit 1
fi

# 2. Pull updates
echo "[*] Checking for repository updates..."
git pull origin main || true

# 3. Launch stack
echo "[*] Starting Mimir Engine stack..."
docker compose up -d --build

echo ""
echo "==================================================="
echo " Mimir Engine is running at http://localhost:59056"
echo "==================================================="
echo ""
