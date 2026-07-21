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

import asyncio
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from comfylab.engine.logging import run_id_var, block_id_var
from comfylab.engine.config import get_config


logger = logging.getLogger("backend.routers.execution")

from comfylab.engine.executor import ExecutionEngine

from comfylab.blocks.script import parse_script_decorators, validate_code as validate_python
from comfylab.blocks.script_lua import parse_lua_decorators, validate_code as validate_lua
from comfylab.blocks.script_js import parse_js_decorators, validate_code as validate_js
from comfylab.blocks.script_julia import validate_code as validate_julia
from comfylab.blocks.script_r import validate_code as validate_r
from comfylab.blocks.script_rust import parse_rust_decorators
from comfylab.blocks.script_octave import parse_octave_decorators
from comfylab.blocks.script_wolfram import parse_wolfram_decorators
import shutil
import tempfile
import os
import inspect
from backend.manager import TelemetryConnectionManager

PARSER_REGISTRY = {
    "python": parse_script_decorators,
    "lua": parse_lua_decorators,
    "javascript": parse_js_decorators,
    "typescript": parse_js_decorators,
    "rust": parse_rust_decorators,
    "julia": parse_script_decorators,
    "r": parse_script_decorators,
    "octave": parse_octave_decorators,
    "matlab": parse_octave_decorators,
    "wolfram": parse_wolfram_decorators,
}

VALIDATOR_REGISTRY = {
    "python": validate_python,
    "lua": validate_lua,
    "javascript": lambda code: validate_js(code, "javascript"),
    "typescript": lambda code: validate_js(code, "typescript"),
    "julia": validate_julia,
    "r": validate_r,
}

# Import comfylab.blocks to trigger dynamic recursive auto-discovery
import comfylab.blocks

router = APIRouter()

# Global singletons for execution coordination and telemetry routing
engine = ExecutionEngine()
manager = TelemetryConnectionManager()

# Bind the engine's telemetry updates to the WebSocket broadcast manager
async def on_telemetry_event(run_id: str, message: Any):
    if isinstance(message, bytes):
        target_run_id = message[:36].decode('utf-8')
        binary_payload = message[36:]
        await manager.broadcast(target_run_id, binary_payload)
    else:
        await manager.broadcast(run_id, message)

engine.telemetry_callback = on_telemetry_event


class BlueprintPayload(BaseModel):
    blocks: list
    links: list
    raw_canvas: Dict[str, Any] = None


@router.post("/run")
async def run_graph(payload: BlueprintPayload):
    """
    Submits a blueprint JSON for execution.
    Launches execution as a non-blocking background task, returning the run_id immediately.
    """
    if engine.state == "RUNNING" or engine.state == "PAUSED":
        raise HTTPException(status_code=400, detail="The execution engine is already running or paused.")

    run_id = str(uuid.uuid4())
    engine.current_raw_canvas = payload.raw_canvas

    async def background_execution():
        try:
            # Wait up to 1.0 second for the frontend to establish its WebSocket subscription
            for _ in range(10):
                if run_id in manager.active_connections and manager.active_connections[run_id]:
                    break
                await asyncio.sleep(0.1)

            await manager.broadcast(run_id, {"type": "run_status", "status": "running"})
            from comfylab.engine.models import BlueprintModel
            blueprint_model = BlueprintModel.model_validate(payload.model_dump())
            engine.load_blueprint(blueprint_model)
            await engine.run(run_id=run_id)
            if engine.state == "ABORTED":
                await manager.broadcast(run_id, {"type": "run_status", "status": "aborted"})
            else:
                await manager.broadcast(run_id, {"type": "run_status", "status": "completed"})
        except Exception as e:
            await manager.broadcast(run_id, {"type": "run_status", "status": "failed", "error": str(e)})

    asyncio.create_task(background_execution())
    return {"run_id": run_id, "status": "started"}


@router.post("/pause")
async def pause_graph():
    """Pauses graph execution."""
    await engine.pause()
    return {"status": "paused"}


@router.post("/resume")
async def resume_graph():
    """Resumes graph execution."""
    await engine.resume()
    return {"status": "resumed"}


@router.post("/abort")
async def abort_graph():
    """Triggers an emergency shutdown, returning abort confirmations."""
    await engine.abort()
    return {"status": "aborted"}


@router.get("/status")
async def get_status():
    """Returns the current state of the execution engine."""
    res = {"state": engine.state}
    if engine.state in ("RUNNING", "PAUSED") and getattr(engine, "current_run_id", None):
        res["run_id"] = engine.current_run_id
        res["raw_canvas"] = getattr(engine, "current_raw_canvas", None)
    return res



