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
from comfylab.devices.keithley.k2400 import Keithley2400


@register_block("devices/keithley/k2400/connect")
class Keithley2400ConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Keithley 2400/2450 Series SMU with safety teardown."""
    icon = "⚡"
    display_name = "Keithley 2400 SMU Connect"
    description = "Opens a VISA session to a Keithley 2400/2450 SMU. On teardown, turns output OFF."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        drv = Keithley2400(device)
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(drv.set_output, False)
        else:
            await asyncio.to_thread(drv.set_output, False)


@register_block("devices/keithley/k2400/source_voltage")
class Keithley2400SourceVoltageBlock(BaseBlock):
    """Configures Source Voltage / Measure Current mode on a Keithley 2400 SMU."""
    icon = "⚙️"
    display_name = "Keithley 2400 Source Voltage"
    description = "Configures voltage setpoint (V), current compliance limit (A), and enables output on a Keithley SMU."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Voltage", type_hint=float, default=0.0),
        DataIn("CurrentLimit", type_hint=float, default=0.1),
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
        voltage = await context.pull(self.id, "Voltage")
        curr_lim = await context.pull(self.id, "CurrentLimit")
        enable = await context.pull(self.id, "Enable")

        drv = Keithley2400(device)
        async with locked_device(context, device, "Keithley 2400 Source Voltage"):
            await asyncio.to_thread(drv.configure_source_voltage, voltage, curr_lim)
            await asyncio.to_thread(drv.set_output, bool(enable))

        return "Out"


@register_block("devices/keithley/k2400/read")
class Keithley2400ReadBlock(BaseBlock):
    """Triggers measurement reading (Voltage V and Current A) from a Keithley 2400 SMU."""
    icon = "📊"
    display_name = "Keithley 2400 Measure V & I"
    description = "Triggers real-time output voltage (V) and current (A) measurement on a Keithley 2400 SMU."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any)
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

        drv = Keithley2400(device)
        async with locked_device(context, device, "Keithley 2400 Read"):
            v, i = await asyncio.to_thread(drv.read_measurement)
            self._last_v = v
            self._last_i = i

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Voltage":
            return self._last_v
        elif pin_name == "Current":
            return self._last_i
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
