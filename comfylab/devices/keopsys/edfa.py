# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Keopsys EDFA (Erbium-Doped Fiber Amplifier) Driver.
Pure Python — no ComfyLAB UI or block dependencies.
Modernized from legacy C++/Qt implementation.
"""

from typing import Any, Optional
from comfylab.devices.base import BaseInstrumentDriver


class KeopsysEDFA(BaseInstrumentDriver):
    """
    Driver for Keopsys Optical Fiber Amplifiers (EDFA) over VISA GPIB / RS-232.
    """

    def set_pump_state(self, enable: bool = True) -> None:
        """Enables or disables pump diode emission (K1 = ON, K0 = OFF)."""
        state_str = "K1" if enable else "K0"
        self.write(state_str)

    def set_control_mode(self, mode: str = "ACC") -> None:
        """Sets control mode ('ACC' = Constant Current, 'APC' = Constant Power)."""
        mode_upper = mode.upper()
        if mode_upper == "ACC":
            self.write("ASS=1")
        elif mode_upper == "APC":
            self.write("ASS=2")
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'ACC' or 'APC'.")

    def set_current(self, current_ma: float) -> None:
        """Sets pump diode current in mA."""
        self.write(f"IC2={current_ma}")

    def set_power(self, power_mw: float) -> None:
        """Sets optical output power in mW."""
        self.write(f"CPU={power_mw / 10.0}")

    def read_temperature(self) -> float:
        """Reads diode temperature in °C."""
        res_str = self.query("TD2?")
        clean_val = res_str.replace("TD2=", "").strip()
        return float(clean_val) / 100.0
