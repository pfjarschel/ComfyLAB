#!/usr/bin/env bash
# ComfyLAB - One-click Windows Build via Docker + Wine

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCKERFILE="$SCRIPT_DIR/docker/Dockerfile.windows"
IMAGE_NAME="comfylab-windows-builder"

# Check Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "\033[1;31mError: 'docker' command not found. Please install Docker or start the Docker daemon.\033[0m"
    exit 1
fi

echo -e "\033[1;35m=========================================================\033[0m"
echo -e "\033[1;35m  ComfyLAB Windows Executable Builder (Docker + Wine)   \033[0m"
echo -e "\033[1;35m=========================================================\033[0m"

# Build Docker image if not present or if requested
if [[ "$1" == "--rebuild" ]] || ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo "[Docker] Building builder image '$IMAGE_NAME'..."
    docker build -t "$IMAGE_NAME" -f "$DOCKERFILE" "$SCRIPT_DIR"
    if [[ "$1" == "--rebuild" ]]; then
        shift
    fi
fi

# Create a fresh local staging directory in /tmp
STAGE_DIR=$(mktemp -d /tmp/comfylab_win_XXXXXX)
echo "[Stage] Staging project files to '$STAGE_DIR'..."

# Copy source tree excluding heavy caches and previous build outputs (preserving frontend/dist)
tar --exclude='node_modules' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='.venv' \
    --exclude='src/dist' \
    --exclude='./src/dist' \
    -cf - -C "$WORKSPACE_ROOT" . | tar -xf - -C "$STAGE_DIR"

# Explicitly ensure frontend/dist is present in staging
if [ -d "$SCRIPT_DIR/frontend/dist" ]; then
    mkdir -p "$STAGE_DIR/src/frontend/dist"
    cp -r "$SCRIPT_DIR/frontend/dist/"* "$STAGE_DIR/src/frontend/dist/"
fi

mkdir -p "$STAGE_DIR/src/dist"
mkdir -p "$SCRIPT_DIR/dist"

echo "[Docker] Running Windows PyInstaller compilation in Wine 11 container..."
docker run --rm \
    -v "$STAGE_DIR":/workspace \
    -e HOST_UID="$(id -u)" \
    -e HOST_GID="$(id -g)" \
    "$IMAGE_NAME" "$@"

# Copy the built Windows executable zip package back to the host src/dist
echo "[Stage] Copying output release packages back to '$SCRIPT_DIR/dist'..."
cp -u "$STAGE_DIR/src/dist/"*.zip "$SCRIPT_DIR/dist/" 2>/dev/null || cp "$STAGE_DIR/src/dist/"*.zip "$SCRIPT_DIR/dist/" 2>/dev/null || true

# Clean up staging
rm -rf "$STAGE_DIR" 2>/dev/null || docker run --rm -v /tmp:/tmp ubuntu:22.04 rm -rf "$STAGE_DIR"

echo -e "\n\033[1;32m=========================================================\033[0m"
echo -e "\033[1;32m  Done! The Windows release package is in src/dist/     \033[0m"
echo -e "\033[1;32m=========================================================\033[0m"
