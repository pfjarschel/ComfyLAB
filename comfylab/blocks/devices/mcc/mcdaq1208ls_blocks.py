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
from comfylab.devices.mcc.mcdaq1208ls import MCCDAQ1208LS


@register_block("devices/mcc/mcdaq1208ls/connect")
class MCCDAQ1208LSConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Measurement Computing (MCC) USB-1208LS DAQ."""
    icon = "⚡"
    display_name = "MCC USB-1208LS Connect"
    description = "Opens a VISA session to an MCC USB-1208LS DAQ module."


@register_block("devices/mcc/mcdaq1208ls/analog_read")
class MCCDAQ1208LSAnalogReadBlock(BaseBlock):
    """Reads analog voltage input (V) from an MCC USB-1208LS channel."""
    icon = "📥"
    display_name = "MCC USB-1208LS Read Analog"
    description = "Queries real-time analog input voltage (V) on an MCC USB-1208LS channel (0-7)."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=0, widget="dropdown", options=[0, 1, 2, 3, 4, 5, 6, 7])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Voltage", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_v: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        chan = await context.pull(self.id, "Channel")

        drv = MCCDAQ1208LS(device)
        async with locked_device(context, device, "MCC DAQ Read"):
            self._last_v = await asyncio.to_thread(drv.read_analog_channel, int(chan))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Voltage":
            return self._last_v
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
