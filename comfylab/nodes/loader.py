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
import importlib
import importlib.util
import sys
from pathlib import Path
import logging

logger = logging.getLogger("comfylab.nodes.loader")

def load_module_from_filepath(filepath: str, module_name: str = None):
    """Dynamically imports a Python module from an absolute filesystem path."""
    path_obj = Path(filepath).resolve()
    if not module_name:
        # Generate a unique module name based on filepath hash/name
        # to avoid name collision in sys.modules
        module_name = f"comfylab_dynamic_{path_obj.stem}_{hash(str(path_obj)) & 0xffffffff}"
    
    spec = importlib.util.spec_from_file_location(module_name, str(path_obj))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for module {module_name} at {filepath}")
        
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        if module_name in sys.modules:
            del sys.modules[module_name]
        raise e

def load_nodes_from_directory(directory_path: str):
    """Recursively scans a directory for .py files and loads them dynamically."""
    dir_path = Path(directory_path).resolve()
    if not dir_path.exists() or not dir_path.is_dir():
        return

    for root, dirs, files in os.walk(dir_path):
        if ".temp" in dirs:
            dirs.remove(".temp")
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                full_path = Path(root) / file
                try:
                    load_module_from_filepath(str(full_path))
                    logger.info(f"Dynamically loaded user node module: {full_path}")
                except Exception as e:
                    # Fault-tolerance: log error, but do not raise, so other nodes continue loading!
                    logger.error(f"Failed to dynamically load user node module at {full_path}: {e}")

def load_all_nodes():
    """
    Recursively scans and imports node files from multiple discovery paths:
    1. Core nodes (comfylab/nodes/)
    2. Global user nodes (~/.comfylab/user_nodes/)
    3. Custom directories from config settings
    4. Current workspace nodes (<workspace>/nodes/)
    """
    # 1. Load Core Nodes
    from comfylab.engine.config import get_config
    config = get_config()
    if getattr(sys, 'frozen', False):
        import comfylab.nodes
        package_path = os.path.join(os.path.dirname(sys.executable), "comfylab", "nodes")
        if hasattr(comfylab.nodes, '__path__'):
            comfylab.nodes.__path__ = list(comfylab.nodes.__path__)
            if package_path not in comfylab.nodes.__path__:
                comfylab.nodes.__path__.insert(0, package_path)
    else:
        package_path = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, files in os.walk(package_path):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                # Determine absolute import path relative to the package root
                rel_path = os.path.relpath(os.path.join(root, file), package_path)
                # Normalize separators (e.g. backslashes on Windows) to forward slash
                normalized_rel_path = rel_path.replace(os.sep, "/")
                module_parts = normalized_rel_path[:-3].split("/")
                
                # Exclude base.py, loader.py, and macro.py in the root directory
                if len(module_parts) == 1:
                    module_name_root = module_parts[0]
                    if module_name_root in ["base", "loader", "macro"]:
                        continue
                    if module_name_root.startswith("script_"):
                        lang = module_name_root[7:]
                        config_key = f"enable_{lang}_scripting"
                        if config_key in config and not config.get(config_key, False):
                            continue
                
                module_name = "comfylab.nodes." + ".".join(module_parts)
                try:
                    if module_name in sys.modules:
                        importlib.reload(sys.modules[module_name])
                    else:
                        importlib.import_module(module_name)
                    logger.info(f"Auto-discovered and loaded node module: {module_name}")
                except Exception as e:
                    logger.error(f"Failed to import auto-discovered module {module_name}: {e}")
                    # Keep it raise for core nodes because they shouldn't fail
                    raise e

    # 2. Load Global User Nodes (~/.comfylab/user_nodes)
    try:
        from comfylab.engine.config import get_global_user_nodes_dir
        global_user_dir = get_global_user_nodes_dir()
        load_nodes_from_directory(str(global_user_dir))
    except Exception as e:
        logger.error(f"Error loading global user nodes: {e}")

    # 3. Load Custom Directories from Config
    try:
        from comfylab.engine.config import get_config
        config = get_config()
        custom_dirs = config.get("custom_node_dirs", [])
        for custom_dir in custom_dirs:
            load_nodes_from_directory(custom_dir)
    except Exception as e:
        logger.error(f"Error loading custom directory nodes: {e}")

    # 4. Load Active Workspace Nodes (<workspace>/nodes)
    try:
        from backend.workspace import get_workspace_path
        workspace_path = get_workspace_path()
        if workspace_path:
            workspace_nodes_dir = Path(workspace_path) / "nodes"
            load_nodes_from_directory(str(workspace_nodes_dir))
    except Exception as e:
        logger.error(f"Error loading workspace nodes: {e}")

    # (macro loading is called separately after load_all_nodes returns)


def load_all_macros():
    try:
        from comfylab.engine.config import get_global_user_macros_dir
        from comfylab.nodes.macro import load_macros_from_directory
        global_macro_dir = get_global_user_macros_dir()
        count = load_macros_from_directory(str(global_macro_dir))
        if count > 0:
            logger.info(f"Loaded {count} macros from global user macros directory.")
    except Exception as e:
        logger.error(f"Error loading global user macros: {e}")

    try:
        from comfylab.nodes.macro import load_macros_from_directory
        from backend.workspace import get_workspace_path
        workspace_path = get_workspace_path()
        if workspace_path:
            workspace_macros_dir = Path(workspace_path) / "macros"
            workspace_macros_dir.mkdir(parents=True, exist_ok=True)
            count = load_macros_from_directory(str(workspace_macros_dir))
            if count > 0:
                logger.info(f"Loaded {count} macros from workspace macros directory.")
    except Exception as e:
        logger.error(f"Error loading workspace macros: {e}")


def reload_registry():
    """Clears and fully reloads all nodes and macros in the global registry."""
    from comfylab.engine.registry import NODE_REGISTRY, load_all_macros_deferred, invalidate_schema_cache
    from comfylab.engine.security import clear_signature_cache
    NODE_REGISTRY.clear()
    invalidate_schema_cache()
    clear_signature_cache()
    load_all_nodes()
    load_all_macros_deferred(force=True)

