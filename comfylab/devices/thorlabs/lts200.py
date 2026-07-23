# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Thorlabs LTS200 / LTS300 Integrated Linear Stage Driver.
Pure Python — no ComfyLAB UI or block dependencies.
Communicates over Virtual COM / ASRL VISA resources.
"""

from typing import Any, Optional
from comfylab.devices.base import BaseInstrumentDriver


class ThorlabsLTS200(BaseInstrumentDriver):
    """
    Driver for Thorlabs LTS200 / LTS300 linear translation stages over VISA ASRL / Serial.
    """

    def move_absolute(self, position_mm: float) -> None:
        """Moves stage to absolute position in millimeters (mm)."""
        self.write(f"ma {position_mm}")

    def move_relative(self, distance_mm: float) -> None:
        """Moves stage relatively by distance in millimeters (mm)."""
        self.write(f"mr {distance_mm}")

    def home(self) -> None:
        """Triggers stage homing sequence."""
        self.write("home")

    def get_position(self) -> float:
        """Queries current stage position in millimeters (mm)."""
        res_str = self.query("pos")
        clean_val = res_str.replace("pos", "").strip()
        return float(clean_val)
