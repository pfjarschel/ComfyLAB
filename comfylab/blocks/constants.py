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

from typing import Any
from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, DataOut, ExecutionContext


@register_block("constants/number")
class NumberBlock(BaseBlock):
    """Outputs a static numerical value defined in properties."""
    icon = "#️⃣"
    display_name = "Number"
    description = "Outputs a constant numerical value."
    default_width = 160
    ui_behavior = {"custom_widget": "constant_number"}
    
    outputs_def = [DataOut("Value", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return float(self.properties.get("value", 0.0))
        return None


@register_block("constants/boolean")
class BooleanBlock(BaseBlock):
    """Outputs a static boolean value (e.g. from an on/off toggle button)."""
    icon = "🔘"
    display_name = "Boolean"
    description = "Outputs a constant boolean value (True/False)."
    default_width = 160
    ui_behavior = {"custom_widget": "constant_boolean"}
    
    outputs_def = [DataOut("Value", type_hint=bool)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return bool(self.properties.get("value", False))
        return None


@register_block("constants/string")
class StringBlock(BaseBlock):
    """Outputs a static string value defined in properties."""
    icon = "🔤"
    display_name = "String"
    description = "Outputs a constant string."
    default_width = 160
    ui_behavior = {"custom_widget": "constant_string"}
    
    outputs_def = [DataOut("Value", type_hint=str)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return str(self.properties.get("value", ""))
        return None
