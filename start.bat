@echo off
title ComfyLAB Launcher

:: ComfyLAB Windows Bootstrapper
:: This script manages the Python virtual environment (.venv) and launches the application.

:: Resolve current directory
cd /d "%~dp0"

echo ============================================
echo          ComfyLAB System Bootstrapper       
echo ============================================

set VENV_DIR=%USERPROFILE%\.comfylab\venv
set PYTHON_EXE=

:: Ensure parent directory exists
if not exist "%USERPROFILE%\.comfylab" mkdir "%USERPROFILE%\.comfylab"

:: 1. Enforce/bootstrap Python virtual environment
if exist "%VENV_DIR%\Scripts\python.exe" (
    set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe
    echo [ComfyLAB Boot] Found active virtual environment at %VENV_DIR%
)

if "%PYTHON_EXE%"=="" (
    echo [ComfyLAB Boot] Virtual environment not found or incomplete. Initializing venv at %VENV_DIR%...
    
    :: Locate system Python
    set SYSTEM_PYTHON=
    where python >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set SYSTEM_PYTHON=python
    ) else (
        where py >nul 2>nul
        if %ERRORLEVEL% equ 0 (
            set SYSTEM_PYTHON=py
        )
    )

    if "%SYSTEM_PYTHON%"=="" (
        echo [ComfyLAB Boot] Error: Python is not installed on this system. Please install Python 3.8+ to run ComfyLAB.
        pause
        exit /b 1
    )

    :: Create virtual environment
    echo [ComfyLAB Boot] Creating virtual environment using %SYSTEM_PYTHON%...
    %SYSTEM_PYTHON% -m venv %VENV_DIR%
    if %ERRORLEVEL% neq 0 (
        echo [ComfyLAB Boot] Warning: Failed to create virtual environment.
        echo [ComfyLAB Boot] Falling back to system Python: %SYSTEM_PYTHON%...
        set PYTHON_EXE=%SYSTEM_PYTHON%
    ) else (
        set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe
        
        :: Install python dependencies
        if exist "requirements.txt" (
            echo [ComfyLAB Boot] Installing dependencies from requirements.txt...
            %PYTHON_EXE% -m pip install --upgrade pip
            %PYTHON_EXE% -m pip install -r requirements.txt
            if %ERRORLEVEL% equ 0 (
                echo [ComfyLAB Boot] Dependencies installed successfully!
            ) else (
                echo [ComfyLAB Boot] Error: Failed to install Python dependencies in venv.
                pause
                exit /b 1
            )
        )
    )
)

:: 2. Launch start.py using resolved Python executable
echo [ComfyLAB Boot] Launching process coordinator...
%PYTHON_EXE% start.py %*
if %ERRORLEVEL% neq 0 (
    exit /b %ERRORLEVEL%
)
