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
import threading
import time
import argparse
import webbrowser
import multiprocessing
from pathlib import Path

import uvicorn

# Ensure multiprocessing support works under frozen PyInstaller binary
multiprocessing.freeze_support()

def parse_args():
    parser = argparse.ArgumentParser(description="ComfyLAB Standalone Application")
    parser.add_argument("--host", default="0.0.0.0", help="Binding address for the backend (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port for the FastAPI backend (default: 8000)")
    parser.add_argument("--local", action="store_true", help="Restrict access to localhost only (bind to 127.0.0.1)")
    return parser.parse_args()

def main():
    args = parse_args()
    host = "127.0.0.1" if args.local else args.host
    port = args.port

    # If running as PyInstaller executable, sys._MEIPASS holds the temp directory
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
        exe_dir = Path(sys.executable).parent.resolve()
        if str(exe_dir) not in sys.path:
            sys.path.insert(0, str(exe_dir))
    else:
        base_dir = Path(__file__).parent.resolve()

    # Add the base directory to sys.path so backend/comfylab can be imported correctly
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))

    # Set PYTHONPATH environment variable to ensure child processes can resolve imports
    os.environ["PYTHONPATH"] = str(base_dir)
    os.environ["COMFYLAB_FRONTEND_PORT"] = str(port)
    os.environ["COMFYLAB_BACKEND_PORT"] = str(port)

    # Auto-open the web browser pointing to the server
    browser_url = f"http://127.0.0.1:{port}" if host in ("0.0.0.0", "::") else f"http://{host}:{port}"
    
    version_file = base_dir / "VERSION"
    version_str = f" v{version_file.read_text().strip()}" if version_file.exists() else ""
    title_str = f"ComfyLAB{version_str} Standalone"
    
    print("\033[1;35m")
    print("  ============================================")
    print("  " + title_str.center(42))
    print("  ============================================")
    print("\033[0m")

    print(f"\n[ComfyLAB Standalone] Launching application on {browser_url} ...")
    
    # The app must be imported only after sys.path/_MEIPASS resolution above
    from backend.main import app

    # Spin up browser opening in a deferred thread/timer
    def open_browser():
        time.sleep(1.5)
        print(f"[ComfyLAB Standalone] Opening browser to {browser_url} ...")
        webbrowser.open(browser_url)

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Run the Uvicorn ASGI server
    # proxy_headers=False: the localhost-trust check relies on the real client
    # IP, so X-Forwarded-For spoofing must not be honored.
    try:
        uvicorn.run(app, host=host, port=port, log_level="warning", proxy_headers=False)
    except KeyboardInterrupt:
        print("\n[ComfyLAB Standalone] Stopping server...")
    print("[ComfyLAB Standalone] Exited cleanly.")

if __name__ == "__main__":
    main()
