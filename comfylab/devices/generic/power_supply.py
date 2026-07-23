# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Generic SCPI DC Power Supply / Source Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Optional
from comfylab.devices.base import BaseInstrumentDriver


class GenericPowerSupply(BaseInstrumentDriver):
    """
    Driver for SCPI-compliant DC Power Supplies (Keysight E36300, Rigol DP series, BK Precision, GW Instek).
    """

    def set_channel(
        self,
        channel: int = 1,
        voltage: Optional[float] = None,
        current_limit: Optional[float] = None
    ) -> None:
        """Sets voltage (V) and current limit (A) for specified channel."""
        try:
            self.write(f"INSTrument:NSELect {channel}")
        except Exception:
            pass

        if voltage is not None:
            self.write(f"SOURce:VOLTage {voltage}")
        if current_limit is not None:
            self.write(f"SOURce:CURRent {current_limit}")

    def set_output(self, channel: int = 1, enable: bool = True) -> None:
        """Enables or disables output state."""
        try:
            self.write(f"INSTrument:NSELect {channel}")
        except Exception:
            pass
        state = "ON" if enable else "OFF"
        self.write(f"OUTPut {state}")

    def measure_voltage(self, channel: int = 1) -> float:
        """Measures output voltage (V)."""
        try:
            self.write(f"INSTrument:NSELect {channel}")
        except Exception:
            pass
        val_str = self.query("MEASure:VOLTage?")
        return float(val_str.split(",")[0])

    def measure_current(self, channel: int = 1) -> float:
        """Measures output current (A)."""
        try:
            self.write(f"INSTrument:NSELect {channel}")
        except Exception:
            pass
        val_str = self.query("MEASure:CURRent?")
        return float(val_str.split(",")[0])
