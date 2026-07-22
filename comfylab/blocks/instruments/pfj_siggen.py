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
from typing import Any, Optional

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.blocks.instruments.devices import BaseDeviceConnectBlock


@register_block("visa/signal_generator/connect")
class PFJSigGenConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a PFJSigGen device with safety teardown (output off)."""
    icon = "⚡"
    display_name = "PFJSigGen Connect"
    description = "Opens a VISA connection to a PFJSigGen signal generator. On teardown, disables output."

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        address = getattr(device, "resource_name", None)
        if address:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(device.write, "out False")
        else:
            await asyncio.to_thread(device.write, "out False")


@register_block("visa/signal_generator/config_wave")
class PFJSigGenConfigWaveBlock(BaseBlock):
    """Configures the main waveform output parameters of a PFJSigGen device."""
    icon = "🎵"
    display_name = "PFJSigGen Config Wave"
    description = "Configures wave shape, frequency, amplitude, offset, phase, and duty cycle of a PFJSigGen device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("WaveType", type_hint=str, default="sine", widget="dropdown", options=["sine", "triangle", "square", "saw", "rsaw", "pulse"]),
        DataIn("Frequency", type_hint=float, default=1000.0, optional=True),
        DataIn("Amplitude", type_hint=float, default=1.0, optional=True),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Phase", type_hint=float, default=0.0, optional=True),
        DataIn("DutyCycle", type_hint=float, default=50.0, optional=True)
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
            raise ValueError("No device connection handle supplied to PFJSigGen Config Wave block.")

        wave_type = await context.pull(self.id, "WaveType")
        frequency = await context.pull(self.id, "Frequency")
        amplitude = await context.pull(self.id, "Amplitude")
        offset = await context.pull(self.id, "Offset")
        phase = await context.pull(self.id, "Phase")
        duty_cycle = await context.pull(self.id, "DutyCycle")

        address = getattr(device, "resource_name", str(device))
        async with context.lock_manager.acquire(address):
            # Configure WaveType
            if wave_type:
                await asyncio.to_thread(device.write, f"wave:wave {wave_type}")

            # Configure Frequency
            if frequency is not None:
                await asyncio.to_thread(device.write, f"freq:freq {frequency}")

            # Configure Amplitude
            if amplitude is not None:
                await asyncio.to_thread(device.write, f"amp:amp {amplitude}")

            # Configure Offset
            if offset is not None:
                await asyncio.to_thread(device.write, f"amp:offs {offset}")

            # Configure Phase
            if phase is not None:
                await asyncio.to_thread(device.write, f"wave:phas {phase}")

            # Configure DutyCycle
            if duty_cycle is not None:
                await asyncio.to_thread(device.write, f"wave:dc {duty_cycle}")

        return "Out"


@register_block("visa/signal_generator/config_chirp")
class PFJSigGenConfigChirpBlock(BaseBlock):
    """Configures the frequency sweep chirp settings of a PFJSigGen device."""
    icon = "📈"
    display_name = "PFJSigGen Config Chirp"
    description = "Configures trigger chirp state, frequency sweep variation span, and period of a PFJSigGen device."

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
        if not device:
            raise ValueError("No device connection handle supplied to PFJSigGen Config Chirp block.")

        chirp = await context.pull(self.id, "Chirp")
        variation = await context.pull(self.id, "Variation")
        period = await context.pull(self.id, "Period")

        address = getattr(device, "resource_name", str(device))
        async with context.lock_manager.acquire(address):
            # Send chirp command
            await asyncio.to_thread(device.write, f"freq:chrp {bool(chirp)}")

            if variation is not None:
                await asyncio.to_thread(device.write, f"freq:cvar {variation}")

            if period is not None:
                await asyncio.to_thread(device.write, f"freq:cper {period}")

        return "Out"


@register_block("visa/signal_generator/set_output")
class PFJSigGenSetOutputBlock(BaseBlock):
    """Enables or disables the main RF output port of a PFJSigGen device."""
    icon = "🔌"
    display_name = "PFJSigGen Set Output"
    description = "Enables or disables the main output signal of a PFJSigGen device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Output", type_hint=bool, default=True, widget="checkbox")
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
            raise ValueError("No device connection handle supplied to PFJSigGen Set Output block.")

        output = await context.pull(self.id, "Output")

        address = getattr(device, "resource_name", str(device))
        async with context.lock_manager.acquire(address):
            await asyncio.to_thread(device.write, f"out {bool(output)}")

        return "Out"
