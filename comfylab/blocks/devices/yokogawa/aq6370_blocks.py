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
from comfylab.devices.yokogawa.aq6370 import AQ6370


@register_block("devices/yokogawa/aq6370/connect")
class AQ6370ConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Yokogawa / Ando AQ6370 Series Optical Spectrum Analyzer (OSA)."""
    icon = "🌈"
    display_name = "Yokogawa AQ6370 Connect"
    description = "Opens a VISA session to a Yokogawa AQ6370 Optical Spectrum Analyzer."


@register_block("devices/yokogawa/aq6370/sweep_config")
class AQ6370SweepConfigBlock(BaseBlock):
    """Configures center wavelength (nm), span (nm), resolution (RBW nm), and sensitivity on a Yokogawa OSA."""
    icon = "🎛️"
    display_name = "Yokogawa AQ6370 Sweep Config"
    description = "Configures center wavelength, span, RBW, and sensitivity on a Yokogawa AQ6370 OSA."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("CenterWavelength", type_hint=float, default=1550.0),
        DataIn("Span", type_hint=float, default=20.0),
        DataIn("RBW", type_hint=float, default=0.02, optional=True),
        DataIn("Sensitivity", type_hint=str, default="NORM", widget="dropdown", options=["NORM", "HIGH1", "HIGH2", "HIGH3", "MID"], optional=True)
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
        sens = await context.pull(self.id, "Sensitivity")

        drv = AQ6370(device)
        async with locked_device(context, device, "Yokogawa AQ6370 Config"):
            await asyncio.to_thread(drv.set_sweep_config, center_nm, span_nm, rbw_nm, sens)

        return "Out"


@register_block("devices/yokogawa/aq6370/acquire")
class AQ6370AcquireBlock(BaseBlock):
    """Triggers a single sweep and pulls wavelength (nm) and power spectral trace (dBm) from a Yokogawa OSA."""
    icon = "📥"
    display_name = "Yokogawa AQ6370 Acquire Trace"
    description = "Triggers single sweep on a Yokogawa OSA, outputs arrays, and broadcasts visual plot telemetry."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Trace", type_hint=str, default="TRA", widget="dropdown", options=["TRA", "TRB", "TRC"])
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
        trace_name = await context.pull(self.id, "Trace")

        drv = AQ6370(device)
        async with locked_device(context, device, "Yokogawa AQ6370 Acquire"):
            wl_vec, p_vec = await asyncio.to_thread(drv.acquire_trace, str(trace_name))
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
