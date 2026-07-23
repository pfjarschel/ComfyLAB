# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Generic SCPI Signal Generator / Function Generator Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Optional
from comfylab.devices.base import BaseInstrumentDriver


class GenericSigGen(BaseInstrumentDriver):
    """
    Driver for SCPI-compliant Signal Generators (Keysight, Rigol, Siglent, Tektronix).
    """

    def set_channel_wave(
        self,
        channel: int = 1,
        shape: Optional[str] = None,
        frequency: Optional[float] = None,
        amplitude: Optional[float] = None,
        offset: Optional[float] = None
    ) -> None:
        """Configures shape, frequency (Hz), amplitude (Vpp), and offset (V)."""
        ch_prefix = f"SOURce{channel}"

        if shape is not None:
            self.write(f"{ch_prefix}:FUNCtion {shape.upper()}")
        if frequency is not None:
            self.write(f"{ch_prefix}:FREQuency {frequency}")
        if amplitude is not None:
            self.write(f"{ch_prefix}:VOLTage {amplitude}")
        if offset is not None:
            self.write(f"{ch_prefix}:VOLTage:OFFSet {offset}")

    def set_output(self, channel: int = 1, enable: bool = True) -> None:
        """Enables or disables output transmission for specified channel."""
        state = "ON" if enable else "OFF"
        self.write(f"OUTPut{channel}:STATe {state}")