@router.post("/blocks/{block_id}/clear")
async def clear_block_data(block_id: str):
    """Resets transient state and tears down persistent state for a given block."""
    block = engine.blocks.get(block_id)
    if not block:
        block = engine.persistent_blocks.get(block_id)

    if block:
        if hasattr(block, "clear_data"):
            await block.clear_data()
        
        if block_id in engine.persistent_blocks:
            try:
                await block.teardown()
            except Exception as e:
                logger.error(f"Teardown failed on clear for block '{block_id}': {e}")
            engine.persistent_blocks.pop(block_id, None)
            
        return {"status": "success"}
    else:
        return {"status": "skipped", "reason": "Block not loaded in current engine or persistent cache"}


@router.post("/blocks/clear_persistent")
async def clear_all_persistent_blocks():
    """Tears down and clears all persistent blocks currently cached in the engine."""
    for block_id, block in list(engine.persistent_blocks.items()):
        try:
            await block.teardown()
        except Exception as e:
            logger.error(f"Teardown failed during clear_persistent for block '{block_id}': {e}")
    engine.persistent_blocks.clear()
    return {"status": "success"}



class ScriptCodePayload(BaseModel):
    code: str
    language: str = "python"


@router.post("/parse_script")
async def parse_script(payload: ScriptCodePayload):
    """
    Parses decorator comments for inputs and outputs from script code depending on language.
    """
    try:
        lang = payload.language.lower()
        parser = PARSER_REGISTRY.get(lang, parse_script_decorators)
        inputs, outputs = parser(payload.code)
        return {"inputs": inputs, "outputs": outputs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse decorators for {payload.language}: {str(e)}")


@router.post("/validate_script")
async def validate_script(payload: ScriptCodePayload):
    """
    Validates script syntax. Runs compiler or interpreter check dry-runs without executing.
    """
    lang = payload.language.lower()
    validator = VALIDATOR_REGISTRY.get(lang)
    if validator:
        try:
            if inspect.iscoroutinefunction(validator):
                res = await validator(payload.code)
            else:
                res = validator(payload.code)
            return res
        except Exception as e:
            return {"valid": False, "error": str(e)}
    return {"valid": True}


@router.websocket("/telemetry/{run_id}")
async def telemetry_websocket(websocket: WebSocket, run_id: str):
    """Establishes a WebSocket connection for streaming telemetry of a run_id and updating running properties."""
    client_host = websocket.client.host if websocket.client else "127.0.0.1"
    is_local = client_host in ("127.0.0.1", "::1", "localhost", "testserver")
    
    if not is_local:
        from backend.ratelimit import is_blocked, record_failure, record_success, block_remaining

        if is_blocked(client_host):
            record_failure(client_host)
            retry = block_remaining(client_host)
            await websocket.close(code=4003, reason=f"Too many failed attempts. Try again in {retry}s.")
            return

        token = websocket.query_params.get("token", "").strip()
        from comfylab.engine.config import SESSION_TOKEN, get_config
        
        is_valid = False
        if token == SESSION_TOKEN:
            is_valid = True
        elif ":" in token:
            parts = token.split(":", 1)
            if len(parts) == 2:
                u, p = parts
                custom_users = get_config().get("custom_users", {})
                if custom_users.get(u) == p:
                    is_valid = True
                    
        if not is_valid:
            record_failure(client_host)
            if is_blocked(client_host):
                retry = block_remaining(client_host)
                await websocket.accept()
                await websocket.close(code=4003, reason=f"Too many failed attempts. Try again in {retry}s.")
                return
            await websocket.accept()
            await websocket.close(code=4001, reason="Unauthorized: Invalid remote access token.")
            return

        record_success(client_host)

    await manager.connect(run_id, websocket)
    try:
        while True:
            # Keep the connection alive and listen for optional incoming client heartbeats or property updates
            msg_text = await websocket.receive_text()
            try:
                import json
                data = json.loads(msg_text)
                if isinstance(data, dict) and data.get("type") == "update_property":
                    block_id = data.get("block_id")
                    name = data.get("name")
                    value = data.get("value")
                    if block_id and name is not None:
                        # Set context vars so the update property log is correctly tagged
                        run_token = run_id_var.set(run_id)
                        block_token = block_id_var.set(block_id)
                        try:
                            # Update the property in the running engine blocks
                            block = engine.blocks.get(block_id)
                            if block:
                                block.properties[name] = value
                                block.properties[name.lower()] = value
                                logger.info(f"Updated running block property {name} = {value}")
                        finally:
                            run_id_var.reset(run_token)
                            block_id_var.reset(block_token)
            except (json.JSONDecodeError, TypeError):
                # Silent fallback for simple text heartbeats or invalid JSON
                pass
    except WebSocketDisconnect:
        manager.disconnect(run_id, websocket)

