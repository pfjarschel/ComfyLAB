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

from comfylab.devices.base import BaseInstrumentDriver, extract_floats


class AQ6370(BaseInstrumentDriver):
    """
    Driver for Yokogawa / Ando AQ6370, AQ6370B, AQ6370D, AQ6375, and AQ6317 Optical Spectrum Analyzers.
    Communicates via VISA GPIB or Ethernet TCPIP using SCPI commands.
    """

    ALL_TRACES = ["TRA", "TRB", "TRC", "TRD", "TRE", "TRF", "TRG"]

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

    def sweep(
        self,
        mode: str = "REPEAT",
        active_trace: str = "TRA",
        fix_other_traces: bool = True,
        wait: bool = False
    ) -> None:
        """
        Controls the OSA sweep execution and active trace states.

        :param mode: 'REPEAT' (continuous), 'SINGLE' (one-shot), or 'STOP' (abort sweep).
        :param active_trace: Active trace for the sweep ('TRA' through 'TRG').
        :param fix_other_traces: If True, sets active_trace to WRITE state and fixes all other traces.
        :param wait: If True and mode is 'SINGLE', blocks until sweep completion (*WAI).
        """
        mode_upper = mode.upper()
        active = active_trace.upper()

        if fix_other_traces:
            for t in self.ALL_TRACES:
                if t == active:
                    self.write(f":TRACe:STATe:{t} WRITe")
                else:
                    self.write(f":TRACe:STATe:{t} FIXed")

        if mode_upper in ("REPEAT", "CONTINUOUS"):
            self.write(":INITiate:SMODe REPEAT")
            self.write(":INITiate:IMMediate")
        elif mode_upper == "SINGLE":
            self.write(":INITiate:SMODe SINGle")
            self.write(":INITiate:IMMediate")
            if wait:
                self.write("*WAI")
        elif mode_upper == "STOP":
            self.write(":ABORt")

    def get_trace(self, trace_name: str = "TRA") -> Tuple[np.ndarray, np.ndarray]:
        """
        Fetches wavelength array (nm) and optical power array (dBm) for the specified trace directly from OSA memory.
        Does not trigger a sweep or block for sweep completion.
        """
        t_name = trace_name.upper()
        x_str = self.query(f":TRACe:X? {t_name}")
        y_str = self.query(f":TRACe:Y? {t_name}")

        x_vals = extract_floats(x_str)
        y_vals = extract_floats(y_str)

        wavelength_nm = np.array(x_vals, dtype=float)
        # Yokogawa returns wavelengths in meters or nm depending on header config. Normalize if in meters (< 1e-3).
        if len(wavelength_nm) > 0 and wavelength_nm[0] < 1.0:
            wavelength_nm = wavelength_nm * 1e9

        power_dbm = np.array(y_vals, dtype=float)

        return wavelength_nm, power_dbm

    def acquire_trace(self, trace_name: str = "TRA") -> Tuple[np.ndarray, np.ndarray]:
        """
        Fetches wavelength array (nm) and power array (dBm) directly from OSA memory without triggering a new sweep.
        """
        return self.get_trace(trace_name)

    def sweep_and_acquire(self, trace_name: str = "TRA") -> Tuple[np.ndarray, np.ndarray]:
        """
        Triggers a single sweep, waits for completion, and fetches the trace data.
        """
        self.sweep(mode="SINGLE", active_trace=trace_name, fix_other_traces=False, wait=True)
        return self.get_trace(trace_name)

