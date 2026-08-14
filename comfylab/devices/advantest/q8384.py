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

from comfylab.devices.base import BaseInstrumentDriver, extract_float, extract_floats


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

    def sweep(self, mode: str = "REPEAT", wait: bool = False) -> None:
        """
        Controls the Advantest OSA sweep mode.

        :param mode: 'REPEAT' (continuous), 'SINGLE' (one-shot), or 'STOP' (stop sweep).
        :param wait: If True and mode is 'SINGLE', blocks until sweep completion (*WAI).
        """
        mode_upper = mode.upper()
        if mode_upper in ("REPEAT", "CONTINUOUS"):
            self.write("SR")
        elif mode_upper == "SINGLE":
            self.write("SI")
            if wait:
                self.write("*WAI")
        elif mode_upper == "STOP":
            self.write("ST")

    def get_trace(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fetches wavelength array (nm) and optical power trace array (dBm) directly from OSA memory.
        Does not trigger a sweep or block for sweep completion.
        """
        # Query center and span for frequency axis generation
        cnt_str = self.query("CNT?")
        span_str = self.query("SPAN?")
        cnt = extract_float(cnt_str, default=1550.0)
        span = extract_float(span_str, default=20.0)
        start_nm = cnt - (span / 2.0)
        stop_nm = cnt + (span / 2.0)

        # Query trace data
        raw_res = self.query("LDAT")
        vals = extract_floats(raw_res)
        power_array = np.array(vals, dtype=float)

        point_count = len(power_array)
        if point_count > 1:
            wavelength_array = np.linspace(start_nm, stop_nm, point_count)
        else:
            wavelength_array = np.array([start_nm])

        return wavelength_array, power_array

    def acquire_trace(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fetches wavelength array (nm) and power array (dBm) directly from OSA memory without triggering a sweep.
        """
        return self.get_trace()

    def sweep_and_acquire(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Triggers a single sweep, waits for completion, and fetches the trace data.
        """
        self.sweep(mode="SINGLE", wait=True)
        return self.get_trace()

