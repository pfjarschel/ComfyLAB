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
from comfylab.devices.srs.sr830 import SR830


@register_block("devices/srs/sr830/connect")
class SR830ConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Stanford Research Systems SR830 Lock-In Amplifier."""
    icon = "📻"
    display_name = "SRS SR830 Connect"
    description = "Opens a VISA session to an SRS SR830/SR850/SR860 Lock-In Amplifier."


@register_block("devices/srs/sr830/reference")
class SR830ReferenceBlock(BaseBlock):
    """Configures internal reference frequency (Hz), phase shift (deg), and sine amplitude (V) on an SRS SR830."""
    icon = "⚙️"
    display_name = "SRS SR830 Reference Config"
    description = "Configures reference frequency, phase, and sine output amplitude on an SRS SR830."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Frequency", type_hint=float, default=1000.0, optional=True),
        DataIn("Phase", type_hint=float, default=0.0, optional=True),
        DataIn("Amplitude", type_hint=float, default=1.0, optional=True)
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
        freq = await context.pull(self.id, "Frequency")
        phase = await context.pull(self.id, "Phase")
        amp = await context.pull(self.id, "Amplitude")

        drv = SR830(device)
        async with locked_device(context, device, "SRS SR830 Config"):
            await asyncio.to_thread(drv.set_reference, freq, phase, amp)

        return "Out"


@register_block("devices/srs/sr830/read")
class SR830ReadBlock(BaseBlock):
    """Queries simultaneous snapshot readings of X (V), Y (V), R magnitude (V), and Phase (deg) from an SRS SR830."""
    icon = "📊"
    display_name = "SRS SR830 Read Snapshot"
    description = "Queries simultaneous snapshot of X, Y, R, and Phase from an SRS SR830 lock-in amplifier."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("X", type_hint=float),
        DataOut("Y", type_hint=float),
        DataOut("R", type_hint=float),
        DataOut("Phase", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_x: float = 0.0
        self._last_y: float = 0.0
        self._last_r: float = 0.0
        self._last_phase: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")

        drv = SR830(device)
        async with locked_device(context, device, "SRS SR830 Read"):
            x, y, r, p = await asyncio.to_thread(drv.snap_all)
            self._last_x = x
            self._last_y = y
            self._last_r = r
            self._last_phase = p

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "X":
            return self._last_x
        elif pin_name == "Y":
            return self._last_y
        elif pin_name == "R":
            return self._last_r
        elif pin_name == "Phase":
            return self._last_phase
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
