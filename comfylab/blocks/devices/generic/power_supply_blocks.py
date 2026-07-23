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
from comfylab.devices.generic.power_supply import GenericPowerSupply


@register_block("devices/generic/power_supply/connect")
class GenericPowerSupplyConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a SCPI DC Power Supply / Source with safety teardown."""
    icon = "🔋"
    display_name = "Generic Power Supply Connect"
    description = "Opens a VISA session to a SCPI Power Supply. On teardown, turns output OFF."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        drv = GenericPowerSupply(device)
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(drv.set_output, 1, False)
        else:
            await asyncio.to_thread(drv.set_output, 1, False)


@register_block("devices/generic/power_supply/set_channel")
class GenericPowerSupplySetChannelBlock(BaseBlock):
    """Configures output voltage setpoint and current compliance limit on a SCPI DC Power Supply."""
    icon = "⚙️"
    display_name = "Generic Power Supply Set Channel"
    description = "Configures voltage (V) and current limit (A) on a SCPI Power Supply channel."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3]),
        DataIn("Voltage", type_hint=float, default=0.0),
        DataIn("CurrentLimit", type_hint=float, default=1.0, optional=True),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        channel = await context.pull(self.id, "Channel")
        voltage = await context.pull(self.id, "Voltage")
        curr_lim = await context.pull(self.id, "CurrentLimit")
        enable = await context.pull(self.id, "Enable")

        drv = GenericPowerSupply(device)
        async with locked_device(context, device, "Generic Power Supply Config"):
            await asyncio.to_thread(drv.set_channel, int(channel), voltage, curr_lim)
            await asyncio.to_thread(drv.set_output, int(channel), bool(enable))

        return "Out"


@register_block("devices/generic/power_supply/measure")
class GenericPowerSupplyMeasureBlock(BaseBlock):
    """Measures actual output voltage and current from a SCPI DC Power Supply channel."""
    icon = "📊"
    display_name = "Generic Power Supply Measure"
    description = "Queries real-time output voltage (V) and current (A) readings from a Power Supply channel."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Voltage", type_hint=float),
        DataOut("Current", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_v: float = 0.0
        self._last_i: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        channel = await context.pull(self.id, "Channel")

        drv = GenericPowerSupply(device)
        async with locked_device(context, device, "Generic Power Supply Measure"):
            self._last_v = await asyncio.to_thread(drv.measure_voltage, int(channel))
            self._last_i = await asyncio.to_thread(drv.measure_current, int(channel))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Voltage":
            return self._last_v
        elif pin_name == "Current":
            return self._last_i
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
