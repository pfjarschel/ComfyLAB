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

import argparse
import os
import sys
import shutil
import subprocess
from pathlib import Path

from build_release import (
    check_prerequisites as check_node,
    build_frontend,
    bump_version,
    check_symlink_support,
    copy_ignore_stage,
)

def check_prerequisites():
    # Check if PyInstaller is installed in the active environment
    try:
        import PyInstaller
    except ImportError:
        print("[Build] 'pyinstaller' is not installed in the active Python environment.")
        print("Installing pyinstaller via pip...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("[Build] 'pyinstaller' successfully installed!")
        except Exception as e:
            print(f"\033[1;31mError: Failed to install pyinstaller: {e}\033[0m")
            sys.exit(1)

def run_pyinstaller(script_dir):
    spec_file = script_dir / "ComfyLAB.spec"
    if not spec_file.exists():
        print(f"\033[1;31mError: PyInstaller spec file '{spec_file.name}' not found!\033[0m")
        sys.exit(1)

    print(f"\n[Build] Starting PyInstaller compilation using spec: {spec_file.name} ...")
    dist_dir = script_dir / "dist" / "standalone"
    cmd = [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean", "--noconfirm",
           "--distpath", str(dist_dir)]

    try:
        subprocess.run(cmd, cwd=str(script_dir), check=True)

        # Verify output binary
        binary_name = "ComfyLAB.exe" if os.name == 'nt' else "ComfyLAB"
        output_binary = dist_dir / binary_name

        # Copy comfylab/blocks next to the compiled binary
        dest_blocks_dir = dist_dir / "comfylab" / "blocks"
        if dest_blocks_dir.exists():
            shutil.rmtree(dest_blocks_dir)
        shutil.copytree(script_dir / "comfylab" / "blocks", dest_blocks_dir, ignore=copy_ignore_stage)
        print(f" -> Copied core block source modules next to binary: {dest_blocks_dir}")

        if output_binary.exists():
            print(f"\n\033[1;32m[Build Finished] Standalone binary compiled: dist/standalone/{output_binary.name}\033[0m")
        else:
            print("\033[1;33mWarning: Compilation finished, but target binary was not found in 'dist/standalone/'.\033[0m")
            
    except subprocess.CalledProcessError as e:
        print(f"\033[1;31mError: PyInstaller exited with a non-zero exit code: {e}\033[0m")
        sys.exit(1)

def run_staged_build(script_dir):
    # Resolve local home staging directory to avoid cloud drive FUSE errors
    stage_dir = Path.home() / ".comfylab" / "build_stage"
    print(f"\n[Build] Unsupported filesystem (FUSE mount). Staging build to local home directory: {stage_dir}")
    
    if stage_dir.exists():
        try:
            shutil.rmtree(stage_dir)
        except Exception as e:
            print(f"\033[1;31mError: Failed to clean staging directory {stage_dir}: {e}\033[0m")
            sys.exit(1)
            
    stage_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Stage files (excluding python venv, node_modules, build directories)
    print(" -> Staging files to local disk...")
    shutil.copytree(script_dir, stage_dir, dirs_exist_ok=True, ignore=copy_ignore_stage)
    
    # 2. Check if pre-compiled frontend exists in source, and copy it to save compile time
    source_dist = script_dir / "frontend" / "dist"
    dest_dist = stage_dir / "frontend" / "dist"
    
    if source_dist.exists():
        print(" -> Copying existing precompiled frontend assets...")
        shutil.copytree(source_dist, dest_dist, dirs_exist_ok=True)
    else:
        # Run node compile inside local staging folder where symlinks work!
        print(" -> Compiled frontend not found. Staging Node packages and compiling...")
        check_node()
        build_frontend(stage_dir)
        
    # 3. Check for PyInstaller inside staging environment
    check_prerequisites()
    
    # 4. Run PyInstaller inside staged directory
    run_pyinstaller(stage_dir)
    
    # 5. Copy the final executable and external blocks folder back to cloud directory
    binary_name = "ComfyLAB.exe" if os.name == 'nt' else "ComfyLAB"
    staged_binary = stage_dir / "dist" / "standalone" / binary_name
    staged_blocks = stage_dir / "dist" / "standalone" / "comfylab" / "blocks"

    dest_dist_dir = script_dir / "dist" / "standalone"
    dest_dist_dir.mkdir(parents=True, exist_ok=True)
    dest_binary = dest_dist_dir / binary_name
    dest_blocks = dest_dist_dir / "comfylab" / "blocks"

    if staged_binary.exists():
        print(f" -> Copying compiled standalone binary back to: {dest_binary}")
        shutil.copy2(staged_binary, dest_binary)
        if os.name != 'nt':
            os.chmod(dest_binary, 0o755)

        if staged_blocks.exists():
            print(f" -> Copying core blocks folder back to: {dest_blocks}")
            if dest_blocks.exists():
                shutil.rmtree(dest_blocks)
            shutil.copytree(staged_blocks, dest_blocks)
            
        print(f"\n\033[1;32m=========================================================\033[0m")
        print(f"\033[1;32m  Standalone Binary Compiled Successfully!\033[0m")
        print(f"\033[1;32m  Location: {dest_binary}\033[0m")
        print(f"\033[1;32m  Folder Structure: {dest_dist_dir}/\033[0m")
        print(f"\033[1;32m=========================================================\033[0m\n")
    else:
        print("\033[1;31mError: Staged compilation finished, but target binary was not found.\033[0m")
        sys.exit(1)
        
    # 6. Clean up staging directory
    print(" -> Cleaning up local staging files...")
    try:
        shutil.rmtree(stage_dir)
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="ComfyLAB PyInstaller Builder")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], help="Auto-increment the version number before building")
    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()

    if args.bump:
        bump_version(script_dir, args.bump)

    
    # Check if filesystem supports symlinks. If not, run local staged build.
    if not check_symlink_support(script_dir):
        run_staged_build(script_dir)
    else:
        # Run build directly in the current directory
        check_prerequisites()
        
        # Ensure frontend/dist is built
        dist_dir = script_dir / "frontend" / "dist"
        if not dist_dir.exists():
            print("[Build] Compiled frontend assets not found at 'frontend/dist'.")
            print("Running frontend production build first...")
            check_node()
            build_frontend(script_dir)

        run_pyinstaller(script_dir)

if __name__ == "__main__":
    main()
