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

from comfylab.engine.config import get_config, update_config
from backend.workspace import get_workspace_path
from comfylab.engine.registry import NODE_REGISTRY
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

