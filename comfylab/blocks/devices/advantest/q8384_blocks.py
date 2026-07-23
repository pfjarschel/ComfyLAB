# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
import struct
from typing import Any, Dict, Optional
import numpy as np

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.blocks.devices.base import BaseDeviceConnectBlock, locked_device
from comfylab.devices.advantest.q8384 import AdvantestQ8384


@register_block("devices/advantest/q8384/connect")
class AdvantestQ8384ConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to an Advantest Q8384 Optical Spectrum Analyzer (OSA)."""
    icon = "🌈"
    display_name = "Advantest Q8384 Connect"
    description = "Opens a VISA session to an Advantest Q8384 Optical Spectrum Analyzer."


@register_block("devices/advantest/q8384/sweep_config")
class AdvantestQ8384SweepConfigBlock(BaseBlock):
    """Configures center wavelength (nm), span (nm), and resolution (RBW nm) on an Advantest Q8384 OSA."""
    icon = "🎛️"
    display_name = "Advantest Q8384 Sweep Config"
    description = "Configures center wavelength, span, and RBW on an Advantest Q8384 OSA."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("CenterWavelength", type_hint=float, default=1550.0),
        DataIn("Span", type_hint=float, default=20.0),
        DataIn("RBW", type_hint=float, default=0.01, optional=True)
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
        center_nm = await context.pull(self.id, "CenterWavelength")
        span_nm = await context.pull(self.id, "Span")
        rbw_nm = await context.pull(self.id, "RBW")

        drv = AdvantestQ8384(device)
        async with locked_device(context, device, "Advantest Q8384 Config"):
            await asyncio.to_thread(drv.set_sweep_config, center_nm, span_nm, rbw_nm)

        return "Out"


@register_block("devices/advantest/q8384/acquire")
class AdvantestQ8384AcquireBlock(BaseBlock):
    """Triggers a single sweep and pulls wavelength (nm) and power trace (dBm) from an Advantest Q8384 OSA."""
    icon = "📥"
    display_name = "Advantest Q8384 Acquire Trace"
    description = "Triggers single sweep on an Advantest Q8384 OSA, outputs arrays, and broadcasts visual plot telemetry."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Power", type_hint=np.ndarray),
        DataOut("Wavelength", type_hint=np.ndarray),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_power: np.ndarray = np.array([])
        self._last_wl: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")

        drv = AdvantestQ8384(device)
        async with locked_device(context, device, "Advantest Q8384 Acquire"):
            wl_vec, p_vec = await asyncio.to_thread(drv.acquire_trace)
            self._last_wl = wl_vec
            self._last_power = p_vec

            # Broadcast plot telemetry
            floats = self._last_power.tolist()
            point_count = len(floats)
            encoded_id = self.id.encode('utf-8')[:36].ljust(36, b'\x00')
            binary_packet = struct.pack(f"<36sI{point_count}f", encoded_id, point_count, *floats)
            await context.send_telemetry(self.id, binary_packet)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Power":
            return self._last_power
        elif pin_name == "Wavelength":
            return self._last_wl
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
