# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Stanford Research Systems SR830 / SR850 / SR860 Lock-In Amplifier Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Tuple, Optional
from comfylab.devices.base import BaseInstrumentDriver


class SR830(BaseInstrumentDriver):
    """
    Driver for Stanford Research Systems SR830, SR810, SR850, and SR860 Lock-In Amplifiers.
    Communicates via VISA GPIB or RS-232 serial.
    """

    def set_reference(
        self,
        frequency_hz: Optional[float] = None,
        phase_deg: Optional[float] = None,
        amplitude_v: Optional[float] = None
    ) -> None:
        """Sets internal reference frequency (Hz), phase shift (deg), and sine output amplitude (V)."""
        if frequency_hz is not None:
            self.write(f"FREQ {frequency_hz}")
        if phase_deg is not None:
            self.write(f"PHAS {phase_deg}")
        if amplitude_v is not None:
            self.write(f"SLVL {amplitude_v}")

    def read_ch1(self) -> float:
        """Reads Channel 1 output voltage (X component or R magnitude depending on display config)."""
        val_str = self.query("OUTP? 1")
        return float(val_str.split(",")[0])

    def read_ch2(self) -> float:
        """Reads Channel 2 output voltage (Y component or Phase angle depending on display config)."""
        val_str = self.query("OUTP? 2")
        return float(val_str.split(",")[0])

    def snap_all(self) -> Tuple[float, float, float, float]:
        """
        Queries simultaneous snapshot of X (V), Y (V), R magnitude (V), and Phase angle (deg).
        Uses SR830 SNAP? 1,2,3,4 command.
        """
        val_str = self.query("SNAP? 1,2,3,4")
        parts = [float(v) for v in val_str.split(",") if v.strip()]
        
        x = parts[0] if len(parts) > 0 else 0.0
        y = parts[1] if len(parts) > 1 else 0.0
        r = parts[2] if len(parts) > 2 else 0.0
        theta = parts[3] if len(parts) > 3 else 0.0

        return x, y, r, theta
