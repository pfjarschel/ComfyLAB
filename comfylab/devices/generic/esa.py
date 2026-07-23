# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Generic SCPI Electrical Spectrum Analyzer (ESA) Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Tuple, Optional
import numpy as np

from comfylab.devices.base import BaseInstrumentDriver, parse_ieee_block


class GenericESA(BaseInstrumentDriver):
    """
    Driver for SCPI-compliant Electrical Spectrum Analyzers (Agilent/Keysight, Rigol, Rohde & Schwarz, Anritsu).
    """

    def set_frequency(
        self,
        center: Optional[float] = None,
        span: Optional[float] = None,
        start: Optional[float] = None,
        stop: Optional[float] = None
    ) -> None:
        """Sets frequency sweep boundaries in Hz."""
        if center is not None:
            self.write(f":FREQuency:CENTer {center}")
        if span is not None:
            self.write(f":FREQuency:SPAN {span}")
        if start is not None:
            self.write(f":FREQuency:STARt {start}")
        if stop is not None:
            self.write(f":FREQuency:STOP {stop}")

    def set_bandwidth(
        self,
        rbw: Optional[float] = None,
        vbw: Optional[float] = None,
        auto_rbw: bool = True
    ) -> None:
        """Configures Resolution Bandwidth (RBW) and Video Bandwidth (VBW) in Hz."""
        if auto_rbw:
            self.write(":BANDwidth:RESolution:AUTO ON")
        elif rbw is not None:
            self.write(f":BANDwidth:RESolution {rbw}")

        if vbw is not None:
            self.write(f":BANDwidth:VIDeo {vbw}")

    def set_sweep(self, points: Optional[int] = None, single: bool = False) -> None:
        """Configures sweep point count and single/continuous sweep mode."""
        if points is not None:
            self.write(f":SWEep:POINts {int(points)}")
        if single:
            self.write(":INITiate:CONTinuous OFF")
        else:
            self.write(":INITiate:CONTinuous ON")

    def acquire_trace(self, trace_num: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Triggers a sweep (if in single mode) and fetches frequency array (Hz) and power trace array (dBm).
        """
        # Fetch start, stop, and point count for frequency axis generation
        try:
            f_start = float(self.query(":FREQuency:STARt?"))
            f_stop = float(self.query(":FREQuency:STOP?"))
        except Exception:
            f_center = float(self.query(":FREQuency:CENTer?"))
            f_span = float(self.query(":FREQuency:SPAN?"))
            f_start = f_center - (f_span / 2.0)
            f_stop = f_center + (f_span / 2.0)

        # Trigger single sweep if in single mode
        try:
            is_cont = self.query(":INITiate:CONTinuous?")
            if is_cont.strip() in ("0", "OFF"):
                self.write(":INITiate:IMMediate")
                self.write("*WAI")
        except Exception:
            pass

        # Query trace data
        raw_res = self.query(f":TRACe:DATA? TRACE{trace_num}")
        
        # Parse comma-separated or space-separated ASCII float numbers
        clean_str = raw_res.replace(";", ",").replace(" ", ",")
        vals = [float(v) for v in clean_str.split(",") if v.strip()]
        power_array = np.array(vals, dtype=float)

        point_count = len(power_array)
        if point_count > 1:
            freq_array = np.linspace(f_start, f_stop, point_count)
        else:
            freq_array = np.array([f_start])

        return freq_array, power_array
