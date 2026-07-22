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
from typing import Any, Optional, Dict
from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, ExecutionContext

logger = logging.getLogger("comfylab.blocks.outputs_basic")


@register_block("outputs/basic/print")
class PrintBlock(BaseBlock):
    """Prints a pulled value to standard output and continues execution."""
    icon = " >_ "
    display_name = "Print"
    description = "Prints a pulled value to standard output and continues execution."
    
    inputs_def = [
        ExecIn("In"),
        DataIn("Value", type_hint=Any, default="", widget="text")
    ]
    outputs_def = [ExecOut("Out")]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self.last_printed: Any = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        val = await context.pull(self.id, "Value")
        self.last_printed = val
        logger.info(f"[ComfyLAB Print '{self.id}'] >>> {val}")
        print(f"[ComfyLAB Print '{self.id}'] >>> {val}")
        return "Out"

    async def clear_data(self) -> None:
        self.last_printed = None


@register_block("outputs/basic/display")
class DisplayBlock(BaseBlock):
    """Displays a pulled value on the block itself by broadcasting telemetry."""
    icon = "🖥️"
    display_name = "Display Value"
    description = "Displays the incoming value in the UI."
    ui_behavior = {"custom_widget": "display_area"}
    
    inputs_def = [
        ExecIn("In"),
        DataIn("Value", type_hint=Any, default="", widget="any")
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        val = await context.pull(self.id, "Value")
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            display_val = val
        else:
            display_val = str(val)
        await context.send_telemetry(self.id, {"value": display_val})
        return "Out"


@register_block("outputs/basic/led_indicator")
class LEDBlock(BaseBlock):
    """Circular passthrough block displaying state (green/red) dynamically."""
    icon = "🔴"
    display_name = "LED Status"
    description = "Circular passthrough status indicator showing green (True) or red (False) dynamically."
    default_width = 40
    default_height = 40
    is_passthrough = True

    inputs_def = [
        ExecIn("In"),
        DataIn("State", type_hint=bool, default=False)
    ]
    outputs_def = [
        ExecOut("Out")
    ]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "In":
            state = bool(await context.pull(self.id, "State"))
            await context.send_telemetry(self.id, {"state": state})
            return "Out"
        return None
