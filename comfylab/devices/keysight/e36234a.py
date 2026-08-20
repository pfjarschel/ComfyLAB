# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Keysight E36234A Dual-Output Autoranging DC Power Supply Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Dict, Optional, Tuple
from comfylab.devices.base import BaseInstrumentDriver, extract_float


class KeysightE36234A(BaseInstrumentDriver):
    """
    Driver for Keysight E36234A (and E36200 / E36300 Series) Dual-Output Autoranging DC Power Supply.
    Channels:
      - CH1: 0 - 60 V, 0 - 10 A, 200 W max autoranging
      - CH2: 0 - 60 V, 0 - 10 A, 200 W max autoranging
    Features: Auto-series and auto-parallel pairing, over-voltage/current protection, low-range current readback.
    Communicates via VISA USB TMC, TCPIP LAN / LXI, or GPIB interfaces.
    """

    def __init__(self, visa_device: Any):
        super().__init__(visa_device)
        try:
            self.device.timeout = 5000
        except Exception:
            pass

    def select_channel(self, channel: int = 1) -> None:
        """Selects active channel (1 or 2)."""
        if channel not in (1, 2):
            raise ValueError(f"Invalid channel: {channel}. Keysight E36234A supports channel 1 or 2.")
        try:
            self.write(f"INSTrument:SELect OUTPut{channel}")
        except Exception:
            self.write(f"INSTrument:NSELect {channel}")

    def set_channel(
        self,
        channel: int = 1,
        voltage: Optional[float] = None,
        current_limit: Optional[float] = None
    ) -> None:
        """
        Configures voltage setpoint (V) and current limit (A) for channel 1 or 2.
        Supports autoranging parameters up to 60V / 10A (200W).
        """
        if channel not in (1, 2):
            raise ValueError(f"Invalid channel: {channel}. Keysight E36234A supports channel 1 or 2.")

        ch_spec = f"(@{channel})"

        if voltage is not None:
            v_clamped = max(0.0, min(float(voltage), 60.0))
            try:
                self.write(f"VOLTage {v_clamped:.4f}, {ch_spec}")
            except Exception:
                self.select_channel(channel)
                self.write(f"VOLTage {v_clamped:.4f}")

        if current_limit is not None:
            c_clamped = max(0.0, min(float(current_limit), 10.0))
            try:
                self.write(f"CURRent {c_clamped:.4f}, {ch_spec}")
            except Exception:
                self.select_channel(channel)
                self.write(f"CURRent {c_clamped:.4f}")

    def set_output(self, enable: bool = True, channel: Optional[int] = None) -> None:
        """
        Enables or disables output state.
        If channel is None or 0, controls all outputs simultaneously.
        """
        state = "ON" if enable else "OFF"
        if channel is not None and channel in (1, 2):
            try:
                self.write(f"OUTPut:STATe {state}, (@{channel})")
                return
            except Exception:
                self.select_channel(channel)
                self.write(f"OUTPut:STATe {state}")
                return

        # Global toggle
        try:
            self.write(f"OUTPut:STATe {state}, (@1,2)")
        except Exception:
            self.write(f"OUTPut:STATe {state}")

    def set_protection(
        self,
        channel: int = 1,
        ovp_voltage: Optional[float] = None,
        ocp_enable: Optional[bool] = None
    ) -> None:
        """Configures Over-Voltage Protection (OVP) and Over-Current Protection (OCP)."""
        if channel not in (1, 2):
            raise ValueError(f"Invalid channel: {channel}. Must be 1 or 2.")

        ch_spec = f"(@{channel})"
        if ovp_voltage is not None:
            try:
                self.write(f"VOLTage:PROTection {float(ovp_voltage):.4f}, {ch_spec}")
                self.write(f"VOLTage:PROTection:STATe ON, {ch_spec}")
            except Exception:
                self.select_channel(channel)
                self.write(f"VOLTage:PROTection {float(ovp_voltage):.4f}")
                self.write("VOLTage:PROTection:STATe ON")

        if ocp_enable is not None:
            ocp_str = "ON" if ocp_enable else "OFF"
            try:
                self.write(f"CURRent:PROTection:STATe {ocp_str}, {ch_spec}")
            except Exception:
                self.select_channel(channel)
                self.write(f"CURRent:PROTection:STATe {ocp_str}")

    def set_pairing_mode(self, mode: str = "OFF") -> None:
        """
        Configures output pairing mode:
        'OFF' (Independent channels), 'SERIES' (Auto-series up to 120V / 10A), or 'PARALLEL' (Auto-parallel up to 60V / 20A).
        """
        m_up = mode.upper()
        if m_up in ("SERIES", "SER"):
            self.write("OUTPut:PAIR SERies")
        elif m_up in ("PARALLEL", "PAR"):
            self.write("OUTPut:PAIR PARallel")
        else:
            self.write("OUTPut:PAIR OFF")

    def measure_voltage(self, channel: int = 1) -> float:
        """Measures output voltage (V) on channel 1 or 2."""
        if channel not in (1, 2):
            raise ValueError(f"Invalid channel: {channel}. Must be 1 or 2.")

        try:
            val_str = self.query(f"MEASure:VOLTage:DC? (@{channel})")
            return extract_float(val_str, default=0.0)
        except Exception:
            self.select_channel(channel)
            val_str = self.query("MEASure:VOLTage:DC?")
            return extract_float(val_str, default=0.0)

    def measure_current(self, channel: int = 1) -> float:
        """Measures output current (A) on channel 1 or 2."""
        if channel not in (1, 2):
            raise ValueError(f"Invalid channel: {channel}. Must be 1 or 2.")

        try:
            val_str = self.query(f"MEASure:CURRent:DC? (@{channel})")
            return extract_float(val_str, default=0.0)
        except Exception:
            self.select_channel(channel)
            val_str = self.query("MEASure:CURRent:DC?")
            return extract_float(val_str, default=0.0)

    def measure_power(self, channel: int = 1) -> float:
        """Measures output power (W) on channel 1 or 2."""
        if channel not in (1, 2):
            raise ValueError(f"Invalid channel: {channel}. Must be 1 or 2.")

        try:
            val_str = self.query(f"MEASure:POWer:DC? (@{channel})")
            return extract_float(val_str, default=0.0)
        except Exception:
            v = self.measure_voltage(channel)
            i = self.measure_current(channel)
            return v * i

    def measure_all(self) -> Dict[str, Tuple[float, float, float]]:
        """
        Reads voltage (V), current (A), and power (W) for both channels.
        Returns: {'CH1': (v1, i1, p1), 'CH2': (v2, i2, p2)}.
        """
        results = {}
        for ch in (1, 2):
            v = self.measure_voltage(ch)
            i = self.measure_current(ch)
            p = v * i
            results[f"CH{ch}"] = (v, i, p)
        return results
