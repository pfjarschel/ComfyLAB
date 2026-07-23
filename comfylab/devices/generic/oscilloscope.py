# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Generic SCPI Oscilloscope Driver.
Pure Python — no ComfyLAB UI or block dependencies.
Supports standard IEEE 488.2 SCPI compliant oscilloscopes (Keysight, Rigol, Siglent, GW Instek, Rohde & Schwarz).
"""

from typing import Any, Tuple, Optional
import numpy as np

from comfylab.devices.base import BaseInstrumentDriver, parse_ieee_block


class GenericOscilloscope(BaseInstrumentDriver):
    """
    Driver for standard SCPI-compliant oscilloscopes over VISA (USB, TCPIP, GPIB).
    """

    def set_timebase(self, scale: Optional[float] = None, position: Optional[float] = None) -> None:
        """Sets horizontal timebase scale (seconds/div) and position offset."""
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
        """Configures channel vertical parameters (scale V/div, offset V, coupling, enable)."""
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel selection: {channel}. Must be 1-4.")
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
        Queries waveform points and computes horizontal time vector (s) and vertical voltage array (V).
        """
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel selection: {channel}. Must be 1-4.")

        self.write(f":WAVeform:SOURce CHANnel{channel}")
        self.write(":WAVeform:FORMat BYTE")

        # Query timebase scale & center
        try:
            t_scale = float(self.query(":TIMebase:SCALe?"))
        except Exception:
            t_scale = 0.001

        # Query raw binary curve
        raw_bytes = self.query_raw(":WAVeform:DATA?")
        payload = parse_ieee_block(raw_bytes)

        if not payload:
            return np.array([]), np.array([])

        raw_values = np.frombuffer(payload, dtype=np.uint8)
        point_count = len(raw_values)

        volts = (raw_values.astype(float) - 128.0) * (t_scale / 25.0)
        time_vec = np.linspace(-5.0 * t_scale, 5.0 * t_scale, point_count)

        return time_vec, volts
