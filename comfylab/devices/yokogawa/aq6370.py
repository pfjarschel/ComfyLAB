# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Yokogawa / Ando AQ6370 Series Optical Spectrum Analyzer (OSA) Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Tuple, Optional
import numpy as np

from comfylab.devices.base import BaseInstrumentDriver


class AQ6370(BaseInstrumentDriver):
    """
    Driver for Yokogawa / Ando AQ6370, AQ6370B, AQ6370D, AQ6375, and AQ6317 Optical Spectrum Analyzers.
    Communicates via VISA GPIB or Ethernet TCPIP using SCPI commands.
    """

    def set_sweep_config(
        self,
        center_nm: Optional[float] = None,
        span_nm: Optional[float] = None,
        rbw_nm: Optional[float] = None,
        sens: Optional[str] = None
    ) -> None:
        """Configures center wavelength (nm), span (nm), resolution RBW (nm), and sensitivity."""
        if center_nm is not None:
            self.write(f":SENSe:WAVelength:CENTer {center_nm}NM")
        if span_nm is not None:
            self.write(f":SENSe:WAVelength:SPAN {span_nm}NM")
        if rbw_nm is not None:
            self.write(f":SENSe:BANDwidth:RESolution {rbw_nm}NM")
        if sens is not None:
            self.write(f":SENSe:SWEep:SENSitivity {sens.upper()}")

    def acquire_trace(self, trace_name: str = "TRA") -> Tuple[np.ndarray, np.ndarray]:
        """
        Triggers a single sweep, waits for completion, and fetches wavelength array (nm) and optical power array (dBm).
        """
        # Trigger single sweep
        self.write(":INITiate:SMODe SINGle")
        self.write(":INITiate:IMMediate")
        self.write("*WAI")

        # Fetch wavelength X-axis array (nm)
        x_str = self.query(f":TRACe:X? {trace_name.upper()}")
        # Fetch power Y-axis array (dBm)
        y_str = self.query(f":TRACe:Y? {trace_name.upper()}")

        x_vals = [float(v) for v in x_str.replace(";", ",").split(",") if v.strip()]
        y_vals = [float(v) for v in y_str.replace(";", ",").split(",") if v.strip()]

        wavelength_nm = np.array(x_vals, dtype=float)
        # Yokogawa returns wavelengths in meters or nm depending on header config. Normalize if in meters (< 1e-3).
        if len(wavelength_nm) > 0 and wavelength_nm[0] < 1.0:
            wavelength_nm = wavelength_nm * 1e9

        power_dbm = np.array(y_vals, dtype=float)

        return wavelength_nm, power_dbm
