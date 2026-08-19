# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Agilent / Keysight 33220A 20 MHz Function / Arbitrary Waveform Generator Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Dict, Optional
from comfylab.devices.base import BaseInstrumentDriver, extract_float


class Agilent33220A(BaseInstrumentDriver):
    """
    Driver for Agilent / Keysight 33220A (and 33210A / 33250A) 20 MHz Function Generator.
    Supports Sine, Square, Ramp, Triangle, Pulse, Noise, DC, Sweeps, and Burst.
    Communicates via VISA USB TMC, GPIB, or LAN interfaces.
    """

    def __init__(self, visa_device: Any):
        super().__init__(visa_device)
        try:
            self.device.timeout = 5000
        except Exception:
            pass

    def set_wave(
        self,
        shape: Optional[str] = "SIN",
        frequency: Optional[float] = None,
        amplitude: Optional[float] = None,
        offset: Optional[float] = None,
        duty_or_sym: Optional[float] = None
    ) -> None:
        """
        Configures output waveform shape, frequency (Hz), amplitude (Vpp), offset (V), and duty/symmetry (%).
        """
        if shape is not None:
            s_up = shape.upper()
            if s_up in ("SIN", "SINE", "SINUSOID"):
                f_str = "SIN"
            elif s_up in ("SQU", "SQUARE"):
                f_str = "SQU"
            elif s_up in ("RAMP", "TRIANGLE", "TRI"):
                f_str = "RAMP"
            elif s_up in ("PULS", "PULSE"):
                f_str = "PULS"
            elif s_up in ("NOIS", "NOISE"):
                f_str = "NOIS"
            elif s_up in ("DC",):
                f_str = "DC"
            else:
                f_str = s_up
            self.write(f"FUNCtion {f_str}")

        if frequency is not None:
            self.write(f"FREQuency {frequency}")

        if amplitude is not None:
            self.write(f"VOLTage {amplitude}")

        if offset is not None:
            self.write(f"VOLTage:OFFSet {offset}")

        if duty_or_sym is not None:
            if shape and shape.upper() in ("SQU", "SQUARE"):
                self.write(f"FUNCtion:SQUare:DCYCle {duty_or_sym}")
            elif shape and shape.upper() in ("RAMP", "TRIANGLE", "TRI"):
                self.write(f"FUNCtion:RAMP:SYMMetry {duty_or_sym}")

    def set_pulse(
        self,
        period: Optional[float] = None,
        width: Optional[float] = None,
        transition: Optional[float] = None
    ) -> None:
        """Configures pulse parameters: period (s), width (s), and edge transition time (s)."""
        self.write("FUNCtion PULSe")
        if period is not None:
            self.write(f"PULSe:PERiod {period}")
        if width is not None:
            self.write(f"PULSe:WIDTh {width}")
        if transition is not None:
            self.write(f"PULSe:TRANsition {transition}")

    def set_output(
        self,
        enable: bool = True,
        load: Optional[str] = "50",
        inverted: bool = False
    ) -> None:
        """
        Enables or disables output state. Optionally sets load impedance ('50' or 'INF') and polarity.
        """
        if load is not None:
            load_val = "INFinity" if str(load).upper() in ("INF", "INFINITY", "HZ", "HIGHZ") else "50"
            self.write(f"OUTPut:LOAD {load_val}")

        pol_str = "INVerted" if inverted else "NORMal"
        self.write(f"OUTPut:POLarity {pol_str}")

        state = "ON" if enable else "OFF"
        self.write(f"OUTPut {state}")

    def set_sweep(
        self,
        start_freq: Optional[float] = None,
        stop_freq: Optional[float] = None,
        sweep_time: Optional[float] = None,
        spacing: str = "LIN",
        enable: bool = True
    ) -> None:
        """Configures frequency sweep mode."""
        if start_freq is not None:
            self.write(f"FREQuency:STARt {start_freq}")
        if stop_freq is not None:
            self.write(f"FREQuency:STOP {stop_freq}")
        if sweep_time is not None:
            self.write(f"SWEep:TIME {sweep_time}")
        sp_str = "LOGarithmic" if spacing.upper() in ("LOG", "LOGARITHMIC") else "LINear"
        self.write(f"SWEep:SPACing {sp_str}")
        st_str = "ON" if enable else "OFF"
        self.write(f"SWEep:STATe {st_str}")

    def set_burst(
        self,
        enable: bool = True,
        ncycles: int = 1,
        phase: float = 0.0
    ) -> None:
        """Configures burst mode."""
        if enable:
            self.write(f"BURSt:NCYCles {int(ncycles)}")
            self.write(f"BURSt:PHASe {phase}")
            self.write("BURSt:STATe ON")
        else:
            self.write("BURSt:STATe OFF")
