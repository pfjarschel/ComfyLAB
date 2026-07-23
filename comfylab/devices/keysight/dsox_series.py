# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Keysight InfiniiVision DSO-X 3000 / 1000 Series Oscilloscope Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Tuple, Optional
import numpy as np

from comfylab.devices.base import BaseInstrumentDriver, parse_ieee_block


class KeysightDSOX(BaseInstrumentDriver):
    """
    Driver for Keysight InfiniiVision DSO-X / MSO-X 1000, 2000, 3000, and 4000 Series Oscilloscopes.
    Communicates via VISA USBTMC, TCPIP LAN, or GPIB interfaces.
    """

    def __init__(self, visa_device: Any):
        super().__init__(visa_device)
        try:
            self.device.timeout = 10000
            self.device.chunk_size = 1048576  # 1 MB buffer for high-resolution waveforms
        except Exception:
            pass

    def set_timebase(self, scale: Optional[float] = None, position: Optional[float] = None) -> None:
        """Sets horizontal timebase scale (seconds/div) and position (delay offset)."""
        if scale is not None:
            self.write(f":TIMebase:SCALe {scale}")
        if position is not None:
            self.write(f":TIMebase:POSition {position}")

    def set_channel(
        self,
        channel: int = 1,
        enable: Optional[bool] = None,
        scale: Optional[float] = None,
        offset: Optional[float] = None,
        coupling: Optional[str] = None
    ) -> None:
        """Configures channel parameters (enable, vertical scale V/div, offset V, coupling AC/DC/GND)."""
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel number: {channel}. Must be 1-4.")
        
        ch_str = f":CHANnel{channel}"
        if enable is not None:
            state = "ON" if enable else "OFF"
            self.write(f"{ch_str}:DISPlay {state}")
        if scale is not None:
            self.write(f"{ch_str}:SCALe {scale}")
        if offset is not None:
            self.write(f"{ch_str}:OFFSet {offset}")
        if coupling is not None:
            self.write(f"{ch_str}:COUPling {coupling.upper()}")

    def acquire_waveform(self, channel: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Acquires vertical voltage waveform array (V) and horizontal time vector (s) for specified channel.
        Queries preamble parameters and parses WORD/BYTE binary payload.
        """
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel number: {channel}. Must be 1-4.")

        self.write(f":WAVeform:SOURce CHANnel{channel}")
        self.write(":WAVeform:FORMat WORD")
        self.write(":WAVeform:UNSigned 1")
        self.write(":WAVeform:BYTEorder MSBF")  # Most significant byte first

        # Query preamble: format, type, points, count, xincrement, xorigin, xreference, yincrement, yorigin, yreference
        pre_str = self.query(":WAVeform:PREamble?")
        pre_vals = [v.strip() for v in pre_str.split(",") if v.strip()]

        x_incr = float(pre_vals[4]) if len(pre_vals) > 4 else 1e-6
        x_orig = float(pre_vals[5]) if len(pre_vals) > 5 else 0.0
        x_ref  = float(pre_vals[6]) if len(pre_vals) > 6 else 0.0
        y_incr = float(pre_vals[7]) if len(pre_vals) > 7 else 0.01
        y_orig = float(pre_vals[8]) if len(pre_vals) > 8 else 0.0
        y_ref  = float(pre_vals[9]) if len(pre_vals) > 9 else 0.0

        # Query binary waveform data payload
        raw_bytes = self.query_raw(":WAVeform:DATA?")
        payload = parse_ieee_block(raw_bytes)

        if not payload:
            return np.array([]), np.array([])

        # 16-bit unsigned integers (big-endian >u2)
        raw_vals = np.frombuffer(payload, dtype=">u2")

        volts = (raw_vals.astype(float) - y_ref) * y_incr + y_orig
        time_vec = ((np.arange(len(raw_vals)) - x_ref) * x_incr) + x_orig

        return time_vec, volts
