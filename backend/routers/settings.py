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

import importlib
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict

from comfylab.engine.config import get_config, update_config
from comfylab.engine.registry import BLOCK_REGISTRY

logger = logging.getLogger("backend.routers.settings")

SCRIPTING_TOGGLES = {
    "enable_lua_scripting": ("comfylab.blocks.script_lua", "LuaScriptBlock", "script/lua"),
    "enable_julia_scripting": ("comfylab.blocks.script_julia", "JuliaScriptBlock", "script/julia"),
    "enable_js_scripting": ("comfylab.blocks.script_js", ["JavaScriptScriptBlock", "TypeScriptScriptBlock"], ["script/javascript", "script/typescript"]),
    "enable_rust_scripting": ("comfylab.blocks.script_rust", "RustScriptBlock", "script/rust"),
    "enable_r_scripting": ("comfylab.blocks.script_r", "RScriptBlock", "script/r"),
    "enable_octave_scripting": ("comfylab.blocks.script_octave", "OctaveScriptBlock", "script/octave"),
    "enable_wolfram_scripting": ("comfylab.blocks.script_wolfram", "WolframScriptBlock", "script/wolfram"),
}

router = APIRouter()

class SettingsPayload(BaseModel):
    custom_block_dirs: List[str]
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

    
    # Selectively synchronize script block registrations to avoid breaking test-only blocks
    for key, (module_path, class_names, type_names) in SCRIPTING_TOGGLES.items():
        classes = class_names if isinstance(class_names, list) else [class_names]
        types = type_names if isinstance(type_names, list) else [type_names]
        
        if updated.get(key, False):
            try:
                mod = importlib.import_module(module_path)
                for cls_name, t_name in zip(classes, types):
                    BLOCK_REGISTRY[t_name] = getattr(mod, cls_name)
            except Exception as e:
                logger.error(
                    f"Failed to dynamically synchronize script block registry for {module_path}: {e}"
                )
        else:
            for t_name in types:
                BLOCK_REGISTRY.pop(t_name, None)
        
    return updated

