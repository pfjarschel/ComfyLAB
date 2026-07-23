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
from comfylab.devices.bk_precision.bk4052 import BK4052


@register_block("devices/bk_precision/bk4052/connect")
class BK4052ConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a BK Precision 4052 function generator with safety teardown."""
    icon = "⚡"
    display_name = "BK Precision 4052 Connect"
    description = "Opens a VISA session to a BK Precision 4052 function generator. On teardown, disables output."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        drv = BK4052(device)
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(drv.set_output, 1, False)
                await asyncio.to_thread(drv.set_output, 2, False)
        else:
            await asyncio.to_thread(drv.set_output, 1, False)
            await asyncio.to_thread(drv.set_output, 2, False)


@register_block("devices/bk_precision/bk4052/config_wave")
class BK4052ConfigWaveBlock(BaseBlock):
    """Configures comprehensive output waveform parameters for a channel on a BK Precision 4052."""
    icon = "🌊"
    display_name = "BK Precision 4052 Config Wave"
    description = "Configures shape, frequency, amplitude, offset, phase, duty cycle, and symmetry on a BK Precision 4052."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2]),
        DataIn("Shape", type_hint=str, default="SINE", widget="dropdown", options=["SINE", "SQUARE", "RAMP", "PULSE", "NOISE", "DC"]),
        DataIn("Frequency", type_hint=float, default=1000.0),
        DataIn("Amplitude", type_hint=float, default=1.0),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Phase", type_hint=float, default=0.0, optional=True),
        DataIn("Duty", type_hint=float, default=50.0, optional=True),
        DataIn("Symmetry", type_hint=float, default=50.0, optional=True)
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
        shape = await context.pull(self.id, "Shape")
        freq = await context.pull(self.id, "Frequency")
        amp = await context.pull(self.id, "Amplitude")
        offset = await context.pull(self.id, "Offset")
        phase = await context.pull(self.id, "Phase")
        duty = await context.pull(self.id, "Duty")
        sym = await context.pull(self.id, "Symmetry")

        drv = BK4052(device)
        async with locked_device(context, device, "BK4052 Config Wave"):
            await asyncio.to_thread(drv.set_channel_wave, int(channel), shape, freq, amp, offset, phase, duty, sym)

        return "Out"


@register_block("devices/bk_precision/bk4052/output")
class BK4052OutputBlock(BaseBlock):
    """Enables or disables output transmission for a channel on a BK Precision 4052."""
    icon = "🔘"
    display_name = "BK Precision 4052 Output"
    description = "Enables or disables channel output transmission state and load impedance on a BK Precision 4052."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2]),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Load", type_hint=str, default="50", widget="dropdown", options=["50", "HZ"], optional=True)
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
        enable = await context.pull(self.id, "Enable")
        load = await context.pull(self.id, "Load")

        drv = BK4052(device)
        async with locked_device(context, device, "BK4052 Output"):
            await asyncio.to_thread(drv.set_output, int(channel), bool(enable), load)

        return "Out"
