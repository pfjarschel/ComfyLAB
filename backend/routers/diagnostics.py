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

import shutil
import asyncio
import logging
from fastapi import APIRouter
from typing import Dict, Any

logger = logging.getLogger("backend.routers.diagnostics")

router = APIRouter(prefix="/diagnostics")

async def get_binary_version(binary: str, version_arg: str = "--version") -> str:
    """Runs the binary with version argument and returns the captured version string."""
    path = shutil.which(binary)
    if not path:
        return "Not Found"
    try:
        process = await asyncio.create_subprocess_exec(
            binary, version_arg,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=2.0)
        output = stdout.decode().strip() or stderr.decode().strip()
        # Clean up output to make it single line and short
        first_line = output.split('\n')[0] if output else "Installed"
        return first_line
    except Exception as e:
        logger.error(f"Failed to get version for {binary}: {e}")
        return "Installed (Version unknown)"

@router.get("/check")
async def check_dependencies() -> Dict[str, Any]:
    """
    Checks the local system PATH for interpreters and compiler toolchains.
    Returns installation status, version, and instructions for missing elements.
    """
    # 1. Check Python Lupa package
    try:
        import lupa
        lupa_status = f"Installed (Lupa {lupa.__version__})"
        lupa_installed = True
    except ImportError:
        lupa_status = "Not Found (Optional, fallback to Lua executable will be used)"
        lupa_installed = False

    # 2. Query binary versions on PATH
    lua_ver = await get_binary_version("lua", "-v")
    julia_ver = await get_binary_version("julia", "--version")
    node_ver = await get_binary_version("node", "--version")
    cargo_ver = await get_binary_version("cargo", "--version")
    ts_node_ver = await get_binary_version("ts-node", "--version")
    tsx_ver = await get_binary_version("tsx", "--version")
    r_ver = await get_binary_version("Rscript", "--version")
    octave_ver = await get_binary_version("octave", "--version")
    wolfram_ver = await get_binary_version("wolframscript", "--version")

    # 3. Compile instructions for missing toolchains
    instructions = {}
    if lua_ver == "Not Found" and not lupa_installed:
        instructions["lua"] = "Install Lua interpreter (e.g. 'sudo apt install lua5.3' or 'brew install lua'). Learn more at https://www.lua.org/download.html."
    if julia_ver == "Not Found":
        instructions["julia"] = "Install Julia from the official downloads page: https://julialang.org/downloads/ (ensure 'julia' is on system PATH)."
    if node_ver == "Not Found":
        instructions["node"] = "Install Node.js from the official downloads page: https://nodejs.org/en/download/ (e.g. 'sudo apt install nodejs' or 'brew install node')."
    elif ts_node_ver == "Not Found" and tsx_ver == "Not Found":
        instructions["typescript"] = "To execute TypeScript scripts in Node, install 'tsx' or 'ts-node' globally via npm: run 'npm install -g tsx' or 'npm install -g ts-node typescript'. Learn more at https://tsx.is/."
    if cargo_ver == "Not Found":
        instructions["rust"] = "Install Rust & Cargo via rustup: run 'curl --proto \"=https\" --tlsv1.2 -sSf https://sh.rustup.rs | sh' or download the installer from https://www.rust-lang.org/tools/install."
    if r_ver == "Not Found":
        instructions["r"] = "Install R from the official website: https://cloud.r-project.org/ (e.g. 'sudo apt install r-base' or 'brew install r'). Ensure the 'jsonlite' package is installed for data serialization."
    if octave_ver == "Not Found":
        instructions["octave"] = "Install GNU Octave from the official page: https://www.gnu.org/software/octave/download (e.g. 'sudo apt install octave' or 'brew install octave')."
    if wolfram_ver == "Not Found":
        instructions["wolfram"] = "Install Wolfram Engine and WolframScript. Learn more at https://www.wolfram.com/wolframscript/."

    return {
        "status": "success",
        "dependencies": {
            "python_lupa": {
                "installed": lupa_installed,
                "version": lupa_status,
                "description": "In-process LuaJIT integration"
            },
            "lua": {
                "installed": lua_ver != "Not Found",
                "version": lua_ver,
                "description": "Lua Script Interpreter"
            },
            "julia": {
                "installed": julia_ver != "Not Found",
                "version": julia_ver,
                "description": "Julia Scientific Computing Language"
            },
            "node": {
                "installed": node_ver != "Not Found",
                "version": node_ver,
                "description": "Node.js JavaScript Runtime"
            },
            "ts_node": {
                "installed": ts_node_ver != "Not Found",
                "version": ts_node_ver,
                "description": "TypeScript execution for Node"
            },
            "tsx": {
                "installed": tsx_ver != "Not Found",
                "version": tsx_ver,
                "description": "TypeScript Execute (tsx) CLI runner"
            },
            "cargo": {
                "installed": cargo_ver != "Not Found",
                "version": cargo_ver,
                "description": "Rust Package Manager & Cargo Script Runner"
            },
            "r": {
                "installed": r_ver != "Not Found",
                "version": r_ver,
                "description": "R Language for Statistical Computing"
            },
            "octave": {
                "installed": octave_ver != "Not Found",
                "version": octave_ver,
                "description": "GNU Octave (MATLAB-compatible environment)"
            },
            "wolfram": {
                "installed": wolfram_ver != "Not Found",
                "version": wolfram_ver,
                "description": "Wolfram Engine & wolframscript CLI"
            }
        },
        "instructions": instructions
    }
