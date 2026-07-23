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
from comfylab.devices.thorlabs.pm100d import ThorlabsPM100D


@register_block("devices/thorlabs/pm100d/connect")
class ThorlabsPM100DConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Thorlabs PM100D/PM100A/PM400 Optical Power Meter."""
    icon = "💡"
    display_name = "Thorlabs PM100D Connect"
    description = "Opens a VISA session to a Thorlabs Optical Power Meter."


@register_block("devices/thorlabs/pm100d/config")
class ThorlabsPM100DConfigBlock(BaseBlock):
    """Configures calibration wavelength (nm), measurement unit (W/dBm), and averaging count."""
    icon = "⚙️"
    display_name = "Thorlabs PM100D Config"
    description = "Configures operating wavelength (nm), display unit (W or dBm), and averaging count on a Thorlabs PM100D."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Wavelength", type_hint=float, default=1550.0),
        DataIn("Unit", type_hint=str, default="W", widget="dropdown", options=["W", "DBM"]),
        DataIn("Averaging", type_hint=int, default=10, optional=True)
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
        wl_nm = await context.pull(self.id, "Wavelength")
        unit = await context.pull(self.id, "Unit")
        avg = await context.pull(self.id, "Averaging")

        drv = ThorlabsPM100D(device)
        async with locked_device(context, device, "Thorlabs PM100D Config"):
            if wl_nm is not None:
                await asyncio.to_thread(drv.set_wavelength, wl_nm)
            if unit is not None:
                await asyncio.to_thread(drv.set_unit, unit)
            if avg is not None:
                await asyncio.to_thread(drv.set_averaging, int(avg))

        return "Out"


@register_block("devices/thorlabs/pm100d/read")
class ThorlabsPM100DReadBlock(BaseBlock):
    """Triggers and reads single optical power measurement from a Thorlabs PM100D."""
    icon = "📥"
    display_name = "Thorlabs PM100D Read Power"
    description = "Triggers an optical power reading from a Thorlabs PM100D power meter."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Power", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_power: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")

        drv = ThorlabsPM100D(device)
        async with locked_device(context, device, "Thorlabs PM100D Read"):
            self._last_power = await asyncio.to_thread(drv.read_power)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Power":
            return self._last_power
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
