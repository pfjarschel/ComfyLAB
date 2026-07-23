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
from comfylab.devices.agilent.hp34401a import HP34401A


@register_block("devices/agilent/hp34401a/connect")
class HP34401AConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to an HP / Agilent 34401A 6½ Digit Multimeter."""
    icon = "🎛️"
    display_name = "HP 34401A DMM Connect"
    description = "Opens a VISA session to an HP / Agilent 34401A 6½ Digit Multimeter."


@register_block("devices/agilent/hp34401a/measure")
class HP34401AMeasureBlock(BaseBlock):
    """Configures measurement mode and triggers a reading on an HP 34401A DMM."""
    icon = "🔢"
    display_name = "HP 34401A Measure"
    description = "Configures mode (VOLT:DC, CURR:DC, RES, etc.) and triggers reading on an HP 34401A DMM."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Mode", type_hint=str, default="VOLT:DC", widget="dropdown", options=["VOLT:DC", "VOLT:AC", "CURR:DC", "CURR:AC", "RES", "FRES"]),
        DataIn("Range", type_hint=float, optional=True),
        DataIn("NPLC", type_hint=float, default=1.0, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Value", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_val: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        mode = await context.pull(self.id, "Mode")
        rng = await context.pull(self.id, "Range")
        nplc = await context.pull(self.id, "NPLC")

        drv = HP34401A(device)
        async with locked_device(context, device, "HP 34401A Measure"):
            await asyncio.to_thread(drv.configure, mode, rng, None, nplc)
            self._last_val = await asyncio.to_thread(drv.read_measurement)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return self._last_val
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
