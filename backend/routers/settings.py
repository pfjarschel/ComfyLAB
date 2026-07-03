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

import datetime
import re
import json
import sys
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from comfylab.engine.config import get_config, get_global_user_nodes_dir, get_global_user_macros_dir, update_config
from backend.workspace import get_workspace_path
from comfylab.nodes.loader import load_module_from_filepath
from comfylab.engine.registry import NODE_REGISTRY
from comfylab.nodes.publisher import generate_node_class_code
from comfylab.nodes.macro import parse_macro_boundary_pins
import importlib

SCRIPTING_TOGGLES = {
    "enable_lua_scripting": ("comfylab.nodes.script_lua", "LuaScriptNode", "script/lua"),
    "enable_julia_scripting": ("comfylab.nodes.script_julia", "JuliaScriptNode", "script/julia"),
    "enable_js_scripting": ("comfylab.nodes.script_js", ["JavaScriptScriptNode", "TypeScriptScriptNode"], ["script/javascript", "script/typescript"]),
    "enable_rust_scripting": ("comfylab.nodes.script_rust", "RustScriptNode", "script/rust"),
    "enable_r_scripting": ("comfylab.nodes.script_r", "RScriptNode", "script/r"),
    "enable_octave_scripting": ("comfylab.nodes.script_octave", "OctaveScriptNode", "script/octave"),
    "enable_wolfram_scripting": ("comfylab.nodes.script_wolfram", "WolframScriptNode", "script/wolfram"),
}

router = APIRouter()

class SettingsPayload(BaseModel):
    custom_node_dirs: List[str]
    script_timeout: float
    visa_backend: str
    last_workspace: str
    enable_lua_scripting: bool = False
    enable_julia_scripting: bool = False
    enable_js_scripting: bool = False
    enable_rust_scripting: bool = False
    enable_r_scripting: bool = False
    enable_octave_scripting: bool = False
    enable_wolfram_scripting: bool = False
    external_python_path: str = ""
    creator_identity: str = ""
    trusted_origins: List[str] = []
    custom_users: Dict[str, str] = {}


@router.get("/settings")
async def get_settings():
    config = get_config().copy()
    config.pop("custom_users", None)
    return config

@router.post("/settings")
async def save_settings(payload: SettingsPayload):
    existing = get_config()
    dump = payload.model_dump()
    
    # Always preserve the existing custom_users configured manually in config.json
    dump["custom_users"] = existing.get("custom_users", {})
    
    # Preserve creator_identity and trusted_origins if they are empty or not provided
    if not dump.get("creator_identity") and existing.get("creator_identity"):
        dump["creator_identity"] = existing["creator_identity"]
    if not dump.get("trusted_origins") and existing.get("trusted_origins"):
        dump["trusted_origins"] = existing["trusted_origins"]
        
    updated = update_config(dump)

    
    # Selectively synchronize script node registrations to avoid breaking test-only nodes
    for key, (module_path, class_names, type_names) in SCRIPTING_TOGGLES.items():
        classes = class_names if isinstance(class_names, list) else [class_names]
        types = type_names if isinstance(type_names, list) else [type_names]
        
        if updated.get(key, False):
            try:
                mod = importlib.import_module(module_path)
                for cls_name, t_name in zip(classes, types):
                    NODE_REGISTRY[t_name] = getattr(mod, cls_name)
            except Exception as e:
                import logging
                logging.getLogger("backend.routers.settings").error(
                    f"Failed to dynamically synchronize script node registry for {module_path}: {e}"
                )
        else:
            for t_name in types:
                NODE_REGISTRY.pop(t_name, None)
        
    return updated

class PublishNodePayload(BaseModel):
    display_name: str
    category: str
    icon: str
    description: str
    code: str
    language: str = "python"
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    destination: str # "global" or "workspace"






