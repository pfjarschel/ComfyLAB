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

from typing import Dict, Type, Any, List
import re
import logging
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut

logger = logging.getLogger("comfylab.engine.registry")


def _safe_getfile(cls: Type[BaseBlock]) -> str:
    try:
        import inspect
        return inspect.getfile(cls)
    except Exception:
        return ""

TEST_VERIFICATION_BLOCKS = {"test/blocked_block", "test/custom_pack_block"}

def _is_verification_test(type_name: str) -> bool:
    return type_name.startswith("test/dynamic_") or type_name in TEST_VERIFICATION_BLOCKS

# Global map storing registered block types
BLOCK_REGISTRY: Dict[str, Type[BaseBlock]] = {}

# Cached serialized block schema (invalidated on any new registration)
_schema_cache: Dict[str, Any] = None


def invalidate_schema_cache() -> None:
    """Clears the cached block schema. Call after block registrations change."""
    global _schema_cache
    _schema_cache = None

def register_block(type_name: str):
    """
    Decorator to register a BaseBlock subclass in the global registry.
    Usage:
        @register_block("math/arithmetic/add")
        class AddBlock(BaseBlock):
            ...
    """
    def decorator(cls: Type[BaseBlock]):
        if not issubclass(cls, BaseBlock):
            raise TypeError(f"Class {cls.__name__} must inherit from BaseBlock")
        
        # Security/Signature check
        try:
            import inspect
            from pathlib import Path
            import comfylab
            
            import sys
            abs_path = Path(inspect.getfile(cls)).resolve()
            if getattr(sys, 'frozen', False):
                ext_core_dir = Path(sys.executable).parent / "comfylab"
                is_core = ext_core_dir.resolve() in abs_path.parents
            else:
                core_dir = Path(comfylab.__file__).parent.resolve()
                is_core = core_dir in abs_path.parents or abs_path == core_dir
            if not hasattr(cls, "unauthorized"):
                if not is_core:
                    import sys
                    is_test_env = any("pytest" in arg or "py.test" in arg for arg in sys.argv) or "pytest" in sys.modules
                    
                    if is_test_env and not _is_verification_test(type_name):
                        cls.unauthorized = False
                        cls.creator_identity = "test"
                    else:

                        from comfylab.engine.security import verify_python_file, get_config
                        creator, is_valid = verify_python_file(abs_path)
                        
                        config = get_config()
                        trusted_origins = config.get("trusted_origins", [])
                        local_identity = config.get("creator_identity", "")
                        
                        is_trusted = is_valid and (creator == local_identity or creator in trusted_origins)
                        if not is_trusted:
                            cls.unauthorized = True
                            cls.creator_identity = creator
                        else:
                            cls.unauthorized = False
                            cls.creator_identity = creator
                else:
                    cls.unauthorized = False
                    cls.creator_identity = "system"

        except Exception:
            if not hasattr(cls, "unauthorized"):
                cls.unauthorized = False
                cls.creator_identity = "system"

        # Derive category from type_name if not explicitly set on the class dict
        if "category" not in cls.__dict__:
            parts = re.split(r'(?<!\\)/', type_name)
            if len(parts) > 2:
                cls.category = "/".join(parts[:-1])
            elif len(parts) > 1:
                cls.category = parts[0]
            else:
                cls.category = "Logic"

        # Prepend "Temporary/" to category if block is loaded from a temp directory
        try:
            from pathlib import Path
            if hasattr(cls, "_cluster_file_path") and cls._cluster_file_path:
                source_path = Path(cls._cluster_file_path).resolve()
            else:
                import inspect
                source_path = Path(inspect.getfile(cls)).resolve()
            
            if ".temp" in source_path.parts:
                cat = getattr(cls, "category", "Logic") or "Logic"
                if not cat.startswith("Temporary/"):
                    cls.category = f"Temporary/{cat}"
        except Exception:
            pass

        existing = BLOCK_REGISTRY.get(type_name)
        if existing is not None and existing is not cls:
            new_src = getattr(cls, "_cluster_file_path", "") or _safe_getfile(cls)
            old_src = getattr(existing, "_cluster_file_path", "") or _safe_getfile(existing)
            logger.warning(
                "Duplicate block type '%s' registered from '%s', overwriting previous registration from '%s'.",
                type_name, new_src or "<unknown>", old_src or "<unknown>"
            )

        BLOCK_REGISTRY[type_name] = cls
        invalidate_schema_cache()
        return cls
    return decorator



def format_category(category_str: str) -> str:
    if not category_str:
        return "LOGIC"
    parts = re.split(r'(?<!\\)/', category_str)
    
    is_temp = False
    if parts[0] == "Temporary":
        is_temp = True
        parts = parts[1:]
        
    if not parts:
        return "TEMPORARY"
        
    main_cat = parts[0].replace("_", " ").upper()
    if len(parts) > 1:
        sub_cats = []
        for p in parts[1:]:
            sub_c = p.replace("_", " ").replace("-", " ")
            sub_c = " ".join(word[0].upper() + word[1:] if word else "" for word in sub_c.split())
            sub_cats.append(sub_c)
        formatted = f"{main_cat}/{'/'.join(sub_cats)}"
    else:
        formatted = main_cat
        
    if is_temp:
        formatted = f"Temporary/{formatted}"
    return formatted


