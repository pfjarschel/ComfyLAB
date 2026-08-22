#!/bin/bash
set -e

export WINEDEBUG=-all
export WINEPREFIX=/root/.wine

cd /workspace/src

echo "========================================================="
echo "  ComfyLAB Windows Release Builder (Wine in Docker)"
echo "========================================================="

# 1. Ensure pre-compiled frontend assets are present
if [ ! -d "frontend/dist" ]; then
    echo "Error: Pre-compiled frontend assets not found at frontend/dist!"
    echo "Please build the frontend before running the release build."
    exit 1
fi
echo "[Build 1/2] Verified pre-compiled frontend assets in frontend/dist."

# 2. Run build_exe.py using Windows Python inside Wine (skipping frontend build)
echo "[Build 2/2] Running PyInstaller Windows build via Wine..."
wine "C:\\Python311\\python.exe" build_exe.py "$@"
wineserver -w

# 3. Fix output file ownership if HOST_UID is provided
if [ -n "$HOST_UID" ] && [ -n "$HOST_GID" ]; then
    echo " -> Adjusting output permissions for host user ($HOST_UID:$HOST_GID)..."
    chown -R "$HOST_UID:$HOST_GID" /workspace/src/dist 2>/dev/null || true
    chown -R "$HOST_UID:$HOST_GID" /workspace 2>/dev/null || true
fi

echo "========================================================="
echo "  Windows Standalone Release Build Completed!"
echo "========================================================="
