#!/usr/bin/env bash

# ComfyLAB Unix Bootstrapper
# This script manages the Python virtual environment (.venv) and launches the application.

# Resolve the directory of this script to run correctly from any location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

info() { echo -e "\033[1;34m[ComfyLAB Boot]\033[0m $1"; }
success() { echo -e "\033[1;32m[ComfyLAB Boot]\033[0m $1"; }
warn() { echo -e "\033[1;33m[ComfyLAB Boot]\033[0m $1"; }
error() { echo -e "\033[1;31m[ComfyLAB Boot]\033[0m $1"; }

echo -e "\033[1;35m"
echo "  ============================================"
echo "           ComfyLAB System Bootstrapper       "
echo "  ============================================"
echo -e "\033[0m"

# 1. Enforce/bootstrap Python virtual environment
VENV_DIR="$HOME/.comfylab/venv"
PYTHON_EXE=""

# Ensure parent directory exists
mkdir -p "$HOME/.comfylab"

if [ -d "$VENV_DIR" ]; then
    info "Found active virtual environment at $VENV_DIR"
    if [ -f "$VENV_DIR/bin/python" ]; then
        PYTHON_EXE="$VENV_DIR/bin/python"
    elif [ -f "$VENV_DIR/bin/python3" ]; then
        PYTHON_EXE="$VENV_DIR/bin/python3"
    fi
fi

if [ -z "$PYTHON_EXE" ]; then
    info "Virtual environment not found or incomplete. Initializing venv at $VENV_DIR..."
    
    # Locate system Python
    SYSTEM_PYTHON=""
    if command -v python3 &>/dev/null; then
        SYSTEM_PYTHON="python3"
    elif command -v python &>/dev/null; then
        SYSTEM_PYTHON="python"
    else
        error "Python is not installed on this system. Please install Python 3.8+ to run ComfyLAB."
        read -p "Press Enter to exit..."
        exit 1
    fi

    # Create virtual environment
    info "Creating virtual environment using $SYSTEM_PYTHON..."
    $SYSTEM_PYTHON -m venv "$VENV_DIR"
    
    if [ $? -ne 0 ]; then
        warn "Failed to create virtual environment (filesystem may not support symlinks/copies)."
        warn "Falling back to system Python: $SYSTEM_PYTHON..."
        PYTHON_EXE="$SYSTEM_PYTHON"
    else
        PYTHON_EXE="$VENV_DIR/bin/python"
        
        # Install python dependencies in venv
        if [ -f "requirements.txt" ]; then
            info "Installing dependencies from requirements.txt..."
            $PYTHON_EXE -m pip install --upgrade pip
            $PYTHON_EXE -m pip install -r requirements.txt
            if [ $? -eq 0 ]; then
                success "Dependencies installed successfully!"
            else
                error "Failed to install Python dependencies in venv."
                read -p "Press Enter to exit..."
                exit 1
            fi
        fi
    fi
fi

# 2. Launch start.py using resolved Python executable
info "Launching process coordinator..."
$PYTHON_EXE start.py "$@"
exit $?
