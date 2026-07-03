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
import shutil
import subprocess
from pathlib import Path

def check_prerequisites():
    if shutil.which("npm") is None:
        print("\033[1;31mError: 'npm' (Node.js) is not installed.\033[0m")
        print("Node.js and npm are required to compile the React frontend bundle.")
        sys.exit(1)

def build_frontend(script_dir):
    frontend_dir = script_dir / "frontend"
    print("\n[Build 1/3] Compiling React frontend...")
    
    print(" -> Running npm install...")
    # Run npm install via list parameters to prevent FileNotFoundError on Linux/macOS
    npm_cmd = ["npm", "install"]
    subprocess.run(npm_cmd, cwd=str(frontend_dir), shell=(os.name == 'nt'), check=True)
    
    print(" -> Running npm run build...")
    # Invoke vite build via node explicitly to ensure cross-platform compatibility
    node_build_cmd = ["node", "node_modules/vite/bin/vite.js", "build"]
    subprocess.run(node_build_cmd, cwd=str(frontend_dir), env=os.environ, check=True)
    
    dist_dir = frontend_dir / "dist"
    if not dist_dir.exists():
        print("\033[1;31mError: Compiled directory 'frontend/dist' was not found. Build failed.\033[0m")
        sys.exit(1)
    print("\033[1;32m[Success] Frontend compiled successfully!\033[0m")

def copy_ignore(path, names):
    # Exclude caches, virtual environments, unit tests, and frontend source assets
    ignored = []
    for name in names:
        if name in ("__pycache__", ".pytest_cache", ".venv", "tests", "node_modules", "src", "public"):
            ignored.append(name)
        elif name.endswith(".pyc") or name.endswith(".pyo") or name.endswith(".pyd"):
            ignored.append(name)
    return ignored

def assemble_release(script_dir):
    print("\n[Build 2/3] Assembling release file structure...")
    release_dir = script_dir / "comfylab"
    
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy Backend python files (excluding pycache)
    print(" -> Copying backend modules...")
    shutil.copytree(script_dir / "backend", release_dir / "backend", ignore=copy_ignore)
    
    # 2. Copy ComfyLAB core engine and registry classes (excluding pycache)
    print(" -> Copying core engine...")
    shutil.copytree(script_dir / "comfylab", release_dir / "comfylab", ignore=copy_ignore)
    
    # 3. Copy compiled frontend bundle
    print(" -> Copying compiled web assets...")
    (release_dir / "frontend").mkdir(exist_ok=True)
    shutil.copytree(script_dir / "frontend" / "dist", release_dir / "frontend" / "dist")
    
    # 4. Copy configurations, license, and entrypoint launchers
    print(" -> Copying wrappers and documentation...")
    shutil.copy2(script_dir / "requirements.txt", release_dir / "requirements.txt")
    shutil.copy2(script_dir / "start.sh", release_dir / "start.sh")
    shutil.copy2(script_dir / "start.bat", release_dir / "start.bat")
    shutil.copy2(script_dir / "start.py", release_dir / "start.py")
    shutil.copy2(script_dir / "LICENSE", release_dir / "LICENSE")
    shutil.copy2(script_dir / "README.md", release_dir / "README.md")
    
    # 5. Enforce executable permissions on start.sh inside the package
    if os.name != 'nt':
        try:
            os.chmod(release_dir / "start.sh", 0o755)
            print(" -> Setting executable permissions on start.sh...")
        except Exception as e:
            print(f" -> Warning: Failed to set executable permissions on start.sh: {e}")

    return release_dir

def compress_release(script_dir, release_dir):
    print("\n[Build 3/3] Compressing release package...")
    zip_file = script_dir / "comfylab-release.zip"
    if zip_file.exists():
        zip_file.unlink()
        
    shutil.make_archive(
        base_name=str(script_dir / "comfylab-release"),
        format='zip',
        root_dir=str(script_dir),
        base_dir=release_dir.name
    )
    
    print(" -> Cleaning up temporary staging folder...")
    shutil.rmtree(release_dir)
    
    print(f"\n\033[1;32m=========================================================\033[0m")
    print(f"\033[1;32m  Build Success! Created: {zip_file.name}\033[0m")
    print(f"\033[1;32m=========================================================\033[0m\n")

def main():
    script_dir = Path(__file__).parent.resolve()
    
    check_prerequisites()
    build_frontend(script_dir)
    release_dir = assemble_release(script_dir)
    compress_release(script_dir, release_dir)

if __name__ == "__main__":
    main()
