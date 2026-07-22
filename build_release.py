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

def check_prerequisites():
    if shutil.which("npm") is None:
        print("\033[1;31mError: 'npm' (Node.js) is not installed.\033[0m")
        print("Node.js and npm are required to compile the React frontend bundle.")
        sys.exit(1)

def check_symlink_support(script_dir):
    # Test symlink creation to detect FUSE cloud mount limitations
    test_link = script_dir / "test_symlink_probe"
    try:
        if test_link.exists():
            test_link.unlink()
        os.symlink("nonexistent_target", test_link)
        test_link.unlink()
        return True
    except OSError:
        if test_link.exists():
            try:
                test_link.unlink()
            except Exception:
                pass
        return False

def copy_ignore_stage(path, names):
    # Exclude caches, virtual environments, VCS data, build artifacts,
    # previous release packages, and any leftover in-repo staging folder
    ignored = []
    for name in names:
        if name in ("__pycache__", ".pytest_cache", ".venv", "tests", "node_modules",
                    ".git", "build", "dist", ".release_staging"):
            ignored.append(name)
        elif name.endswith(".pyc") or name.endswith(".pyo") or name.endswith(".pyd"):
            ignored.append(name)
        elif name.endswith(".zip"):
            ignored.append(name)
    return ignored

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
    # Stage inside a dedicated hidden folder. NEVER stage directly at
    # script_dir / "comfylab": that is the real source package, and the
    # cleanup below would delete the engine source tree.
    staging_root = script_dir / ".release_staging"
    release_dir = staging_root / "comfylab"

    if staging_root.exists():
        shutil.rmtree(staging_root)
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
    
    if (script_dir / "VERSION").exists():
        shutil.copy2(script_dir / "VERSION", release_dir / "VERSION")
    
    # 5. Enforce executable permissions on start.sh inside the package
    if os.name != 'nt':
        try:
            os.chmod(release_dir / "start.sh", 0o755)
            print(" -> Setting executable permissions on start.sh...")
        except Exception as e:
            print(f" -> Warning: Failed to set executable permissions on start.sh: {e}")

    return release_dir

def compress_release(script_dir, release_dir, version):
    print(f"\n[Build 3/3] Compressing release package (v{version})...")
    release_name = f"comfylab-release-v{version}"
    zip_file = script_dir / f"{release_name}.zip"
    if zip_file.exists():
        zip_file.unlink()
        
    shutil.make_archive(
        base_name=str(script_dir / release_name),
        format='zip',
        root_dir=str(release_dir.parent),
        base_dir=release_dir.name
    )

    print(" -> Cleaning up temporary staging folder...")
    shutil.rmtree(release_dir.parent)
    
    print(f"\n\033[1;32m=========================================================\033[0m")
    print(f"\033[1;32m  Build Success! Created: {zip_file.name}\033[0m")
    print(f"\033[1;32m=========================================================\033[0m\n")

def bump_version(script_dir, bump_type):
    version_file = script_dir / "VERSION"
    version_str = "0.0.0"
    if version_file.exists():
        version_str = version_file.read_text().strip()
    
    parts = version_str.split(".")
    while len(parts) < 3:
        parts.append("0")
    
    try:
        major, minor, patch = map(int, parts[:3])
    except ValueError:
        print(f"\033[1;31mError: VERSION file contains invalid semver '{version_str}'. Cannot bump.\033[0m")
        sys.exit(1)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
        
    new_version = f"{major}.{minor}.{patch}"
    version_file.write_text(new_version)
    print(f"\033[1;36m[Version] Bumped {bump_type} version: {version_str} -> {new_version}\033[0m")
    return new_version

def get_version(script_dir):
    version_file = script_dir / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.0.0"

def run_staged_build(script_dir, version):
    """
    Cloud/FUSE-safe release build: stages everything to a local home directory,
    compiles the frontend and assembles/compresses the package there, then copies
    only the final .zip back to the repo directory.
    """
    stage_dir = Path.home() / ".comfylab" / "release_stage"
    print(f"\n[Build] Unsupported filesystem (FUSE/cloud mount). Staging build to local directory: {stage_dir}")

    if stage_dir.exists():
        try:
            shutil.rmtree(stage_dir)
        except Exception as e:
            print(f"\033[1;31mError: Failed to clean staging directory {stage_dir}: {e}\033[0m")
            sys.exit(1)

    stage_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Stage the source tree to local disk (excluding artifacts and leftovers)
        print(" -> Staging source files to local disk...")
        shutil.copytree(script_dir, stage_dir, dirs_exist_ok=True, ignore=copy_ignore_stage)

        # 2. Compile the frontend locally (npm/vite are unreliable on cloud drives)
        check_prerequisites()
        build_frontend(stage_dir)

        # 3. Assemble the release structure locally
        release_dir = assemble_release(stage_dir)

        # 4. Compress, writing the final .zip back to the repo directory
        compress_release(script_dir, release_dir, version)
    finally:
        # Always clean up the local staging area, even on failure
        print(" -> Cleaning up local staging files...")
        try:
            shutil.rmtree(stage_dir)
        except Exception:
            pass

def main():
    parser = argparse.ArgumentParser(description="ComfyLAB Release Builder")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], help="Auto-increment the version number before building")
    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    
    if args.bump:
        version = bump_version(script_dir, args.bump)
    else:
        version = get_version(script_dir)
        
    print(f"\n[Build Init] Starting ComfyLAB build for v{version}...")

    # On cloud/FUSE drives (no symlink support), stage the whole build locally
    # to avoid sync churn and npm/vite flakiness; otherwise build in place.
    if not check_symlink_support(script_dir):
        run_staged_build(script_dir, version)
    else:
        check_prerequisites()
        build_frontend(script_dir)
        release_dir = assemble_release(script_dir)
        compress_release(script_dir, release_dir, version)

if __name__ == "__main__":
    main()
