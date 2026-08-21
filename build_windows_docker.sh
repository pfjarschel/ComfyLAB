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
    echo "[Docker] Building builder image '$IMAGE_NAME' (this may take a few minutes on first run)..."
    docker build -t "$IMAGE_NAME" -f "$DOCKERFILE" "$SCRIPT_DIR"
    if [[ "$1" == "--rebuild" ]]; then
        shift
    fi
fi

echo "[Docker] Running Windows build inside Wine container..."
docker run --rm \
    -v "$WORKSPACE_ROOT":/workspace \
    -e HOST_UID="$(id -u)" \
    -e HOST_GID="$(id -g)" \
    "$IMAGE_NAME" "$@"

echo -e "\n\033[1;32mDone! The Windows release package is in src/dist/\033[0m"
