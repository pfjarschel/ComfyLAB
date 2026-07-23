# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Agilent / Keysight 8163B / 8164B / 816x Optical Mainframe Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Optional
from comfylab.devices.base import BaseInstrumentDriver


class Agilent816x(BaseInstrumentDriver):
    """
    Driver for Agilent / Keysight 8163A/B, 8164A/B, and 8166A/B Lightwave Multimeter mainframes
    hosting tunable laser sources and optical power sensor modules.
    """

    def set_laser_wavelength(self, slot: int = 1, wavelength_nm: float = 1550.0) -> None:
        """Sets laser source output wavelength in nanometers (nm)."""
        wavelength_m = wavelength_nm * 1e-9
        self.write(f":SOURce{slot}:WAVelength {wavelength_m}")

    def set_laser_power(self, slot: int = 1, power_dbm: float = 0.0) -> None:
        """Sets laser source output power in dBm."""
        self.write(f":SOURce{slot}:POWer {power_dbm}DBM")

    def set_laser_state(self, slot: int = 1, enable: bool = True) -> None:
        """Enables or disables laser diode output state for specified slot."""
        state = "ON" if enable else "OFF"
        self.write(f":SOURce{slot}:POWer:STATe {state}")

    def set_sensor_wavelength(self, slot: int = 2, wavelength_nm: float = 1550.0) -> None:
        """Sets optical power sensor calibration wavelength in nanometers (nm)."""
        wavelength_m = wavelength_nm * 1e-9
        self.write(f":SENSe{slot}:POWer:WAVelength {wavelength_m}")

    def read_sensor_power(self, slot: int = 2) -> float:
        """Reads optical power from sensor module in slot (returns power in Watts)."""
        val_str = self.query(f":READ{slot}:POWer?")
        return float(val_str.split(",")[0])