@router.post("/nodes/publish")
async def publish_node(payload: PublishNodePayload):
    # Determine directory
    if payload.destination == "global":
        target_dir = get_global_user_nodes_dir()
    elif payload.destination == "workspace":
        workspace_path = get_workspace_path()
        if not workspace_path:
            raise HTTPException(status_code=400, detail="No active workspace found to publish node to.")
        target_dir = workspace_path / "nodes"
        target_dir.mkdir(parents=True, exist_ok=True)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid destination: {payload.destination}")

    # Generate file name
    clean_name = re.sub(r'[^a-zA-Z0-9\s_-]', '', payload.display_name)
    clean_name = re.sub(r'[\s_-]+', '_', clean_name).strip('_').lower()
    
    if not clean_name:
        raise HTTPException(status_code=400, detail="Invalid node name.")

    prefix = "user" if payload.destination == "global" else "workspace"
    type_name = f"{prefix}/{clean_name}"
    
    # Class name formatting
    words = re.sub(r'[^a-zA-Z0-9\s_-]', '', payload.display_name).replace('_', ' ').replace('-', ' ').split()
    class_name = "".join(w.capitalize() for w in words)
    if not class_name.endswith("Node"):
        class_name += "Node"
        
    filename = f"{clean_name}.py"
    filepath = target_dir / filename

    # Generate Python code
    code_content = generate_node_class_code(
        display_name=payload.display_name,
        class_name=class_name,
        type_name=type_name,
        category=payload.category,
        icon=payload.icon,
        description=payload.description,
        inputs=payload.inputs,
        outputs=payload.outputs,
        original_code=payload.code,
        language=payload.language,
        destination=payload.destination,
        clean_name=clean_name
    )

    # Validate syntax with compile()
    try:
        compile(code_content, f"<publish:{clean_name}>", "exec")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Generated code has syntax errors: {e}")

    # Write file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write node class file: {e}")

    # Sign file
    try:
        from comfylab.engine.security import sign_python_file
        sign_python_file(filepath)
    except Exception as e:
        if filepath.exists():
            filepath.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to cryptographically sign node class file: {e}")

    # Trigger hot-reload
    try:
        load_module_from_filepath(str(filepath))
    except Exception as e:
        # If it failed to import, clean up written file to avoid breaking next starts
        if filepath.exists():
            filepath.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to import/register published node: {e}")

    return {
        "success": True,
        "type": type_name,
        "file_path": str(filepath)
    }

class PublishMacroPayload(BaseModel):
    display_name: str
    category: str
    icon: str
    description: str
    internal_blueprint: Dict[str, Any]
    boundary_pins: Dict[str, Any]
    destination: str  # "global", "workspace", or "temp"
    type_name: Optional[str] = None


@router.post("/nodes/publish_macro")
async def publish_macro(payload: PublishMacroPayload):
    if payload.destination == "global":
        target_dir = get_global_user_macros_dir()
        prefix = "user/macro"
    elif payload.destination == "workspace":
        workspace_path = get_workspace_path()
        if not workspace_path:
            raise HTTPException(status_code=400, detail="No active workspace found to publish macro to.")
        target_dir = workspace_path / "macros"
        target_dir.mkdir(parents=True, exist_ok=True)
        prefix = "workspace/macro"
    elif payload.destination == "temp":
        workspace_path = get_workspace_path()
        if not workspace_path:
            raise HTTPException(status_code=400, detail="No active workspace found to publish macro to.")
        target_dir = workspace_path / "macros" / ".temp"
        target_dir.mkdir(parents=True, exist_ok=True)
        if payload.type_name and "/" in payload.type_name:
            prefix = payload.type_name.rsplit("/", 1)[0]
        else:
            prefix = "workspace/macro"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid destination: {payload.destination}")

    clean_name = re.sub(r'[^a-zA-Z0-9\s_-]', '', payload.display_name)
    clean_name = re.sub(r'[\s_-]+', '_', clean_name).strip('_').lower()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Invalid node name.")

    type_name = f"{prefix}/{clean_name}"
    filename = f"{clean_name}.macro.json"
    filepath = target_dir / filename

    boundary_pins = parse_macro_boundary_pins(payload.internal_blueprint, payload.boundary_pins)

    macro_json = {
        "name": payload.display_name,
        "type_name": type_name,
        "category": payload.category,
        "icon": payload.icon,
        "display_name": payload.display_name,
        "description": payload.description,
        "internal_blueprint": payload.internal_blueprint,
        "boundary_pins": boundary_pins
    }

    from comfylab.engine.models import MacroDefinitionModel
    try:
        MacroDefinitionModel.model_validate(macro_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid macro definition: {e}")

    try:
        from comfylab.engine.security import sign_json
        signed_macro = sign_json(macro_json)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(signed_macro, f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write macro file: {e}")

    try:
        from comfylab.nodes.macro import load_macro_from_file
        load_macro_from_file(str(filepath))
    except Exception as e:
        if filepath.exists():
            filepath.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to register published macro: {e}")

    return {
        "success": True,
        "type": type_name,
        "file_path": str(filepath)
    }


@router.get("/macro/{type_name:path}")
async def get_macro_definition(type_name: str):
    from pathlib import Path
    from comfylab.engine.config import get_global_user_macros_dir
    from backend.workspace import get_workspace_path

    slug = type_name.split("/")[-1] if "/" in type_name else type_name
    candidates = []
    candidates.append(get_global_user_macros_dir() / f"{slug}.macro.json")
    ws = get_workspace_path()
    if ws:
        candidates.append(ws / "macros" / f"{slug}.macro.json")
        candidates.append(ws / "macros" / ".temp" / f"{slug}.macro.json")

    for candidate in candidates:
        if candidate.exists():
            with open(candidate, "r", encoding="utf-8") as f:
                data = json.load(f)
                if ".temp" in candidate.parts:
                    data["_is_temp"] = True
                return data

    raise HTTPException(status_code=404, detail=f"Macro definition not found for type '{type_name}'")



