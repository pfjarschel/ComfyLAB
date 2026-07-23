# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
from typing import Any, Optional, Dict

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.blocks.devices.base import BaseDeviceConnectBlock, locked_device


@register_block("devices/virtual/signal_generator/connect")
class VirtSigGenConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a VirtSigGen device with safety teardown (output off)."""
    icon = "⚡"
    display_name = "VirtSigGen Connect"
    description = "Opens a VISA connection to a VirtSigGen signal generator. On teardown, disables output."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        address = getattr(device, "resource_name", None)
        if address:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(device.write, "out False")
        else:
            await asyncio.to_thread(device.write, "out False")


@register_block("devices/virtual/signal_generator/config_wave")
class VirtSigGenConfigWaveBlock(BaseBlock):
    """Configures the main waveform output parameters of a VirtSigGen device."""
    icon = "🎵"
    display_name = "VirtSigGen Config Wave"
    description = "Configures wave shape, frequency, amplitude, offset, phase, and duty cycle of a VirtSigGen device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("WaveType", type_hint=str, default="sine", widget="dropdown", options=["sine", "triangle", "square", "saw", "rsaw", "pulse"]),
        DataIn("Frequency", type_hint=float, default=1000.0, optional=True),
        DataIn("Amplitude", type_hint=float, default=1.0, optional=True),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Phase", type_hint=float, default=0.0, optional=True),
        DataIn("DutyCycle", type_hint=float, default=50.0, optional=True),
        DataIn("Shape", type_hint=str, default="sine", optional=True)
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

        wave_type = await context.pull(self.id, "WaveType")
        shape = await context.pull(self.id, "Shape")
        frequency = await context.pull(self.id, "Frequency")
        amplitude = await context.pull(self.id, "Amplitude")
        offset = await context.pull(self.id, "Offset")
        phase = await context.pull(self.id, "Phase")
        duty_cycle = await context.pull(self.id, "DutyCycle")

        target_wave = wave_type if wave_type is not None else shape

        async with locked_device(context, device, "VirtSigGen Config Wave"):
            if target_wave:
                w_str = str(target_wave).lower()
                if w_str in ("sawtooth", "ramp"):
                    w_str = "saw"
                await asyncio.to_thread(device.write, f"wave:wave {w_str}")

            if frequency is not None:
                await asyncio.to_thread(device.write, f"freq:freq {frequency}")

            if amplitude is not None:
                await asyncio.to_thread(device.write, f"amp:amp {amplitude}")

            if offset is not None:
                await asyncio.to_thread(device.write, f"amp:offs {offset}")

            if phase is not None:
                await asyncio.to_thread(device.write, f"wave:phas {phase}")

            if duty_cycle is not None:
                await asyncio.to_thread(device.write, f"wave:dc {duty_cycle}")

        return "Out"


@register_block("devices/virtual/signal_generator/config_chirp")
class VirtSigGenConfigChirpBlock(BaseBlock):
    """Configures the frequency sweep chirp settings of a VirtSigGen device."""
    icon = "📈"
    display_name = "VirtSigGen Config Chirp"
    description = "Configures trigger chirp state, frequency sweep variation span, and period of a VirtSigGen device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Chirp", type_hint=bool, default=False, widget="checkbox"),
        DataIn("Variation", type_hint=float, default=100.0, optional=True),
        DataIn("Period", type_hint=float, default=1.0, optional=True)
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

        chirp = await context.pull(self.id, "Chirp")
        variation = await context.pull(self.id, "Variation")
        period = await context.pull(self.id, "Period")

        async with locked_device(context, device, "VirtSigGen Config Chirp"):
            await asyncio.to_thread(device.write, f"freq:chrp {bool(chirp)}")

            if variation is not None:
                await asyncio.to_thread(device.write, f"freq:cvar {variation}")

            if period is not None:
                await asyncio.to_thread(device.write, f"freq:cper {period}")

        return "Out"


@register_block("devices/virtual/signal_generator/output")
class VirtSigGenOutputBlock(BaseBlock):
    """Enables or disables output signal transmission of a VirtSigGen device."""
    icon = "🔘"
    display_name = "VirtSigGen Output"
    description = "Enables or disables output state (ON/OFF) of a VirtSigGen device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Output", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Enable", type_hint=bool, default=True, optional=True)
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

        output = await context.pull(self.id, "Output")
        enable = await context.pull(self.id, "Enable")

        target_out = output if output is not None else enable

        async with locked_device(context, device, "VirtSigGen Output"):
            await asyncio.to_thread(device.write, f"out {bool(target_out)}")

        return "Out"
