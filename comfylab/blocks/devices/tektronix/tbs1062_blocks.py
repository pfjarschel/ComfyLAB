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
from comfylab.devices.tektronix.tbs1062 import TBS1062


@register_block("devices/tektronix/tbs1062/connect")
class TBS1062ConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Tektronix TBS1062 oscilloscope with safety teardown."""
    icon = "📺"
    display_name = "Tektronix TBS1062 Connect"
    description = "Opens a VISA session to a Tektronix TBS1062 oscilloscope. On teardown, stops acquisition."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        drv = TBS1062(device)
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(drv.stop_acquisition)
        else:
            await asyncio.to_thread(drv.stop_acquisition)


@register_block("devices/tektronix/tbs1062/timebase")
class TBS1062TimebaseBlock(BaseBlock):
    """Configures horizontal timebase scale (seconds/div) and position on a Tektronix TBS1062."""
    icon = "⏱️"
    display_name = "Tektronix TBS1062 Timebase"
    description = "Configures horizontal timebase scale and offset position on a Tektronix TBS1062."

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

        drv = TBS1062(device)
        async with locked_device(context, device, "TBS1062 Timebase"):
            await asyncio.to_thread(drv.set_timebase, scale, position)

        return "Out"


@register_block("devices/tektronix/tbs1062/channel")
class TBS1062ChannelBlock(BaseBlock):
    """Configures vertical scale, offset position, coupling, and enable state for a TBS1062 channel."""
    icon = "📶"
    display_name = "Tektronix TBS1062 Channel"
    description = "Configures vertical channel parameters (scale, position, coupling, enable) on a TBS1062."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2]),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Scale", type_hint=float, default=1.0, optional=True),
        DataIn("Position", type_hint=float, default=0.0, optional=True),
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
        position = await context.pull(self.id, "Position")
        coupling = await context.pull(self.id, "Coupling")

        drv = TBS1062(device)
        async with locked_device(context, device, "TBS1062 Channel Config"):
            await asyncio.to_thread(drv.set_channel, int(channel), enable, scale, position, coupling)

        return "Out"


@register_block("devices/tektronix/tbs1062/acquire")
class TBS1062AcquireBlock(BaseBlock):
    """Pulls waveform arrays from a Tektronix TBS1062 oscilloscope."""
    icon = "📥"
    display_name = "Tektronix TBS1062 Acquire"
    description = "Triggers acquisition retrieval from a Tektronix TBS1062, outputs arrays, and broadcasts visual plot telemetry."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2])
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

        drv = TBS1062(device)
        async with locked_device(context, device, "TBS1062 Acquire"):
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
