# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Keithley 2400 / 2420 / 2450 Series Source Measure Unit (SMU) Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Tuple, Optional
from comfylab.devices.base import BaseInstrumentDriver


class Keithley2400(BaseInstrumentDriver):
    """
    Driver for Keithley 2400, 2410, 2420, 2440, and 2450 Source Measure Units (SMUs).
    Communicates via VISA GPIB, RS-232, or Ethernet TCPIP using standard SCPI commands.
    """

    def configure_source_voltage(
        self,
        voltage: float = 0.0,
        current_limit: float = 0.1,
        voltage_range: Optional[float] = None
    ) -> None:
        """Sets SMU to Source Voltage / Measure Current mode."""
        self.write(":SOURce:FUNCtion VOLTage")
        if voltage_range is not None:
            self.write(f":SOURce:VOLTage:RANGe {voltage_range}")
        self.write(f":SOURce:VOLTage:LEVel {voltage}")
        self.write(f":SENSe:CURRent:PROTection {current_limit}")
        self.write(":SENS:FUNC 'CURR'")

    def configure_source_current(
        self,
        current: float = 0.0,
        voltage_limit: float = 10.0,
        current_range: Optional[float] = None
    ) -> None:
        """Sets SMU to Source Current / Measure Voltage mode."""
        self.write(":SOURce:FUNCtion CURRent")
        if current_range is not None:
            self.write(f":SOURce:CURRent:RANGe {current_range}")
        self.write(f":SOURce:CURRent:LEVel {current}")
        self.write(f":SENSe:VOLTage:PROTection {voltage_limit}")
        self.write(":SENS:FUNC 'VOLT'")

    def set_output(self, enable: bool = True) -> None:
        """Enables or disables output state."""
        state = "ON" if enable else "OFF"
        self.write(f":OUTPut {state}")

    def read_measurement(self) -> Tuple[float, float]:
        """
        Triggers measurement reading. Returns tuple of (Voltage_V, Current_A).
        """
        val_str = self.query(":READ?")
        parts = [float(v) for v in val_str.split(",") if v.strip()]
        
        voltage = parts[0] if len(parts) > 0 else 0.0
        current = parts[1] if len(parts) > 1 else 0.0
        return voltage, current
