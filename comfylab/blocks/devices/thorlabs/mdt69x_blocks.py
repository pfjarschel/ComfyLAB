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
from comfylab.devices.thorlabs.mdt69x import ThorlabsMDT69X


@register_block("devices/thorlabs/mdt69x/connect")
class ThorlabsMDT69XConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Thorlabs MDT69X 3-Axis Piezo Controller."""
    icon = "⚡"
    display_name = "Thorlabs MDT69X Connect"
    description = "Opens a VISA session to a Thorlabs MDT693B/MDT694B Piezo Controller."


@register_block("devices/thorlabs/mdt69x/set_voltage")
class ThorlabsMDT69XSetVoltageBlock(BaseBlock):
    """Sets output piezo voltage (0-100V) for X, Y, or Z axis on a Thorlabs MDT69X controller."""
    icon = "⚡"
    display_name = "Thorlabs MDT69X Set Voltage"
    description = "Sets piezo voltage output (V) for a channel axis (X/Y/Z) on a Thorlabs MDT69X."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Axis", type_hint=str, default="X", widget="dropdown", options=["X", "Y", "Z"]),
        DataIn("Voltage", type_hint=float, default=0.0)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("ActualVoltage", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_v: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        axis = await context.pull(self.id, "Axis")
        voltage = await context.pull(self.id, "Voltage")

        drv = ThorlabsMDT69X(device)
        async with locked_device(context, device, "Thorlabs MDT69X Set Voltage"):
            await asyncio.to_thread(drv.set_voltage, axis, voltage)
            self._last_v = await asyncio.to_thread(drv.get_voltage, axis)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "ActualVoltage":
            return self._last_v
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
