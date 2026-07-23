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
from comfylab.devices.generic.siggen import GenericSigGen


@register_block("devices/generic/siggen/connect")
class GenericSigGenConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Generic SCPI Signal Generator."""
    icon = "⚡"
    display_name = "Generic SigGen Connect"
    description = "Opens a VISA session to a SCPI Signal / Function Generator."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        drv = GenericSigGen(device)
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(drv.set_output, 1, False)
        else:
            await asyncio.to_thread(drv.set_output, 1, False)


@register_block("devices/generic/siggen/config_wave")
class GenericSigGenConfigWaveBlock(BaseBlock):
    """Configures output waveform parameters for a channel on a SCPI Signal Generator."""
    icon = "🌊"
    display_name = "Generic SigGen Config Wave"
    description = "Configures shape, frequency, amplitude, and offset for a channel on a SCPI Signal Generator."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2]),
        DataIn("Shape", type_hint=str, default="SINE", widget="dropdown", options=["SINE", "SQUARE", "RAMP", "PULSE", "NOISE"]),
        DataIn("Frequency", type_hint=float, default=1000.0),
        DataIn("Amplitude", type_hint=float, default=1.0),
        DataIn("Offset", type_hint=float, default=0.0, optional=True)
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

        drv = GenericSigGen(device)
        async with locked_device(context, device, "Generic SigGen Config Wave"):
            await asyncio.to_thread(drv.set_channel_wave, int(channel), shape, freq, amp, offset)

        return "Out"


@register_block("devices/generic/siggen/output")
class GenericSigGenOutputBlock(BaseBlock):
    """Enables or disables channel output state on a SCPI Signal Generator."""
    icon = "🔘"
    display_name = "Generic SigGen Output"
    description = "Enables or disables channel output transmission state on a SCPI Signal Generator."

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

        drv = GenericSigGen(device)
        async with locked_device(context, device, "Generic SigGen Output"):
            await asyncio.to_thread(drv.set_output, int(channel), bool(enable))

        return "Out"
