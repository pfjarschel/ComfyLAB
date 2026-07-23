# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
HP / Agilent 34401A 6½ Digit Multimeter Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Optional
import numpy as np
from comfylab.devices.base import BaseInstrumentDriver


class HP34401A(BaseInstrumentDriver):
    """
    Driver for HP / Agilent 34401A 6½ digit multimeter over VISA GPIB / RS-232.
    """

    def configure(
        self,
        mode: str = "VOLT:DC",
        range_val: Optional[float] = None,
        resolution: Optional[float] = None,
        nplc: Optional[float] = 1.0
    ) -> None:
        """Configures measurement mode (VOLT:DC, VOLT:AC, CURR:DC, CURR:AC, RES, FRES)."""
        mode_upper = mode.upper()
        cmd = f"CONF:{mode_upper}"
        if range_val is not None:
            cmd += f" {range_val}"
            if resolution is not None:
                cmd += f",{resolution}"
        self.write(cmd)

        if nplc is not None:
            base_func = mode_upper.split(":")[0]
            self.write(f":SENS:{base_func}:NPLC {nplc}")

    def read_voltage_dc(self) -> float:
        """Reads DC Voltage in Volts."""
        self.write("CONF:VOLT:DC")
        self.write("INIT")
        res_str = self.query("FETC?")
        vals = [float(v) for v in res_str.split(",") if v.strip()]
        return float(np.mean(vals)) if len(vals) > 0 else 0.0

    def read_current_dc(self) -> float:
        """Reads DC Current in Amperes."""
        self.write("CONF:CURR:DC")
        self.write("INIT")
        res_str = self.query("FETC?")
        vals = [float(v) for v in res_str.split(",") if v.strip()]
        return float(np.mean(vals)) if len(vals) > 0 else 0.0

    def read_measurement(self) -> float:
        """Triggers and reads single measurement value."""
        res_str = self.query("READ?")
        return float(res_str.split(",")[0])
