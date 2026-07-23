# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Thorlabs PM100D / PM100A / PM400 Optical Power Meter Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Optional
from comfylab.devices.base import BaseInstrumentDriver


class ThorlabsPM100D(BaseInstrumentDriver):
    """
    Driver for Thorlabs PM100D, PM100A, PM100USB, and PM400 Optical Power Meters.
    Communicates via VISA USBTMC or Virtual COM port using SCPI commands.
    """

    def set_wavelength(self, wavelength_nm: float) -> None:
        """Sets operating calibration wavelength in nanometers (nm)."""
        # Thorlabs accepts wavelength in meters (or nm if specified)
        wavelength_m = wavelength_nm * 1e-9
        self.write(f":SENS:POW:WAV {wavelength_m}")

    def get_wavelength(self) -> float:
        """Returns operating calibration wavelength in nanometers (nm)."""
        val_str = self.query(":SENS:POW:WAV?")
        return float(val_str) * 1e9

    def set_unit(self, unit: str = "W") -> None:
        """Sets power measurement display unit ('W' or 'DBM')."""
        unit_upper = unit.upper()
        if unit_upper not in ("W", "DBM"):
            raise ValueError(f"Invalid unit: {unit}. Must be 'W' or 'DBM'.")
        self.write(f":SENS:POW:UNIT {unit_upper}")

    def set_averaging(self, count: int = 10) -> None:
        """Sets measurement averaging count."""
        self.write(f":SENS:AVER:COUN {int(count)}")

    def read_power(self) -> float:
        """Triggers and reads single optical power measurement (in set unit, default W)."""
        val_str = self.query(":READ?")
        return float(val_str.split(",")[0])
