# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Tektronix TBS1062 / TBS1000 Series Oscilloscope Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Tuple, Optional
import numpy as np

from comfylab.devices.base import BaseInstrumentDriver, parse_ieee_block


class TBS1062(BaseInstrumentDriver):
    """
    Driver for Tektronix TBS1062 and compatible TBS1000/TDS2000 series oscilloscopes.
    Communicates via VISA USB or GPIB interfaces.
    """

    def __init__(self, visa_device: Any):
        super().__init__(visa_device)
        try:
            self.device.timeout = 10000
            self.device.chunk_size = 40960
        except Exception:
            pass

    def set_timebase(self, scale: Optional[float] = None, position: Optional[float] = None) -> None:
        """Sets horizontal timebase scale (seconds/div) and position (offset)."""
        if scale is not None:
            self.write(f"HORizontal:MAIn:SCALE {scale}")
        if position is not None:
            self.write(f"HORizontal:MAIn:POSition {position}")

    def get_timebase_scale(self) -> float:
        """Returns horizontal timebase scale in seconds/div."""
        val = self.query("HORizontal:MAIn:SCALE?")
        return float(val.split()[-1])

    def set_channel(
        self,
        channel: int = 1,
        enable: Optional[bool] = None,
        scale: Optional[float] = None,
        position: Optional[float] = None,
        coupling: Optional[str] = None
    ) -> None:
        """Configures channel parameters (enable, vertical scale V/div, position, coupling)."""
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel number: {channel}. Must be 1-4.")
        
        chan_str = f"CH{channel}"
        if enable is not None:
            state = "ON" if enable else "OFF"
            self.write(f"SELECT:{chan_str} {state}")
        if scale is not None:
            self.write(f"{chan_str}:SCALE {scale}")
        if position is not None:
            self.write(f"{chan_str}:POSition {position}")
        if coupling is not None:
            self.write(f"{chan_str}:COUPling {coupling.upper()}")

    def set_trigger(
        self,
        mode: Optional[str] = None,
        source: Optional[str] = None,
        level: Optional[float] = None
    ) -> None:
        """Configures main trigger parameters."""
        if mode is not None:
            self.write(f"TRIGger:MAIn:MODE {mode.upper()}")
        if source is not None:
            self.write(f"TRIGger:MAIn:EDGE:SOURce {source.upper()}")
        if level is not None:
            self.write(f"TRIGger:MAIn:EDGE:LEVel {level}")

    def stop_acquisition(self) -> None:
        """Stops oscilloscope acquisition."""
        self.write("ACQuire:STATE STOP")

    def run_acquisition(self) -> None:
        """Starts oscilloscope acquisition."""
        self.write("ACQuire:STATE RUN")

    def acquire_waveform(self, channel: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Acquires vertical voltage waveform array and horizontal time vector for the selected channel.
        Queries preamble parameters (XINcr, XZERo, YMUlt, YOFF, YZERo) and decodes the binary byte payload.
        """
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel number: {channel}. Must be 1-4.")

        chan_str = f"CH{channel}"
        self.write(f"DATa:SOURce {chan_str}")
        self.write("DATa:ENCdg SRIbinary")  # Signed Ribinary 8-bit integer
        self.write("DATa:WIDth 1")          # 1 byte per sample
        self.write("DATa:STARt 1")
        self.write("DATa:STOP 2500")

        # Fetch waveform preamble scale factors
        x_incr = float(self.query("WFMPRe:XINcr?"))
        x_zero = float(self.query("WFMPRe:XZERo?"))
        y_mult = float(self.query("WFMPRe:YMUlt?"))
        y_off = float(self.query("WFMPRe:YOFF?"))
        y_zero = float(self.query("WFMPRe:YZERo?"))

        # Fetch binary curve data
        raw_bytes = self.query_raw("CURVe?")
        payload = parse_ieee_block(raw_bytes)

        if not payload:
            return np.array([]), np.array([])

        raw_values = np.frombuffer(payload, dtype=np.int8)

        volts = (raw_values.astype(float) - y_off) * y_mult + y_zero
        time_vec = (np.arange(len(raw_values)) * x_incr) + x_zero

        return time_vec, volts
