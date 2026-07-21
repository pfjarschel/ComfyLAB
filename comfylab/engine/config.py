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
import json
from pathlib import Path
import logging

logger = logging.getLogger("comfylab.engine.config")

DEFAULT_CONFIG = {
    "custom_block_dirs": [],
    "last_workspace": "",
    "script_timeout": 30.0,
    "visa_backend": "",
    "enable_lua_scripting": False,
    "enable_julia_scripting": False,
    "enable_js_scripting": False,
    "enable_rust_scripting": False,
    "enable_r_scripting": False,
    "enable_octave_scripting": False,
    "enable_wolfram_scripting": False,
    "external_python_path": "",
    "creator_identity": "",
    "trusted_origins": [],
    "custom_users": {}
}

def get_comfylab_base_dir() -> Path:
    """Returns the base ~/.comfylab path and ensures it exists."""
    base_dir = Path.home() / ".comfylab"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def get_global_user_blocks_dir() -> Path:
    """Returns the base user_blocks directory (~/.comfylab/user_blocks) and ensures it exists."""
    blocks_dir = get_comfylab_base_dir() / "user_blocks"
    blocks_dir.mkdir(parents=True, exist_ok=True)
    return blocks_dir


def get_global_user_clusters_dir() -> Path:
    """Returns the base user_clusters directory (~/.comfylab/user_clusters) and ensures it exists."""
    clusters_dir = get_comfylab_base_dir() / "user_clusters"
    clusters_dir.mkdir(parents=True, exist_ok=True)
    return clusters_dir

def get_config_file_path() -> Path:
    """Returns the path to ~/.comfylab/config.json."""
    return get_comfylab_base_dir() / "config.json"

def get_config() -> dict:
    """Loads and returns the configuration dictionary, merging defaults for any missing keys."""
    path = get_config_file_path()
    config = DEFAULT_CONFIG.copy()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    # Merge loaded keys on top of default ones
                    config.update(loaded)
        except Exception as e:
            logger.error(f"Error loading config file {path}: {e}. Using defaults.")
    else:
        # Save defaults if no file exists
        save_config(config)
    return config

def save_config(config: dict):
    """Saves the configuration dictionary to ~/.comfylab/config.json."""
    path = get_config_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving config file {path}: {e}")

def update_config(updates: dict) -> dict:
    """Updates specific keys in the configuration file and returns the updated config."""
    config = get_config()
    config.update(updates)
    save_config(config)
    return config
