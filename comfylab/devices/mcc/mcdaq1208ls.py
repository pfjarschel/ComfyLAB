# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Measurement Computing (MCC) USB-1208LS DAQ Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Optional
from comfylab.devices.base import BaseInstrumentDriver


class MCCDAQ1208LS(BaseInstrumentDriver):
    """
    Driver for Measurement Computing USB-1208LS / USB DAQ series over VISA / SCPI or PyUSB interface.
    """

    def read_analog_channel(self, channel: int = 0) -> float:
        """Reads analog voltage (V) on specified channel (0 to 7)."""
        val_str = self.query(f"AIN {channel}")
        clean_val = val_str.replace("AIN", "").strip()
        return float(clean_val)

    def write_analog_channel(self, channel: int = 0, voltage: float = 0.0) -> None:
        """Outputs analog voltage (V) on specified channel (0 or 1)."""
        self.write(f"AOUT {channel} {voltage}")

    def write_digital_port(self, port: str = "A", value: int = 0) -> None:
        """Sets digital port byte value."""
        self.write(f"DOUT PORT{port.upper()} {int(value)}")
