# 4. Pre-compiled Frontend Check
echo ""
echo "[4/5] Checking Svelte 5 dashboard build..."
if [ ! -f "dist/index.html" ]; then
    if ! command -v npm &> /dev/null; then
        echo "WARNING: 'npm' is not installed. Skipping UI build."
    else
        echo "Building frontend static assets..."
        cd mimir-desktop
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        npm run build
        cd ..
        echo "Copying built dashboard to root..."
        cp -r mimir-desktop/dist ./dist
    fi
fi
