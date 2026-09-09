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
