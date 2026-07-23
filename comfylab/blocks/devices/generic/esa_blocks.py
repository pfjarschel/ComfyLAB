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
from comfylab.devices.generic.esa import GenericESA


@register_block("devices/generic/esa/connect")
class GenericESAConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Generic SCPI Electrical Spectrum Analyzer."""
    icon = "📻"
    display_name = "Generic ESA Connect"
    description = "Opens a VISA session to a SCPI Electrical Spectrum Analyzer (ESA)."


@register_block("devices/generic/esa/sweep_config")
class GenericESASweepConfigBlock(BaseBlock):
    """Configures frequency boundaries, RBW/VBW, and sweep points on a SCPI ESA."""
    icon = "🎛️"
    display_name = "Generic ESA Sweep Config"
    description = "Configures frequency center/span, start/stop, RBW, VBW, and sweep points on a SCPI ESA."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Center", type_hint=float, default=1e9, optional=True),
        DataIn("Span", type_hint=float, default=100e6, optional=True),
        DataIn("Start", type_hint=float, optional=True),
        DataIn("Stop", type_hint=float, optional=True),
        DataIn("RBW", type_hint=float, optional=True),
        DataIn("VBW", type_hint=float, optional=True),
        DataIn("Points", type_hint=int, default=401, optional=True)
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
        center = await context.pull(self.id, "Center")
        span = await context.pull(self.id, "Span")
        start = await context.pull(self.id, "Start")
        stop = await context.pull(self.id, "Stop")
        rbw = await context.pull(self.id, "RBW")
        vbw = await context.pull(self.id, "VBW")
        points = await context.pull(self.id, "Points")

        drv = GenericESA(device)
        async with locked_device(context, device, "Generic ESA Config"):
            await asyncio.to_thread(drv.set_frequency, center, span, start, stop)
            await asyncio.to_thread(drv.set_bandwidth, rbw, vbw, auto_rbw=(rbw is None))
            await asyncio.to_thread(drv.set_sweep, points)

        return "Out"


@register_block("devices/generic/esa/acquire")
class GenericESAAcquireBlock(BaseBlock):
    """Pulls frequency vector (Hz) and power spectral trace (dBm) from a SCPI ESA."""
    icon = "📥"
    display_name = "Generic ESA Acquire Trace"
    description = "Triggers trace acquisition retrieval from a SCPI ESA, outputs arrays, and broadcasts visual plot telemetry."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Trace", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Power", type_hint=np.ndarray),
        DataOut("Frequency", type_hint=np.ndarray),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_power: np.ndarray = np.array([])
        self._last_freq: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        trace_num = await context.pull(self.id, "Trace")

        drv = GenericESA(device)
        async with locked_device(context, device, "Generic ESA Acquire"):
            f_vec, p_vec = await asyncio.to_thread(drv.acquire_trace, int(trace_num))
            self._last_freq = f_vec
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
        elif pin_name == "Frequency":
            return self._last_freq
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
