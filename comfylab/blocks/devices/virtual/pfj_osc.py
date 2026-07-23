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


@register_block("devices/virtual/oscilloscope/connect")
class VirtOscConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a VirtOsc device with safety teardown (stop acquisition)."""
    icon = "📺"
    display_name = "VirtOsc Connect"
    description = "Opens a VISA connection to a VirtOsc oscilloscope. On teardown, stops acquisition."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        address = getattr(device, "resource_name", None)
        if address:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(device.write, "stop")
        else:
            await asyncio.to_thread(device.write, "stop")


@register_block("devices/virtual/oscilloscope/timebase")
class VirtOscTimebaseBlock(BaseBlock):
    """Configures horizontal acquisition parameters (scale, offset, length) on a VirtOsc device."""
    icon = "⏱️"
    display_name = "VirtOsc Timebase"
    description = "Configures horizontal timebase scale, offset, and points size on a VirtOsc device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Scale", type_hint=float, default=0.001),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Points", type_hint=int, default=1000, optional=True)
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
        offset = await context.pull(self.id, "Offset")
        points = await context.pull(self.id, "Points")

        async with locked_device(context, device, "VirtOsc Timebase"):
            if scale is not None:
                await asyncio.to_thread(device.write, f"horiz:scale {scale}")
            if offset is not None:
                await asyncio.to_thread(device.write, f"horiz:offset {offset}")
            if points is not None:
                await asyncio.to_thread(device.write, f"acq:points {int(points)}")

        return "Out"


@register_block("devices/virtual/oscilloscope/channel")
class VirtOscChannelBlock(BaseBlock):
    """Configures input channel scale, offset, and enable state on a VirtOsc device."""
    icon = "📶"
    display_name = "VirtOsc Channel"
    description = "Configures a specific input channel vertical parameters (scale, offset, active state) on a VirtOsc device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Scale", type_hint=float, default=1.0, optional=True),
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
        enable = await context.pull(self.id, "Enable")
        scale = await context.pull(self.id, "Scale")
        offset = await context.pull(self.id, "Offset")

        if not (1 <= int(channel) <= 4):
            raise ValueError(f"Invalid channel selection for VirtOsc: {channel}. Must be 1-4.")

        async with locked_device(context, device, "VirtOsc Channel Config"):
            await asyncio.to_thread(device.write, f"c{channel}:enable {bool(enable)}")
            if scale is not None:
                await asyncio.to_thread(device.write, f"c{channel}:scale {scale}")
            if offset is not None:
                await asyncio.to_thread(device.write, f"c{channel}:offset {offset}")

        return "Out"


@register_block("devices/virtual/oscilloscope/trigger")
class VirtOscTriggerBlock(BaseBlock):
    """Configures the capture trigger mode on a VirtOsc device."""
    icon = "🎯"
    display_name = "VirtOsc Trigger"
    description = "Sets trigger operating mode (e.g. auto, free) on a VirtOsc device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Mode", type_hint=str, default="auto", widget="dropdown", options=["auto", "free"])
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

        async with locked_device(context, device, "VirtOsc Trigger"):
            await asyncio.to_thread(device.write, f"trig:{mode}")

        return "Out"


@register_block("devices/virtual/oscilloscope/state")
class VirtOscStateBlock(BaseBlock):
    """Starts or stops active scanning/acquiring loops on a VirtOsc device."""
    icon = "⏯️"
    display_name = "VirtOsc State"
    description = "Puts VirtOsc device scanning state to either RUN or STOP."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("State", type_hint=str, default="run", widget="dropdown", options=["run", "stop"])
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

        state = await context.pull(self.id, "State")

        async with locked_device(context, device, "VirtOsc State"):
            if state == "run":
                await asyncio.to_thread(device.write, "run")
            elif state == "stop":
                await asyncio.to_thread(device.write, "stop")

        return "Out"


@register_block("devices/virtual/oscilloscope/acquire")
class VirtOscAcquireBlock(BaseBlock):
    """Pulls timebase coordinates and waveform channel values from a VirtOsc device."""
    icon = "📥"
    display_name = "VirtOsc Acquire"
    description = "Triggers acquisition retrieval, outputs waveform arrays, and broadcasts visual plot telemetry."

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
        if not (1 <= int(channel) <= 4):
            raise ValueError(f"Invalid channel selection for VirtOsc: {channel}. Must be 1-4.")

        async with locked_device(context, device, "VirtOsc Acquire"):
            time_str = await asyncio.to_thread(device.query, "horiz:data?")
            data_str = await asyncio.to_thread(device.query, f"c{channel}:data?")

            self._last_time = np.array([float(v) for v in time_str.split(",") if v.strip()], dtype=float)
            self._last_waveform = np.array([float(v) for v in data_str.split(",") if v.strip()], dtype=float)

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
