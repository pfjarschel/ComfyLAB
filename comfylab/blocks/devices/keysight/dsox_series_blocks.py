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
from comfylab.devices.keysight.dsox_series import KeysightDSOX


@register_block("devices/keysight/dsox_series/connect")
class KeysightDSOXConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Keysight InfiniiVision DSO-X / MSO-X Series oscilloscope."""
    icon = "📺"
    display_name = "Keysight DSO-X Connect"
    description = "Opens a VISA session to a Keysight InfiniiVision DSO-X 3000/2000/1000 oscilloscope."


@register_block("devices/keysight/dsox_series/timebase")
class KeysightDSOXTimebaseBlock(BaseBlock):
    """Configures horizontal timebase scale (s/div) and position offset on a Keysight DSO-X."""
    icon = "⏱️"
    display_name = "Keysight DSO-X Timebase"
    description = "Configures timebase scale and offset position on a Keysight DSO-X oscilloscope."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Scale", type_hint=float, default=0.001),
        DataIn("Position", type_hint=float, default=0.0, optional=True)
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
        scale = await context.pull(self.id, "Scale")
        position = await context.pull(self.id, "Position")

        drv = KeysightDSOX(device)
        async with locked_device(context, device, "Keysight DSO-X Timebase"):
            await asyncio.to_thread(drv.set_timebase, scale, position)

        return "Out"


@register_block("devices/keysight/dsox_series/channel")
class KeysightDSOXChannelBlock(BaseBlock):
    """Configures vertical channel scale (V/div), offset (V), coupling (DC/AC/GND), and enable state."""
    icon = "📶"
    display_name = "Keysight DSO-X Channel"
    description = "Configures vertical channel parameters on a Keysight DSO-X oscilloscope."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Scale", type_hint=float, default=1.0, optional=True),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Coupling", type_hint=str, default="DC", widget="dropdown", options=["DC", "AC", "GND"], optional=True)
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
        scale = await context.pull(self.id, "Scale")
        offset = await context.pull(self.id, "Offset")
        coupling = await context.pull(self.id, "Coupling")

        drv = KeysightDSOX(device)
        async with locked_device(context, device, "Keysight DSO-X Channel"):
            await asyncio.to_thread(drv.set_channel, int(channel), enable, scale, offset, coupling)

        return "Out"


@register_block("devices/keysight/dsox_series/acquire")
class KeysightDSOXAcquireBlock(BaseBlock):
    """Pulls waveform arrays from a Keysight DSO-X oscilloscope."""
    icon = "📥"
    display_name = "Keysight DSO-X Acquire"
    description = "Triggers high-speed waveform acquisition from a Keysight DSO-X, outputs arrays, and broadcasts telemetry."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Waveform", type_hint=np.ndarray),
        DataOut("Time", type_hint=np.ndarray),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_waveform: np.ndarray = np.array([])
        self._last_time: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        channel = await context.pull(self.id, "Channel")

        drv = KeysightDSOX(device)
        async with locked_device(context, device, "Keysight DSO-X Acquire"):
            t_vec, v_vec = await asyncio.to_thread(drv.acquire_waveform, int(channel))
            self._last_time = t_vec
            self._last_waveform = v_vec

            # Broadcast plot telemetry
            floats = self._last_waveform.tolist()
            point_count = len(floats)
            encoded_id = self.id.encode('utf-8')[:36].ljust(36, b'\x00')
            binary_packet = struct.pack(f"<36sI{point_count}f", encoded_id, point_count, *floats)
            await context.send_telemetry(self.id, binary_packet)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Waveform":
            return self._last_waveform
        elif pin_name == "Time":
            return self._last_time
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
