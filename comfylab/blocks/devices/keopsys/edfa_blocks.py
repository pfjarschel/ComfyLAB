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
from comfylab.devices.keopsys.edfa import KeopsysEDFA


@register_block("devices/keopsys/edfa/connect")
class KeopsysEDFAConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Keopsys EDFA with safety teardown (pump off)."""
    icon = "💡"
    display_name = "Keopsys EDFA Connect"
    description = "Opens a VISA session to a Keopsys EDFA. On teardown, turns pump diode OFF."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        drv = KeopsysEDFA(device)
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(drv.set_pump_state, False)
        else:
            await asyncio.to_thread(drv.set_pump_state, False)


@register_block("devices/keopsys/edfa/config")
class KeopsysEDFAConfigBlock(BaseBlock):
    """Configures control mode (ACC/APC), current (mA), power (mW), and pump state on a Keopsys EDFA."""
    icon = "⚙️"
    display_name = "Keopsys EDFA Config"
    description = "Configures operating mode (ACC/APC), setpoint (current/power), and pump state on a Keopsys EDFA."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Mode", type_hint=str, default="ACC", widget="dropdown", options=["ACC", "APC"]),
        DataIn("Current_mA", type_hint=float, default=100.0, optional=True),
        DataIn("Power_mW", type_hint=float, default=10.0, optional=True),
        DataIn("EnablePump", type_hint=bool, default=True, widget="checkbox")
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
        mode = await context.pull(self.id, "Mode")
        curr_ma = await context.pull(self.id, "Current_mA")
        pwr_mw = await context.pull(self.id, "Power_mW")
        enable = await context.pull(self.id, "EnablePump")

        drv = KeopsysEDFA(device)
        async with locked_device(context, device, "Keopsys EDFA Config"):
            await asyncio.to_thread(drv.set_pump_state, bool(enable))
            await asyncio.to_thread(drv.set_control_mode, mode)
            if mode == "ACC" and curr_ma is not None:
                await asyncio.to_thread(drv.set_current, curr_ma)
            elif mode == "APC" and pwr_mw is not None:
                await asyncio.to_thread(drv.set_power, pwr_mw)

        return "Out"
