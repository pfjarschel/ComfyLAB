# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Pure-Python, headless Virtual RC Circuit complying with standard SCPI commands.
Port: 51236
IDN: ComfyLAB,Virtual RC Circuit,VRC1,1.0.0
"""

import numpy as np
from scipy import signal
from typing import List, Optional, Any
from comfylab.virtual.scpi_base import VirtualSCPIInstrument


class VirtualRCCircuit(VirtualSCPIInstrument):
    """
    Headless RC circuit simulation.
    Calculates filtered capacitor or resistor output on demand.
    Default parameters: R = 1000 Ohms, C = 0.1 uF (cutoff freq approx 1591.55 Hz).
    """

    def __init__(self, port: int = 51236, name: str = "Virtual RC Circuit", verbose: bool = False):
        super().__init__(port=port, name=name, verbose=verbose)

        self.resistance: float = 1000.0   # Ohms
        self.capacitance: float = 0.1     # uF (microfarads)
        self.output_mode: str = "C"       # 'C' = capacitor output, 'R' = resistor output
        self._input_source = None

        self._register_handlers()

    def get_idn(self) -> str:
        return "ComfyLAB,Virtual RC Circuit,VRC1,1.0.0"

    def reset(self) -> None:
        self.resistance = 1000.0
        self.capacitance = 0.1
        self.output_mode = "C"

    def set_input_source(self, source: Any) -> None:
        """Sets the upstream signal generator feeding this RC circuit."""
        self._input_source = source

    def _register_handlers(self) -> None:
        # SCPI commands
        self.register_command("resistance", self._set_r)
        self.register_query("resistance?", lambda args: f"{self.resistance:.6e}")
        self.register_command("capacitance", self._set_c)
        self.register_query("capacitance?", lambda args: f"{self.capacitance:.6e}")
        self.register_command("output", self._set_out)
        self.register_query("output?", lambda args: self.output_mode)

        # Legacy SimVISA compatibility
        self.register_command("r", self._set_r)
        self.register_query("r?", lambda args: f"{self.resistance}")
        self.register_command("c", self._set_c)
        self.register_query("c?", lambda args: f"{self.capacitance}")
        self.register_command("out", self._set_out)
        self.register_query("out?", lambda args: self.output_mode)

    def _set_r(self, args: List[str]) -> None:
        if args:
            try:
                self.resistance = max(1e-3, float(args[0]))
            except ValueError:
                pass

    def _set_c(self, args: List[str]) -> None:
        if args:
            try:
                self.capacitance = max(1e-6, float(args[0]))
            except ValueError:
                pass

    def _set_out(self, args: List[str]) -> None:
        if args:
            val = args[0].strip().upper()
            if val in ("C", "CAP", "CAPACITOR"):
                self.output_mode = "C"
            elif val in ("R", "RES", "RESISTOR"):
                self.output_mode = "R"

    def calculate_signal(self, v_in: np.ndarray, t_array: np.ndarray) -> np.ndarray:
        """
        Calculates the RC circuit output given input voltage vector v_in across time t_array.
        Calculates on demand using an exact discrete IIR filter with pre-roll
        to eliminate artificial transient warmup.
        """
        n = len(t_array)
        if n == 0 or len(v_in) == 0:
            return np.zeros_like(t_array)

        # Time constant tau = R * C (in seconds, capacitance is in uF)
        tau = self.resistance * (self.capacitance * 1e-6)
        if tau <= 0:
            tau = 1e-6

        dt = (t_array[-1] - t_array[0]) / max(1, n - 1)
        if dt <= 0:
            dt = 1e-5

        # Discrete lowpass filter coefficient: alpha = dt / (tau + dt)
        alpha = dt / (tau + dt)
        b = [alpha]
        a = [1.0, -(1.0 - alpha)]

        # Pre-roll padding to settle steady-state filter response (at least 5 * tau or 1 full window)
        settle_points = min(max(int(5.0 * tau / dt), 50), n * 2)
        if len(v_in) >= 2:
            # Replicate initial periodic segment as pre-roll
            pad = np.tile(v_in, int(np.ceil(settle_points / len(v_in))))[:settle_points]
        else:
            pad = np.full(settle_points, v_in[0])

        extended_v = np.concatenate([pad, v_in])
        # Filter: V_c is the low-pass capacitor voltage
        filtered_extended = signal.lfilter(b, a, extended_v)
        v_c = filtered_extended[settle_points:]

        if self.output_mode == "R":
            # Voltage across resistor: V_r = V_in - V_c
            return v_in - v_c
        return v_c
