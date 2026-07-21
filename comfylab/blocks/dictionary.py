# Copyright (C) 2026 Paulo Felipe Jarschel

import copy
from typing import Any

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, DataIn, DataOut, ExecutionContext

@register_block("dictionary/create")
class DictCreateBlock(BaseBlock):
    """Creates an empty dictionary."""
    icon = "{} "
    display_name = "Create Dictionary"
    description = "Outputs a new, empty dictionary."
    
    inputs_def = []
    outputs_def = [DataOut("Dictionary", type_hint=dict)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Dictionary":
            return {}
        return None

@register_block("dictionary/set")
class DictSetBlock(BaseBlock):
    """Sets a key/value pair in a dictionary."""
    icon = "➕"
    display_name = "Set Key/Value"
    description = "Sets or updates a key/value pair in a dictionary. Returns a new dictionary."
    
    inputs_def = [
        DataIn("Dictionary", type_hint=dict),
        DataIn("Key", type_hint=str, default="my_key", widget="text"),
        DataIn("Value", type_hint=Any)
    ]
    outputs_def = [DataOut("Dictionary", type_hint=dict)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Dictionary":
            d = await context.pull(self.id, "Dictionary")
            k = await context.pull(self.id, "Key")
            v = await context.pull(self.id, "Value")
            
            if not isinstance(d, dict):
                d = {}
            if not isinstance(k, str):
                k = str(k)
                
            new_dict = copy.copy(d)
            new_dict[k] = v
            return new_dict
        return None

@register_block("dictionary/get")
class DictGetBlock(BaseBlock):
    """Gets a value from a dictionary by key."""
    icon = "🔍"
    display_name = "Get Value"
    description = "Retrieves the value for a specific key in a dictionary."
    
    inputs_def = [
        DataIn("Dictionary", type_hint=dict),
        DataIn("Key", type_hint=str, default="my_key", widget="text"),
        DataIn("Default", type_hint=Any, optional=True)
    ]
    outputs_def = [DataOut("Value", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            d = await context.pull(self.id, "Dictionary")
            k = await context.pull(self.id, "Key")
            default_val = await context.pull(self.id, "Default")
            
            if not isinstance(d, dict):
                return default_val
            return d.get(str(k), default_val)
        return None

@register_block("dictionary/keys")
class DictKeysBlock(BaseBlock):
    """Gets a list of all keys in a dictionary."""
    icon = "🔑"
    display_name = "Get Keys"
    description = "Outputs a list of all keys in the dictionary."
    
    inputs_def = [
        DataIn("Dictionary", type_hint=dict)
    ]
    outputs_def = [DataOut("Keys", type_hint=list)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Keys":
            d = await context.pull(self.id, "Dictionary")
            if not isinstance(d, dict):
                return []
            return list(d.keys())
        return None

@register_block("dictionary/values")
class DictValuesBlock(BaseBlock):
    """Gets a list of all values in a dictionary."""
    icon = "📦"
    display_name = "Get Values"
    description = "Outputs a list of all values in the dictionary."
    
    inputs_def = [
        DataIn("Dictionary", type_hint=dict)
    ]
    outputs_def = [DataOut("Values", type_hint=list)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Values":
            d = await context.pull(self.id, "Dictionary")
            if not isinstance(d, dict):
                return []
            return list(d.values())
        return None
