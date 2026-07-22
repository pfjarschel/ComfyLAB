#!/usr/bin/env python
# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
import webbrowser
import re
import importlib.metadata
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="ComfyLAB Unified Process Coordinator")
    parser.add_argument("--host", default="0.0.0.0", help="Binding address for the backend (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port for the FastAPI backend (default: 8000)")
    parser.add_argument("--vite-port", type=int, default=5173, help="Port for the Vite frontend dev server (default: 5173)")
    parser.add_argument("--local", action="store_true", help="Restrict access to localhost only (bind to 127.0.0.1)")
    parser.add_argument("--dev", action="store_true", help="Force development mode (runs Vite and FastAPI concurrently)")
    return parser.parse_args()

def is_npm_installed():
    return shutil.which("npm") is not None

def check_python_dependencies(script_dir):
    requirements_file = script_dir / "requirements.txt"
    if not requirements_file.exists():
        return
    
    missing_packages = []
    
    with open(requirements_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Extract package name (e.g., 'pydantic' from 'pydantic>=2.0.0')
            match = re.match(r'^([a-zA-Z0-9_\-]+)', line)
            if match:
                pkg_name = match.group(1)
                try:
                    importlib.metadata.version(pkg_name)
                except importlib.metadata.PackageNotFoundError:
                    try:
                        # Try with underscores instead of hyphens
                        importlib.metadata.version(pkg_name.replace('-', '_'))
                    except importlib.metadata.PackageNotFoundError:
                        missing_packages.append(line)
                        
    if missing_packages:
        print(f"[ComfyLAB] Missing Python packages detected: {', '.join(missing_packages)}")
        print("[ComfyLAB] Running pip install to restore dependencies...")
        try:
            # sys.executable points to the current running python (which is the venv's python)
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], check=True)
            print("[ComfyLAB] Python dependencies successfully installed!")
        except Exception as e:
            print(f"\033[1;31m[ComfyLAB Error] Failed to install Python dependencies: {e}\033[0m")
            print("Please run 'pip install -r requirements.txt' manually.")
            input("\nPress Enter to exit...")
            sys.exit(1)

