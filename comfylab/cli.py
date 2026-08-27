#!/usr/bin/env python3
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
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="ComfyLAB Unified Process Coordinator")
    parser.add_argument("--host", default="0.0.0.0", help="Binding address for the backend (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port for the FastAPI backend (default: 8000)")
    parser.add_argument("--vite-port", type=int, default=5173, help="Port for the Vite frontend dev server (default: 5173)")
    parser.add_argument("--local", action="store_true", help="Restrict access to localhost only (bind to 127.0.0.1)")
    parser.add_argument("--dev", action="store_true", help="Force development mode (runs Vite and FastAPI concurrently)")
    parser.add_argument("--lite", action="store_true", help="Launch in Lite Mode (reduces visual effects for low-power hardware)")
    return parser.parse_args()

def is_npm_installed():
    return shutil.which("npm") is not None

def check_python_dependencies(script_dir: Path):
    requirements_file = script_dir / "requirements.txt"
    if not requirements_file.exists():
        return
    
    import importlib.metadata
    missing_packages = []
    
    with open(requirements_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re.match(r'^([a-zA-Z0-9_\-]+)', line)
            if match:
                pkg_name = match.group(1)
                try:
                    importlib.metadata.version(pkg_name)
                except importlib.metadata.PackageNotFoundError:
                    try:
                        importlib.metadata.version(pkg_name.replace('-', '_'))
                    except importlib.metadata.PackageNotFoundError:
                        missing_packages.append(line)
                        
    if missing_packages:
        print(f"[ComfyLAB] Missing Python packages detected: {', '.join(missing_packages)}")
        print("[ComfyLAB] Running pip install to restore dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], check=True)
            print("[ComfyLAB] Python dependencies successfully installed!")
        except Exception as e:
            print(f"\033[1;31m[ComfyLAB Error] Failed to install Python dependencies: {e}\033[0m")
            print("Please run 'pip install -r requirements.txt' manually.")
            input("\nPress Enter to exit...")
            sys.exit(1)

def get_installed_version() -> str:
    try:
        from importlib.metadata import version
        return version("comfylab")
    except Exception:
        pass
    try:
        import comfylab
        if hasattr(comfylab, "__version__") and comfylab.__version__:
            return comfylab.__version__
    except Exception:
        pass
    for path in [Path(__file__).resolve().parent.parent / "VERSION", Path(__file__).resolve().parent / "VERSION"]:
        if path.exists():
            return path.read_text().strip()
    return "0.0.0"

def main():
    args = parse_args()
    host = "127.0.0.1" if args.local else args.host
    port = args.port
    vite_port = args.vite_port

    # Determine execution root (source repository root or current directory)
    cli_dir = Path(__file__).resolve().parent
    repo_root = cli_dir.parent
    if (repo_root / "backend").exists() and (repo_root / "comfylab").exists():
        source_dir = repo_root
    else:
        source_dir = Path.cwd()

    check_python_dependencies(source_dir)

    # Resolve frontend dist path using backend.main helper if available
    try:
        from backend.main import get_frontend_dist_path
        frontend_dist = get_frontend_dist_path()
    except Exception:
        frontend_dist = source_dir / "frontend" / "dist"

    frontend_dir = source_dir / "frontend"
    frontend_node_modules = frontend_dir / "node_modules"

    version_str = get_installed_version()
    title_str = f"ComfyLAB v{version_str} Process Coordinator"

    print("\033[1;35m")
    print("  ============================================")
    print("  " + title_str.center(42))
    print("  ============================================")
    print("\033[0m")

    # 1. Determine execution mode based on pre-compiled frontend assets
    if frontend_dist.exists() and not args.dev:
        mode = "production"
        try:
            rel_path = frontend_dist.relative_to(source_dir)
        except ValueError:
            rel_path = frontend_dist
        print(f"[ComfyLAB] Mode: Production (Pre-compiled frontend found at '{rel_path}')")
    else:
        mode = "development"
        dev_reason = "forced via --dev" if args.dev else "pre-compiled frontend NOT found"
        print(f"[ComfyLAB] Mode: Development ({dev_reason})")

    # 2. Setup Environment Variables
    env = os.environ.copy()
    if (source_dir / "backend").exists():
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{source_dir}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = str(source_dir)

    backend_proc = None
    frontend_proc = None

    try:
        if mode == "production":
            env["COMFYLAB_FRONTEND_PORT"] = str(port)
            env["COMFYLAB_BACKEND_PORT"] = str(port)
            query_str = "?lite=1" if args.lite else ""
            browser_url = f"http://127.0.0.1:{port}{query_str}" if host in ("0.0.0.0", "::") else f"http://{host}:{port}{query_str}"
            
            print(f"[ComfyLAB] Starting FastAPI Backend on {host}:{port}...")
            # --no-proxy-headers: ComfyLAB's localhost-trust check relies on the real
            # client IP, so X-Forwarded-For spoofing must not be honored.
            backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", host, "--port", str(port), "--log-level", "warning", "--no-proxy-headers"]
            cwd_target = str(source_dir) if (source_dir / "backend").exists() else None
            backend_proc = subprocess.Popen(backend_cmd, cwd=cwd_target, env=env)
            
            # Wait for backend to initialize before opening browser
            time.sleep(1.5)
            print(f"[ComfyLAB] Opening browser to {browser_url} ...")
            webbrowser.open(browser_url)

        else:
            env["COMFYLAB_FRONTEND_PORT"] = str(vite_port)
            env["COMFYLAB_BACKEND_PORT"] = str(port)
            env["COMFYLAB_DEV_MODE"] = "1"
            
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
                try:
                    rel_frontend = frontend_dir.relative_to(source_dir)
                except ValueError:
                    rel_frontend = frontend_dir
                print(f"[ComfyLAB] node_modules not found in '{rel_frontend}'. Running 'npm install'...")
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

            query_str = "?lite=1" if args.lite else ""
            browser_url = f"http://127.0.0.1:{vite_port}{query_str}" if host in ("0.0.0.0", "::") else f"http://{host}:{vite_port}{query_str}"

            # Start backend (FastAPI) on the configured port
            print(f"[ComfyLAB] Starting FastAPI Backend on {host}:{port}...")
            backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", host, "--port", str(port), "--reload", "--log-level", "warning", "--no-proxy-headers"]
            backend_proc = subprocess.Popen(backend_cmd, cwd=str(source_dir), env=env)

            # Start frontend (Vite) on the configured vite_port
            print(f"[ComfyLAB] Starting Vite Frontend dev server on port {vite_port}...")
            vite_args = ["--port", str(vite_port)]
            if host in ("0.0.0.0", "::"):
                vite_args.append("--host")
                vite_args.append("0.0.0.0")

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
            port_file = source_dir / "frontend" / "public" / "backend_port.json"
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
