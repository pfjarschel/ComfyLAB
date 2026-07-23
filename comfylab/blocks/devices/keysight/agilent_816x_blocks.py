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
from comfylab.devices.keysight.agilent_816x import Agilent816x


@register_block("devices/keysight/agilent_816x/connect")
class Agilent816xConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to an Agilent / Keysight 816x Lightwave Mainframe with safety teardown."""
    icon = "💡"
    display_name = "Keysight 816x Connect"
    description = "Opens a VISA session to a Keysight 816x Lightwave Mainframe. On teardown, turns laser output OFF."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        drv = Agilent816x(device)
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(drv.set_laser_state, 1, False)
        else:
            await asyncio.to_thread(drv.set_laser_state, 1, False)


@register_block("devices/keysight/agilent_816x/laser_config")
class Agilent816xLaserConfigBlock(BaseBlock):
    """Configures wavelength (nm), power (dBm), and state for a tunable laser module on a Keysight 816x."""
    icon = "⚙️"
    display_name = "Keysight 816x Laser Config"
    description = "Configures wavelength (nm), output power (dBm), and laser state on a Keysight 816x slot."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Slot", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Wavelength", type_hint=float, default=1550.0),
        DataIn("Power", type_hint=float, default=0.0),
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
        slot = await context.pull(self.id, "Slot")
        wl_nm = await context.pull(self.id, "Wavelength")
        power_dbm = await context.pull(self.id, "Power")
        enable = await context.pull(self.id, "Enable")

        drv = Agilent816x(device)
        async with locked_device(context, device, "Keysight 816x Laser Config"):
            if wl_nm is not None:
                await asyncio.to_thread(drv.set_laser_wavelength, int(slot), wl_nm)
            if power_dbm is not None:
                await asyncio.to_thread(drv.set_laser_power, int(slot), power_dbm)
            await asyncio.to_thread(drv.set_laser_state, int(slot), bool(enable))

        return "Out"


@register_block("devices/keysight/agilent_816x/read_power")
class Agilent816xReadPowerBlock(BaseBlock):
    """Reads optical power (W) from a power sensor module on a Keysight 816x mainframe."""
    icon = "📥"
    display_name = "Keysight 816x Read Power"
    description = "Queries optical power from a power sensor module slot on a Keysight 816x mainframe."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Slot", type_hint=int, default=2, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Wavelength", type_hint=float, default=1550.0, optional=True)
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
        slot = await context.pull(self.id, "Slot")
        wl_nm = await context.pull(self.id, "Wavelength")

        drv = Agilent816x(device)
        async with locked_device(context, device, "Keysight 816x Read Power"):
            if wl_nm is not None:
                await asyncio.to_thread(drv.set_sensor_wavelength, int(slot), wl_nm)
            self._last_power = await asyncio.to_thread(drv.read_sensor_power, int(slot))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Power":
            return self._last_power
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