def main():
    args = parse_args()
    host = "127.0.0.1" if args.local else args.host
    port = args.port
    vite_port = args.vite_port

    script_dir = Path(__file__).parent.resolve()
    check_python_dependencies(script_dir)

    frontend_dir = script_dir / "frontend"
    frontend_dist = frontend_dir / "dist"
    frontend_node_modules = frontend_dir / "node_modules"

    version_file = script_dir / "VERSION"
    version_str = f" v{version_file.read_text().strip()}" if version_file.exists() else ""
    title_str = f"ComfyLAB{version_str} Process Coordinator"

    print("\033[1;35m")
    print("  ============================================")
    print("  " + title_str.center(42))
    print("  ============================================")
    print("\033[0m")

    # 1. Determine execution mode based on pre-compiled frontend assets
    if frontend_dist.exists() and not args.dev:
        mode = "production"
        print(f"[ComfyLAB] Mode: Production (Pre-compiled frontend found at '{frontend_dist.relative_to(script_dir)}')")
    else:
        mode = "development"
        dev_reason = "forced via --dev" if args.dev else "pre-compiled frontend NOT found"
        print(f"[ComfyLAB] Mode: Development ({dev_reason})")

    # 2. Setup Environment Variables
    env = os.environ.copy()
    env["PYTHONPATH"] = str(script_dir)

    backend_proc = None
    frontend_proc = None

    try:
        if mode == "production":
            # In production, FastAPI serves the compiled files directly on the configured port
            browser_url = f"http://127.0.0.1:{port}" if host in ("0.0.0.0", "::") else f"http://{host}:{port}"
            
            print(f"[ComfyLAB] Starting FastAPI Backend on {host}:{port}...")
            # --no-proxy-headers: ComfyLAB's localhost-trust check relies on the real
            # client IP, so X-Forwarded-For spoofing must not be honored.
            backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", host, "--port", str(port), "--log-level", "info", "--no-proxy-headers"]
            backend_proc = subprocess.Popen(backend_cmd, cwd=str(script_dir), env=env)
            
            # Wait for backend to initialize before opening browser
            time.sleep(1.5)
            print(f"[ComfyLAB] Opening browser to {browser_url} ...")
            webbrowser.open(browser_url)

        else:
            # In development, Vite runs on port 5173 and proxy requests to FastAPI on port 8000
            # Validate that Node.js / NPM is installed
            if not is_npm_installed():
                print("\033[1;31m[ComfyLAB Error] Pre-compiled frontend assets were not found, requiring a development-mode run.\033[0m")
                print("\033[1;31m                 However, 'npm' / Node.js was not found in your system PATH.\033[0m")
                print("\nTo run in development mode, please install Node.js (https://nodejs.org).")
                print("Otherwise, download the run-ready release package containing pre-compiled frontend assets.")
                print("\nIf you are on Windows, ensure Node.js is added to your environment variables.")
                input("\nPress Enter to exit...")
                sys.exit(1)

            # Ensure frontend dependencies are installed
            if not frontend_node_modules.exists():
                print(f"[ComfyLAB] node_modules not found in '{frontend_dir.relative_to(script_dir)}'. Running 'npm install'...")
                # Use shell=True on Windows to resolve npm.cmd correctly
                npm_cmd = "npm install"
                install_proc = subprocess.run(npm_cmd, cwd=str(frontend_dir), shell=(os.name == 'nt'))
                if install_proc.returncode != 0:
                    print("\033[1;31m[ComfyLAB Error] Failed to install frontend dependencies.\033[0m")
                    input("\nPress Enter to exit...")
                    sys.exit(1)
                print("[ComfyLAB] Frontend dependencies installed successfully!")

            # In development, write the backend port configuration for the frontend to read
            public_dir = frontend_dir / "public"
            public_dir.mkdir(parents=True, exist_ok=True)
            port_file = public_dir / "backend_port.json"
            try:
                with open(port_file, "w") as pf:
                    json.dump({"port": port}, pf)
                print(f"[ComfyLAB] Registered custom backend port {port} in frontend configuration.")
            except Exception as e:
                print(f"[ComfyLAB Warning] Failed to write backend_port.json: {e}")

            browser_url = f"http://127.0.0.1:{vite_port}" if host in ("0.0.0.0", "::") else f"http://{host}:{vite_port}"

            # Start backend (FastAPI) on the configured port
            print(f"[ComfyLAB] Starting FastAPI Backend on {host}:{port}...")
            backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", host, "--port", str(port), "--reload", "--log-level", "info", "--no-proxy-headers"]
            backend_proc = subprocess.Popen(backend_cmd, cwd=str(script_dir), env=env)

            # Start frontend (Vite) on the configured vite_port
            print(f"[ComfyLAB] Starting Vite Frontend dev server on port {vite_port}...")
            vite_args = ["--port", str(vite_port)]
            if host in ("0.0.0.0", "::"):
                vite_args.append("--host")
                vite_args.append("0.0.0.0")

            # Run Vite via node explicitly to avoid mount/permissions execution issues
            vite_cmd = ["node", "node_modules/vite/bin/vite.js"] + vite_args
            frontend_proc = subprocess.Popen(vite_cmd, cwd=str(frontend_dir), env=env)

            # Wait for Vite dev server to bind to the port
            time.sleep(1.5)
            print(f"[ComfyLAB] Opening browser to {browser_url} ...")
            webbrowser.open(browser_url)

        # 3. Monitor running processes
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("[ComfyLAB] Backend process stopped unexpectedly.")
                break
            if frontend_proc and frontend_proc.poll() is not None:
                print("[ComfyLAB] Frontend dev server stopped unexpectedly.")
                break

    except KeyboardInterrupt:
        print("\n[ComfyLAB] Shutting down processes...")
    finally:
        # Clean up the temporary backend port json file
        try:
            port_file = script_dir / "frontend" / "public" / "backend_port.json"
            if port_file.exists():
                port_file.unlink()
        except Exception:
            pass

        # Graceful cleanup of child processes
        for p, name in [(frontend_proc, "Frontend"), (backend_proc, "Backend")]:
            if p:
                print(f"[ComfyLAB] Stopping {name} process...")
                try:
                    p.terminate()
                except Exception as e:
                    print(f"[ComfyLAB] Error terminating {name}: {e}")

        # Wait and kill if they don't terminate within timeout
        for p, name in [(frontend_proc, "Frontend"), (backend_proc, "Backend")]:
            if p:
                try:
                    p.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    print(f"[ComfyLAB] {name} did not terminate. Killing process...")
                    try:
                        p.kill()
                    except Exception as e:
                        print(f"[ComfyLAB] Error killing {name}: {e}")

    print("[ComfyLAB] Shutdown complete.")

if __name__ == "__main__":
    main()
