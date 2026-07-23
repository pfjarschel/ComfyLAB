# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Owon DGE2000 / Minipa MFG-4230 Series Dual-Channel Function Generator Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Optional
from comfylab.devices.base import BaseInstrumentDriver


class DGE2000(BaseInstrumentDriver):
    """
    Driver for Owon DGE2000 series (and Minipa MFG-4230 rebrand) dual-channel function generators.
    Uses standard SCPI commands (SOURce<n>:FUNCtion, FREQuency, VOLTage, etc.).
    """

    def set_channel_wave(
        self,
        channel: int = 1,
        shape: Optional[str] = None,
        frequency: Optional[float] = None,
        amplitude: Optional[float] = None,
        offset: Optional[float] = None,
        phase: Optional[float] = None
    ) -> None:
        """Configures waveform shape, frequency (Hz), amplitude (Vpp), offset (V), and phase (deg) for a channel."""
        if channel not in (1, 2):
            raise ValueError(f"Invalid channel selection: {channel}. Must be 1 or 2.")

        ch_prefix = f"SOURce{channel}"

        if shape is not None:
            # Map standard shape names to SCPI expected tokens
            shape_upper = shape.upper()
            if shape_upper in ("SINE", "SIN"):
                func_str = "SINE"
            elif shape_upper in ("SQUARE", "SQU"):
                func_str = "SQUare"
            elif shape_upper in ("RAMP", "TRIANGLE"):
                func_str = "RAMP"
            elif shape_upper in ("PULSE", "PULS"):
                func_str = "PULSe"
            elif shape_upper in ("NOISE", "NOIS"):
                func_str = "NOISe"
            else:
                func_str = shape_upper

            self.write(f"{ch_prefix}:FUNCtion {func_str}")

        if frequency is not None:
            self.write(f"{ch_prefix}:FREQuency {frequency}")

        if amplitude is not None:
            self.write(f"{ch_prefix}:VOLTage {amplitude}")

        if offset is not None:
            self.write(f"{ch_prefix}:VOLTage:OFFSet {offset}")

        if phase is not None:
            self.write(f"{ch_prefix}:PHASe {phase}")

    def set_output(self, channel: int = 1, enable: bool = True) -> None:
        """Enables or disables output state for channel 1 or 2."""
        if channel not in (1, 2):
            raise ValueError(f"Invalid channel selection: {channel}. Must be 1 or 2.")
        state = "ON" if enable else "OFF"
        self.write(f"OUTPut{channel}:STATe {state}")
