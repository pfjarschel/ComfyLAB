# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Agilent E4407B / E4400 Series Electrical Spectrum Analyzer (ESA) Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Tuple, Optional
import numpy as np

from comfylab.devices.base import BaseInstrumentDriver, parse_ieee_block


class AgilentE4407B(BaseInstrumentDriver):
    """
    Driver for Agilent E4407B and ESA-E / ESA-L series spectrum analyzers (9 kHz - 26.5 GHz).
    """

    def set_frequency(
        self,
        center_hz: Optional[float] = None,
        span_hz: Optional[float] = None,
        start_hz: Optional[float] = None,
        stop_hz: Optional[float] = None
    ) -> None:
        """Sets frequency sweep center, span, start, and stop in Hz."""
        if center_hz is not None:
            self.write(f":SENSe:FREQuency:CENTer {center_hz}")
        if span_hz is not None:
            self.write(f":SENSe:FREQuency:SPAN {span_hz}")
        if start_hz is not None:
            self.write(f":SENSe:FREQuency:STARt {start_hz}")
        if stop_hz is not None:
            self.write(f":SENSe:FREQuency:STOP {stop_hz}")

    def set_bandwidth(self, rbw_hz: Optional[float] = None, vbw_hz: Optional[float] = None) -> None:
        """Configures Resolution Bandwidth (RBW) and Video Bandwidth (VBW) in Hz."""
        if rbw_hz is not None:
            self.write(f":SENSe:BANDwidth:RESolution {rbw_hz}")
        if vbw_hz is not None:
            self.write(f":SENSe:BANDwidth:VIDeo {vbw_hz}")

    def set_attenuation(self, attenuation_db: float = 10.0, auto: bool = True) -> None:
        """Configures RF attenuation in dB."""
        if auto:
            self.write(":SENSe:POWer:RF:ATTenuation:AUTO ON")
        else:
            self.write(f":SENSe:POWer:RF:ATTenuation {attenuation_db}")

    def acquire_trace(self, trace_num: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Queries trace data (Trace 1, 2, or 3) and computes frequency array (Hz) and power array (dBm).
        """
        self.write(":UNIT:POWer DBM")
        self.write(":FORMat:DATA ASCII")

        f_start = float(self.query(":SENSe:FREQuency:STARt?"))
        f_stop = float(self.query(":SENSe:FREQuency:STOP?"))

        raw_res = self.query(f":TRACe:DATA? TRACE{trace_num}")
        vals = [float(v) for v in raw_res.replace(";", ",").split(",") if v.strip()]
        power_array = np.array(vals, dtype=float)

        point_count = len(power_array)
        if point_count > 1:
            freq_array = np.linspace(f_start, f_stop, point_count)
        else:
            freq_array = np.array([f_start])

        return freq_array, power_array
