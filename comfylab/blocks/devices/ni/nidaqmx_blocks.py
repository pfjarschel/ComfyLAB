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
from comfylab.devices.ni.nidaqmx_device import NIDAQmxDevice


@register_block("devices/ni/nidaqmx/connect")
class NIDAQmxConnectBlock(BaseBlock):
    """Initializes connection to National Instruments DAQmx hardware (e.g. 'Dev1')."""
    icon = "⚡"
    display_name = "NI DAQmx Connect"
    description = "Initializes an NI-DAQmx hardware session (e.g. 'Dev1'). Raises explicit error if drivers are missing."

    inputs_def = [
        ExecIn("Open"),
        DataIn("DeviceName", type_hint=str, default="Dev1", widget="text")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._daq = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        dev_name = await context.pull(self.id, "DeviceName")
        self._daq = await asyncio.to_thread(NIDAQmxDevice, dev_name)
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return self._daq
        return None


@register_block("devices/ni/nidaqmx/analog_read")
class NIDAQmxAnalogReadBlock(BaseBlock):
    """Acquires finite analog input voltage sampling from an NI DAQ channel (e.g. 'ai0')."""
    icon = "📥"
    display_name = "NI DAQmx Analog Read"
    description = "Acquires finite sample block of Analog Input voltage from an NI DAQ channel (e.g. 'ai0')."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=str, default="ai0", widget="text"),
        DataIn("SampleRate", type_hint=float, default=10000.0),
        DataIn("Samples", type_hint=int, default=1000),
        DataIn("MinVoltage", type_hint=float, default=-10.0, optional=True),
        DataIn("MaxVoltage", type_hint=float, default=10.0, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Voltage", type_hint=np.ndarray),
        DataOut("Time", type_hint=np.ndarray),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_volts: np.ndarray = np.array([])
        self._last_time: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        chan = await context.pull(self.id, "Channel")
        rate = await context.pull(self.id, "SampleRate")
        samples = await context.pull(self.id, "Samples")
        min_v = await context.pull(self.id, "MinVoltage")
        max_v = await context.pull(self.id, "MaxVoltage")

        if not isinstance(device, NIDAQmxDevice):
            raise ValueError("Invalid NI-DAQmx device handle supplied.")

        t_vec, v_vec = await asyncio.to_thread(
            device.read_analog_input,
            chan,
            min_v if min_v is not None else -10.0,
            max_v if max_v is not None else 10.0,
            int(samples),
            float(rate)
        )
        self._last_time = t_vec
        self._last_volts = v_vec

        # Broadcast plot telemetry
        floats = self._last_volts.tolist()
        point_count = len(floats)
        encoded_id = self.id.encode('utf-8')[:36].ljust(36, b'\x00')
        binary_packet = struct.pack(f"<36sI{point_count}f", encoded_id, point_count, *floats)
        await context.send_telemetry(self.id, binary_packet)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Voltage":
            return self._last_volts
        elif pin_name == "Time":
            return self._last_time
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("devices/ni/nidaqmx/analog_write")
class NIDAQmxAnalogWriteBlock(BaseBlock):
    """Outputs DC analog voltage to an NI DAQ analog output channel (e.g. 'ao0')."""
    icon = "⚡"
    display_name = "NI DAQmx Analog Write"
    description = "Outputs DC analog voltage to an NI DAQ analog output channel (e.g. 'ao0')."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=str, default="ao0", widget="text"),
        DataIn("Voltage", type_hint=float, default=0.0)
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
        chan = await context.pull(self.id, "Channel")
        voltage = await context.pull(self.id, "Voltage")

        if not isinstance(device, NIDAQmxDevice):
            raise ValueError("Invalid NI-DAQmx device handle supplied.")

        await asyncio.to_thread(device.write_analog_output, chan, float(voltage))
        return "Out"
