# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import asyncio
import struct
from typing import Any, Dict, Optional, List

from comfylab.engine.registry import register_node
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.nodes.instruments.devices import BaseDeviceConnectNode


@register_node("visa/oscilloscope/connect")
class PFJOscConnectNode(BaseDeviceConnectNode):
    """Opens a VISA connection to a PFJOsc device with safety teardown (stop acquisition)."""
    icon = "📺"
    display_name = "PFJOsc Connect"
    description = "Opens a VISA connection to a PFJOsc oscilloscope. On teardown, stops acquisition."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        address = getattr(device, "resource_name", None)
        if address:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(device.write, "stop")
        else:
            await asyncio.to_thread(device.write, "stop")


@register_node("visa/oscilloscope/timebase")
class PFJOscTimebaseNode(BaseNode):
    """Configures horizontal acquisition parameters (scale, offset, length) on a PFJOsc device."""
    icon = "⏱️"
    display_name = "PFJOsc Timebase"
    description = "Configures horizontal timebase scale, offset, and points size on a PFJOsc device."

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
        if not device:
            raise ValueError("No device connection handle supplied to PFJOsc Timebase node.")

        scale = await context.pull(self.id, "Scale")
        offset = await context.pull(self.id, "Offset")
        points = await context.pull(self.id, "Points")

        address = getattr(device, "resource_name", str(device))
        async with context.lock_manager.acquire(address):
            if scale is not None:
                await asyncio.to_thread(device.write, f"horiz:scale {scale}")
            if offset is not None:
                await asyncio.to_thread(device.write, f"horiz:offset {offset}")
            if points is not None:
                await asyncio.to_thread(device.write, f"acq:points {int(points)}")

        return "Out"


@register_node("visa/oscilloscope/channel")
class PFJOscChannelNode(BaseNode):
    """Configures input channel scale, offset, and enable state on a PFJOsc device."""
    icon = "📶"
    display_name = "PFJOsc Channel"
    description = "Configures a specific input channel vertical parameters (scale, offset, active state) on a PFJOsc device."

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
        if not device:
            raise ValueError("No device connection handle supplied to PFJOsc Channel node.")

        channel = await context.pull(self.id, "Channel")
        enable = await context.pull(self.id, "Enable")
        scale = await context.pull(self.id, "Scale")
        offset = await context.pull(self.id, "Offset")

        if not (1 <= int(channel) <= 4):
            raise ValueError(f"Invalid channel selection for PFJOsc: {channel}. Must be 1-4.")

        address = getattr(device, "resource_name", str(device))
        async with context.lock_manager.acquire(address):
            # Set enable state
            await asyncio.to_thread(device.write, f"c{channel}:enable {bool(enable)}")

            if scale is not None:
                await asyncio.to_thread(device.write, f"c{channel}:scale {scale}")

            if offset is not None:
                await asyncio.to_thread(device.write, f"c{channel}:offset {offset}")

        return "Out"


@register_node("visa/oscilloscope/trigger")
class PFJOscTriggerNode(BaseNode):
    """Configures the capture trigger mode on a PFJOsc device."""
    icon = "🎯"
    display_name = "PFJOsc Trigger"
    description = "Sets trigger operating mode (e.g. auto, free) on a PFJOsc device."

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
        if not device:
            raise ValueError("No device connection handle supplied to PFJOsc Trigger node.")

        mode = await context.pull(self.id, "Mode")

        address = getattr(device, "resource_name", str(device))
        async with context.lock_manager.acquire(address):
            await asyncio.to_thread(device.write, f"trig:{mode}")

        return "Out"


@register_node("visa/oscilloscope/state")
class PFJOscStateNode(BaseNode):
    """Starts or stops active scanning/acquiring loops on a PFJOsc device."""
    icon = "⏯️"
    display_name = "PFJOsc State"
    description = "Puts PFJOsc device scanning state to either RUN or STOP."

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
        if not device:
            raise ValueError("No device connection handle supplied to PFJOsc State node.")

        state = await context.pull(self.id, "State")

        address = getattr(device, "resource_name", str(device))
        async with context.lock_manager.acquire(address):
            if state == "run":
                await asyncio.to_thread(device.write, "run")
            elif state == "stop":
                await asyncio.to_thread(device.write, "stop")

        return "Out"


@register_node("visa/oscilloscope/acquire")
class PFJOscAcquireNode(BaseNode):
    """Pulls timebase coordinates and waveform channel values from a PFJOsc device."""
    icon = "📥"
    display_name = "PFJOsc Acquire"
    description = "Triggers acquisition retrieval, outputs waveform arrays, and broadcasts visual plot telemetry."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Waveform", type_hint=list),
        DataOut("Time", type_hint=list),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._last_waveform: List[float] = []
        self._last_time: List[float] = []

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        if not device:
            raise ValueError("No device connection handle supplied to PFJOsc Acquire node.")

        channel = await context.pull(self.id, "Channel")
        if not (1 <= int(channel) <= 4):
            raise ValueError(f"Invalid channel selection for PFJOsc: {channel}. Must be 1-4.")

        address = getattr(device, "resource_name", str(device))
        async with context.lock_manager.acquire(address):
            # Query horizontal time data
            time_str = await asyncio.to_thread(device.query, "horiz:data?")
            # Query vertical voltage data
            data_str = await asyncio.to_thread(device.query, f"c{channel}:data?")

            # Parse responses
            self._last_time = [float(v) for v in time_str.split(",") if v.strip()]
            self._last_waveform = [float(v) for v in data_str.split(",") if v.strip()]

            # Package and send visual telemetry packet
            floats = [float(v) for v in self._last_waveform]
            point_count = len(floats)
            
            # Pack: 36-char node ID (padded), 4-byte unsigned int point count, and floats
            encoded_id = self.id.encode('utf-8')[:36].ljust(36, b'\x00')
            binary_packet = struct.pack(f"<36sI{point_count}f", encoded_id, point_count, *floats)
            
            # Broadcast over telemetry websocket
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
