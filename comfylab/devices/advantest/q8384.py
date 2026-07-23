# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Advantest Q8384 Optical Spectrum Analyzer (OSA) Driver.
Pure Python — no ComfyLAB UI or block dependencies.
Modernized from legacy C++/Qt implementation.
"""

from typing import Any, Tuple, Optional
import numpy as np

from comfylab.devices.base import BaseInstrumentDriver


class AdvantestQ8384(BaseInstrumentDriver):
    """
    Driver for Advantest Q8384 High-Resolution Optical Spectrum Analyzer (OSA) over VISA GPIB.
    """

    def set_sweep_config(
        self,
        center_nm: Optional[float] = None,
        span_nm: Optional[float] = None,
        rbw_nm: Optional[float] = None
    ) -> None:
        """Configures center wavelength (nm), span (nm), and resolution (RBW nm)."""
        if center_nm is not None:
            self.write(f"CNT {center_nm}")
        if span_nm is not None:
            self.write(f"SPAN {span_nm}")
        if rbw_nm is not None:
            self.write(f"RESLN {rbw_nm}")

    def acquire_trace(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Triggers a single sweep and queries wavelength array (nm) and optical power trace array (dBm).
        """
        # Trigger single sweep and wait
        self.write("SI")
        self.write("*WAI")

        # Query center and span for frequency axis generation
        try:
            cnt_str = self.query("CNT?")
            span_str = self.query("SPAN?")
            cnt = float(cnt_str.split()[-1])
            span = float(span_str.split()[-1])
            start_nm = cnt - (span / 2.0)
            stop_nm = cnt + (span / 2.0)
        except Exception:
            start_nm = 1540.0
            stop_nm = 1560.0

        # Query trace data
        raw_res = self.query("LDAT")
        vals = [float(v) for v in raw_res.replace(";", ",").replace("\n", ",").split(",") if v.strip()]
        power_array = np.array(vals, dtype=float)

        point_count = len(power_array)
        if point_count > 1:
            wavelength_array = np.linspace(start_nm, stop_nm, point_count)
        else:
            wavelength_array = np.array([start_nm])

        return wavelength_array, power_array