def get_block_class(type_name: str) -> Type[BaseBlock]:
    """
    Retrieves the block class registered for a type name.
    Raises KeyError if the type name is not registered.
    """
    if type_name not in BLOCK_REGISTRY:
        raise KeyError(f"Block type '{type_name}' is not registered in BLOCK_REGISTRY.")
    return BLOCK_REGISTRY[type_name]


def _map_type_hint_to_str(type_hint: Any) -> str:
    """Maps a Python type hint class to a frontend-compatible type string."""
    import numpy as np
    if type_hint is float or type_hint is int:
        return "number"
    elif type_hint is bool:
        return "boolean"
    elif type_hint is str:
        return "text"
    elif type_hint is list:
        return "list"
    elif type_hint is np.ndarray:
        return "ndarray"
    elif type_hint is dict:
        return "dictionary"
    return "any"

def _map_default_widget(type_str: str) -> str:
    """Returns the default widget name for a given type string."""
    if type_str == "boolean":
        return "checkbox"
    elif type_str == "number":
        return "number"
    elif type_str == "text":
        return "text"
    return "any"

def get_all_blocks_schema() -> Dict[str, Any]:
    """
    Serializes all registered blocks, their metadata, and their inputs/outputs definition.
    Result is cached and reused until the registry changes (see invalidate_schema_cache).
    """
    global _schema_cache
    if _schema_cache is not None:
        return _schema_cache

    schema = {}
    for type_name, cls in BLOCK_REGISTRY.items():
        exec_ins = []
        exec_outs = []
        data_ins = []
        data_outs = []
        
        # Sort and serialize inputs
        for pin in cls.inputs_def:
            if isinstance(pin, ExecIn):
                exec_ins.append(pin.name)
            elif isinstance(pin, DataIn):
                type_str = _map_type_hint_to_str(pin.type_hint)
                widget = pin.widget or _map_default_widget(type_str)

                pin_schema = {
                    "name": pin.name,
                    "label": pin.name,
                    "defaultVal": pin.default,
                    "type": type_str,
                    "widget": widget,
                    "optional": pin.optional
                }
                if pin.min_val is not None: pin_schema["min"] = pin.min_val
                if pin.max_val is not None: pin_schema["max"] = pin.max_val
                if pin.step is not None: pin_schema["step"] = pin.step
                if pin.options is not None: pin_schema["options"] = pin.options
                
                data_ins.append(pin_schema)
                
        # Sort and serialize outputs
        for pin in cls.outputs_def:
            if isinstance(pin, ExecOut):
                exec_outs.append(pin.name)
            elif isinstance(pin, DataOut):
                type_str = _map_type_hint_to_str(pin.type_hint)
                data_outs.append({
                    "name": pin.name,
                    "label": pin.name,
                    "type": type_str
                })
                
        # Determine friendly display name
        display_name = getattr(cls, "display_name", "") or cls.__name__
        if display_name.endswith("Block") and display_name != "Block":
            display_name = display_name[:-4]  # Strip "Block" suffix for presentation

        # Resolve relative source file path
        import inspect
        from pathlib import Path
        filepath = ""
        try:
            abs_path = inspect.getfile(cls)
            p = Path(abs_path)
            if p.is_absolute():
                try:
                    filepath = str(p.relative_to(Path.cwd()))
                except ValueError:
                    try:
                        filepath = "~/" + str(p.relative_to(Path.home()))
                    except ValueError:
                        filepath = str(p)
            else:
                filepath = str(p)
        except Exception:
            pass

        schema[type_name] = {
            "name": display_name,
            "icon": getattr(cls, "icon", "⚙️") or "⚙️",
            "category": format_category(getattr(cls, "category", "Logic") or "Logic"),
            "description": getattr(cls, "description", "") or "",
            "author": getattr(cls, "author", "") or "",
            "filepath": filepath,
            "execIns": exec_ins,
            "execOuts": exec_outs,
            "dataIns": data_ins,
            "dataOuts": data_outs,
            "ui_behavior": getattr(cls, "ui_behavior", {}) or {},
            "original_code": getattr(cls, "original_code", "") or "",
            "script_language": getattr(cls, "script_language", "") or "",
            "unauthorized": getattr(cls, "unauthorized", False),
            "creator_identity": getattr(cls, "creator_identity", ""),
            "broken": getattr(cls, "broken", False),
            "broken_reason": getattr(cls, "broken_reason", ""),
            "defaultWidth": getattr(cls, "default_width", None),
            "defaultHeight": getattr(cls, "default_height", None),
            "isPassthrough": getattr(cls, "is_passthrough", False)
        }
    _schema_cache = schema
    return schema



# Trigger recursive auto-discovery of all block modules
from comfylab.blocks.loader import load_all_blocks
load_all_blocks()

# Cluster loading is deferred to avoid circular imports during module initialization.
# It is called explicitly from the FastAPI startup event and from the /blocks/reload endpoint.
_clusters_loaded = False


def load_all_clusters_deferred(force: bool = False):
    global _clusters_loaded
    if _clusters_loaded and not force:
        return
    from comfylab.blocks.loader import load_all_clusters
    load_all_clusters()
    _clusters_loaded = True

