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
from comfylab.devices.minipa.mfg4230 import MFG4230


@register_block("devices/minipa/mfg4230/connect")
class MFG4230ConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Minipa MFG-4230 function generator with safety teardown."""
    icon = "⚡"
    display_name = "Minipa MFG-4230 Connect"
    description = "Opens a VISA session to a Minipa MFG-4230 function generator. On teardown, disables output."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        drv = MFG4230(device)
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(drv.set_output, 1, False)
                await asyncio.to_thread(drv.set_output, 2, False)
        else:
            await asyncio.to_thread(drv.set_output, 1, False)
            await asyncio.to_thread(drv.set_output, 2, False)


@register_block("devices/minipa/mfg4230/config_wave")
class MFG4230ConfigWaveBlock(BaseBlock):
    """Configures output waveform parameters for a channel on a Minipa MFG-4230 function generator."""
    icon = "🌊"
    display_name = "Minipa MFG-4230 Config Wave"
    description = "Configures shape, frequency, amplitude, offset, and phase for a channel on a Minipa MFG-4230."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2]),
        DataIn("Shape", type_hint=str, default="SINE", widget="dropdown", options=["SINE", "SQUARE", "RAMP", "PULSE", "NOISE"]),
        DataIn("Frequency", type_hint=float, default=1000.0),
        DataIn("Amplitude", type_hint=float, default=1.0),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Phase", type_hint=float, default=0.0, optional=True)
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

        drv = MFG4230(device)
        async with locked_device(context, device, "MFG4230 Config Wave"):
            await asyncio.to_thread(drv.set_channel_wave, int(channel), shape, freq, amp, offset, phase)

        return "Out"


@register_block("devices/minipa/mfg4230/output")
class MFG4230OutputBlock(BaseBlock):
    """Enables or disables output transmission for a channel on a Minipa MFG-4230."""
    icon = "🔘"
    display_name = "Minipa MFG-4230 Output"
    description = "Enables or disables channel output transmission state on a Minipa MFG-4230."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2]),
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
        enable = await context.pull(self.id, "Enable")

        drv = MFG4230(device)
        async with locked_device(context, device, "MFG4230 Output"):
            await asyncio.to_thread(drv.set_output, int(channel), bool(enable))

        return "Out"
