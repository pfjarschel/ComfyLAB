# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Keithley 2231A-30-3 Triple-Channel DC Power Supply Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Dict, Optional, Tuple
from comfylab.devices.base import BaseInstrumentDriver, extract_float


class Keithley2231A(BaseInstrumentDriver):
    """
    Driver for Keithley 2231A-30-3 Triple-Channel DC Power Supply (and 2220/2230 series).
    Channels:
      - CH1: 0 - 30 V, 0 - 3 A
      - CH2: 0 - 30 V, 0 - 3 A
      - CH3: 0 - 5 V,  0 - 3 A
    Communicates via VISA USB TMC, Virtual COM Serial, or GPIB interfaces.
    """

    def __init__(self, visa_device: Any):
        super().__init__(visa_device)
        try:
            self.device.timeout = 5000
        except Exception:
            pass

    def select_channel(self, channel: int = 1) -> None:
        """Selects active channel (1, 2, or 3)."""
        if channel not in (1, 2, 3):
            raise ValueError(f"Invalid channel: {channel}. Keithley 2231A supports channels 1, 2, or 3.")
        self.write(f"INSTrument:SELect CH{channel}")

    def set_channel(
        self,
        channel: int = 1,
        voltage: Optional[float] = None,
        current_limit: Optional[float] = None
    ) -> None:
        """
        Configures voltage setpoint (V) and current limit (A) for the specified channel (1, 2, or 3).
        """
        if channel not in (1, 2, 3):
            raise ValueError(f"Invalid channel: {channel}. Keithley 2231A supports channels 1, 2, or 3.")

        self.select_channel(channel)

        if voltage is not None:
            # Channel 3 is max 5V, Channels 1 & 2 are max 30V
            max_v = 5.0 if channel == 3 else 30.0
            v_clamped = max(0.0, min(float(voltage), max_v))
            self.write(f"VOLTage {v_clamped:.4f}")

        if current_limit is not None:
            c_clamped = max(0.0, min(float(current_limit), 3.0))
            self.write(f"CURRent {c_clamped:.4f}")

    def set_output(self, enable: bool = True, channel: Optional[int] = None) -> None:
        """
        Enables or disables output.
        If channel is specified, attempts channel-specific output toggle if supported,
        otherwise controls global output state.
        """
        state = "ON" if enable else "OFF"
        if channel is not None and channel in (1, 2, 3):
            try:
                self.write(f"CHANnel:OUTPut CH{channel},{state}")
                return
            except Exception:
                pass
        self.write(f"OUTPut:STATe {state}")

    def measure_voltage(self, channel: int = 1) -> float:
        """Measures output voltage (V) on specified channel (1, 2, or 3)."""
        if channel not in (1, 2, 3):
            raise ValueError(f"Invalid channel: {channel}. Must be 1, 2, or 3.")
        
        try:
            val_str = self.query(f"MEASure:VOLTage? CH{channel}")
            return extract_float(val_str, default=0.0)
        except Exception:
            self.select_channel(channel)
            val_str = self.query("MEASure:VOLTage?")
            return extract_float(val_str, default=0.0)

    def measure_current(self, channel: int = 1) -> float:
        """Measures output current (A) on specified channel (1, 2, or 3)."""
        if channel not in (1, 2, 3):
            raise ValueError(f"Invalid channel: {channel}. Must be 1, 2, or 3.")
        
        try:
            val_str = self.query(f"MEASure:CURRent? CH{channel}")
            return extract_float(val_str, default=0.0)
        except Exception:
            self.select_channel(channel)
            val_str = self.query("MEASure:CURRent?")
            return extract_float(val_str, default=0.0)

    def measure_all(self) -> Dict[str, Tuple[float, float]]:
        """
        Reads output voltage and current for all 3 channels.
        Returns dictionary: {'CH1': (v1, i1), 'CH2': (v2, i2), 'CH3': (v3, i3)}.
        """
        results = {}
        for ch in (1, 2, 3):
            v = self.measure_voltage(ch)
            i = self.measure_current(ch)
            results[f"CH{ch}"] = (v, i)
        return results

    def set_tracking_mode(self, mode: str = "INDEPENDENT") -> None:
        """
        Sets tracking mode for CH1 and CH2:
        'INDEPENDENT' (None/0), 'SERIES' (Series/1), or 'PARALLEL' (Parallel/2).
        """
        mode_upper = mode.upper()
        if mode_upper in ("SERIES", "SER"):
            self.write("OUTPut:TRACk SERies")
        elif mode_upper in ("PARALLEL", "PAR"):
            self.write("OUTPut:TRACk PARallel")
        else:
            self.write("OUTPut:TRACk NONE")
