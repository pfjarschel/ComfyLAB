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
import logging
import secrets
import base64
import shutil
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.routers.execution import router as execution_router
from backend.routers.settings import router as settings_router
from backend.routers.diagnostics import router as diagnostics_router
from backend.routers.workspace import router as workspace_router
from backend.routers.packages import router as packages_router
from backend.routers.blocks import router as blocks_router
import comfylab.engine.config as config_module
from comfylab.engine.config import get_config
from comfylab.engine.registry import BLOCK_REGISTRY, load_all_clusters_deferred
from backend.workspace import set_workspace_path
from backend.auth import verify_access_token, verify_user_password
from backend.ratelimit import is_blocked, record_failure, record_success, block_remaining, remaining_attempts, is_first_attempt
from comfylab.engine.logging import setup_logging

# Initialize structured logging first thing on startup
setup_logging()
logger = logging.getLogger("backend.main")

# Word lists directory (relative to this file)
_WORD_DIR = Path(__file__).parent

def _load_wordlist(filename):
    path = _WORD_DIR / filename
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]

# Generate adjective-noun remote access token
def generate_server_token():
    adjectives = _load_wordlist("adjectives.txt")
    nouns = _load_wordlist("nouns.txt")
    # secrets.choice: token is a security credential, so use a CSPRNG
    return f"{secrets.choice(adjectives)}-{secrets.choice(nouns)}"


SERVER_TOKEN = generate_server_token()
config_module.SESSION_TOKEN = SERVER_TOKEN

print("\033[1;35m")
print("  ========================================================")
print(f"   [ComfyLAB Security] Remote Access Token: {SERVER_TOKEN}  ")
print("  ========================================================")
print("\033[0m")

app = FastAPI(
    title="ComfyLAB Virtual Sandbox API",
    description="Backend API serving the ComfyLAB push/pull block execution engine and WebSocket telemetry."
)

API_PATHS = {"/run", "/pause", "/resume", "/abort", "/status", "/blocks", "/parse_script", "/validate_script", "/workspace", "/settings"}

def is_test_environment() -> bool:
    """Checks if the application is running under an active test runner (pytest/unittest)."""
    return (
        os.getenv("COMFYLAB_TESTING") == "1"
        or os.getenv("PYTEST_CURRENT_TEST") is not None
        or any("pytest" in arg.lower() for arg in sys.argv)
    )

def get_frontend_dist_path() -> Path:
    """Resolves the pre-compiled frontend assets directory across development, production, and frozen standalone modes."""
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            dist = Path(meipass) / "frontend" / "dist"
            if dist.exists():
                return dist
        exe_dist = Path(sys.executable).parent / "frontend" / "dist"
        if exe_dist.exists():
            return exe_dist

    current_dir = Path(__file__).parent.resolve()
    source_dist = current_dir.parent / "frontend" / "dist"
    if source_dist.exists():
        return source_dist

    cwd_dist = Path.cwd() / "frontend" / "dist"
    if cwd_dist.exists():
        return cwd_dist

    return source_dist

# Security middleware to enforce remote access token verification
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Bypass OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
        
    path = request.url.path
    is_api = any(path == p or path.startswith(p + "/") for p in API_PATHS)

    client_host = request.client.host if request.client else "127.0.0.1"
    is_testing = is_test_environment()
    is_local = is_testing or client_host in ("127.0.0.1", "::1", "localhost", "testserver")
    
    if is_api and not is_local:
        if is_blocked(client_host):
            record_failure(client_host)
            retry = block_remaining(client_host)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Too many failed attempts. Try again in {retry}s.",
                    "retry_after_seconds": retry
                },
                headers={"Retry-After": str(retry)}
            )
        # Check authentication token/credentials
        token = ""
        auth_header = request.headers.get("Authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif auth_header.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = decoded.split(":", 1)
                if verify_user_password(username, password):
                    record_success(client_host)
                    return await call_next(request)
            except Exception:
                pass
                
        if not token:
            token = request.headers.get("X-ComfyLAB-Auth", "").strip()
            
        if not token:
            token = request.query_params.get("token", "").strip()
            
        # Validate token against SESSION_TOKEN or custom_users
        is_valid = verify_access_token(token)
                    
        if not is_valid:
            if is_first_attempt(client_host):
                print(f"\033[1;35m[ComfyLAB] Remote Access Token: {SERVER_TOKEN}\033[0m")
            record_failure(client_host)
            if is_blocked(client_host):
                retry = block_remaining(client_host)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Too many failed attempts. Try again in {retry}s.",
                        "retry_after_seconds": retry
                    },
                    headers={"Retry-After": str(retry)}
                )
            retry_hint = f" {remaining_attempts(client_host)} attempt(s) remaining before temporary block."
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Invalid or missing remote access token/credentials." + retry_hint}
            )

    record_success(client_host)
    return await call_next(request)

# Enable CORS for frontend cross-origin requests (must be outermost so error responses get CORS headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(execution_router)
app.include_router(settings_router)
app.include_router(diagnostics_router)
app.include_router(workspace_router)
app.include_router(packages_router)
app.include_router(blocks_router)

@app.on_event("startup")
async def startup_event():
    config = get_config()
    last_ws = config.get("last_workspace", "")
    if last_ws:
        try:
            ws_path = Path(last_ws)
            set_workspace_path(last_ws)
            logger.info(f"Auto-restored last workspace: {last_ws}")
            
            # Clean up temporary package files on server startup
            for subdir in ["blueprints", "blocks", "clusters"]:
                temp_dir = ws_path / subdir / ".temp"
                if temp_dir.exists():
                    try:
                        shutil.rmtree(temp_dir)
                        logger.info(f"Purged temporary directory on startup: {temp_dir}")
                    except Exception as purge_err:
                        logger.error(f"Failed to purge temporary directory {temp_dir} on startup: {purge_err}")
            tmp_dir = ws_path / ".tmp"
            if tmp_dir.exists():
                try:
                    shutil.rmtree(tmp_dir)
                    logger.info(f"Purged runtime temp directory on startup: {tmp_dir}")
                except Exception as purge_err:
                    logger.error(f"Failed to purge runtime temp directory {tmp_dir} on startup: {purge_err}")
        except Exception as e:
            logger.error(f"Failed to auto-restore last workspace {last_ws}: {e}")
    try:
        load_all_clusters_deferred()
        logger.info(f"Cluster loading complete. Total registered blocks: {len(BLOCK_REGISTRY)}")
    except Exception as e:
        logger.error(f"Cluster loading skipped (will retry on reload): {e}")

IS_TESTING = is_test_environment()
FRONTEND_DIST = get_frontend_dist_path()

if FRONTEND_DIST.exists() and not IS_TESTING:
    logger.info(f"Serving pre-compiled frontend from: {FRONTEND_DIST}")
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
else:
    logger.info("Pre-compiled frontend not found or in testing mode. Fallback API route active.")
    @app.get("/")
    async def read_root():
        return {
            "status": "online",
            "service": "ComfyLAB Core Engine API"
        }
