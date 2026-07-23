# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
from typing import Any, Dict, Optional

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.blocks.devices.base import BaseDeviceConnectBlock, locked_device
from comfylab.devices.thorlabs.lts200 import ThorlabsLTS200


@register_block("devices/thorlabs/lts200/connect")
class ThorlabsLTS200ConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Thorlabs LTS200/LTS300 Linear Stage."""
    icon = "🎯"
    display_name = "Thorlabs LTS200 Connect"
    description = "Opens a VISA session to a Thorlabs LTS200 Linear Stage."


@register_block("devices/thorlabs/lts200/move")
class ThorlabsLTS200MoveBlock(BaseBlock):
    """Moves a Thorlabs LTS200 stage to an absolute position (mm) or relative distance."""
    icon = "↔️"
    display_name = "Thorlabs LTS200 Move"
    description = "Moves a Thorlabs LTS200 stage to a specified position (mm)."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Position_mm", type_hint=float, default=0.0),
        DataIn("Mode", type_hint=str, default="Absolute", widget="dropdown", options=["Absolute", "Relative"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("CurrentPosition", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_pos: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        val_mm = await context.pull(self.id, "Position_mm")
        mode = await context.pull(self.id, "Mode")

        drv = ThorlabsLTS200(device)
        async with locked_device(context, device, "Thorlabs LTS200 Move"):
            if mode == "Absolute":
                await asyncio.to_thread(drv.move_absolute, val_mm)
            else:
                await asyncio.to_thread(drv.move_relative, val_mm)
            
            self._last_pos = await asyncio.to_thread(drv.get_position)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "CurrentPosition":
            return self._last_pos
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
