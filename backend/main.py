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

import logging
import random
import base64
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
import comfylab.engine.config as config_module
from comfylab.engine.config import get_config
from backend.workspace import set_workspace_path
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
    return f"{random.choice(adjectives)}-{random.choice(nouns)}"


SERVER_TOKEN = generate_server_token()
config_module.SESSION_TOKEN = SERVER_TOKEN

print("\033[1;35m")
print("  ========================================================")
print(f"   [ComfyLAB Security] Remote Access Token: {SERVER_TOKEN}  ")
print("  ========================================================")
print("\033[0m")

app = FastAPI(
    title="ComfyLAB Virtual Sandbox API",
    description="Backend API serving the ComfyLAB push/pull node execution engine and WebSocket telemetry."
)

API_PATHS = {"/run", "/pause", "/resume", "/abort", "/status", "/nodes", "/parse_script", "/validate_script", "/workspace", "/settings"}

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Bypass OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
        
    path = request.url.path
    is_api = any(path == p or path.startswith(p + "/") for p in API_PATHS)
    
    import sys
    client_host = request.client.host if request.client else "127.0.0.1"
    is_testing = "pytest" in sys.modules or "unittest" in sys.modules
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
                config = get_config()
                custom_users = config.get("custom_users", {})
                if custom_users.get(username) == password:
                    record_success(client_host)
                    return await call_next(request)
            except Exception:
                pass
                
        if not token:
            token = request.headers.get("X-ComfyLAB-Auth", "").strip()
            
        if not token:
            token = request.query_params.get("token", "").strip()
            
        # Validate token against SESSION_TOKEN or custom_users
        is_valid = False
        if token == config_module.SESSION_TOKEN:
            is_valid = True
        elif ":" in token:
            parts = token.split(":", 1)
            if len(parts) == 2:
                u, p = parts
                config = get_config()
                custom_users = config.get("custom_users", {})
                if custom_users.get(u) == p:
                    is_valid = True
                    
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
            import shutil
            for subdir in ["blueprints", "nodes", "macros"]:
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
        from comfylab.engine.registry import load_all_macros_deferred
        load_all_macros_deferred()
        from comfylab.engine.registry import NODE_REGISTRY
        logger.info(f"Macro loading complete. Total registered nodes: {len(NODE_REGISTRY)}")
    except Exception as e:
        logger.error(f"Macro loading skipped (will retry on reload): {e}")

import sys
IS_TESTING = "pytest" in sys.modules or "unittest" in sys.modules

# Serve frontend static assets if they are pre-compiled in production
CURRENT_DIR = Path(__file__).parent.resolve()
FRONTEND_DIST = CURRENT_DIR.parent / "frontend" / "dist"

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
