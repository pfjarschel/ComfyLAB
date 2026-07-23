# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Generic SCPI Digital Multimeter (DMM) Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Optional
from comfylab.devices.base import BaseInstrumentDriver


class GenericDMM(BaseInstrumentDriver):
    """
    Driver for SCPI-compliant Digital Multimeters (Keysight 34401A/34461A, Keithley 2000, Fluke, Rigol).
    """

    def configure(
        self,
        function_mode: str = "VOLT:DC",
        range_val: Optional[float] = None,
        resolution: Optional[float] = None,
        nplc: Optional[float] = None
    ) -> None:
        """Configures measurement function mode (VOLT:DC, VOLT:AC, CURR:DC, CURR:AC, RES, FRES)."""
        mode_upper = function_mode.upper()
        
        # Build CONFigure string
        cmd = f":CONFigure:{mode_upper}"
        if range_val is not None:
            cmd += f" {range_val}"
            if resolution is not None:
                cmd += f",{resolution}"
        self.write(cmd)

        if nplc is not None:
            # Set integration aperture in Number of Power Line Cycles
            base_func = mode_upper.split(":")[0]
            self.write(f":SENS:{base_func}:NPLC {nplc}")

    def read_measurement(self) -> float:
        """Triggers a measurement and returns float reading."""
        val_str = self.query(":READ?")
        return float(val_str.split(",")[0])

    def fetch_measurement(self) -> float:
        """Fetches last completed measurement from buffer."""
        val_str = self.query(":FETCh?")
        return float(val_str.split(",")[0])
