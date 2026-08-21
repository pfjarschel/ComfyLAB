#!/bin/bash
set -e

export WINEDEBUG=-all
export WINEPREFIX=/root/.wine

cd /workspace/src

echo "========================================================="
echo "  ComfyLAB Windows Release Builder (Wine in Docker)"
echo "========================================================="

# 1. Compile frontend if dist doesn't exist
if [ ! -d "frontend/dist" ]; then
    echo "[Build 1/3] Frontend dist not found. Compiling React frontend with Node.js..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run build
    cd ..
else
    echo "[Build 1/3] Using pre-compiled frontend assets in frontend/dist."
fi

# 2. Ensure any new/updated python dependencies in requirements.txt are installed in Wine
echo "[Build 2/3] Verifying Windows Python dependencies..."
xvfb-run -a wine "C:\\Python311\\python.exe" -m pip install -r requirements.txt

# 3. Run build_exe.py using Windows Python inside Wine
echo "[Build 3/3] Running PyInstaller Windows build..."
xvfb-run -a wine "C:\\Python311\\python.exe" build_exe.py "$@"

# 4. Fix output file ownership if HOST_UID is provided
if [ -n "$HOST_UID" ] && [ -n "$HOST_GID" ]; then
    echo " -> Adjusting output permissions for host user ($HOST_UID:$HOST_GID)..."
    chown -R "$HOST_UID:$HOST_GID" /workspace/src/dist 2>/dev/null || true
fi

echo "========================================================="
echo "  Windows Standalone Release Build Completed!"
echo "========================================================="
