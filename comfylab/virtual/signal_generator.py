# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Pure-Python, headless Virtual Signal Generator complying with standard SCPI commands.
Port: 51235
IDN: ComfyLAB,Virtual Signal Generator,VSG1,1.0.0
"""

import numpy as np
from typing import List, Optional
from comfylab.virtual.scpi_base import VirtualSCPIInstrument


class VirtualSignalGenerator(VirtualSCPIInstrument):
    """
    Headless Signal Generator instrument simulating standard waveform outputs.
    Calculates waveforms strictly on demand.
    """

    def __init__(self, port: int = 51235, name: str = "Virtual Signal Generator", verbose: bool = False):
        super().__init__(port=port, name=name, verbose=verbose)

        # Configurable Parameters
        self.frequency: float = 1000.0  # Hz
        self.amplitude: float = 2.0     # Vpp
        self.offset: float = 0.0        # V
        self.phase: float = 0.0         # Degrees
        self.duty_cycle: float = 50.0   # Percentage (0-100)
        self.wave_type: str = "SINUSOID"
        self.output_enabled: bool = True

        # Chirp parameters
        self.chirp_enabled: bool = False
        self.chirp_variation: float = 100.0  # %
        self.chirp_period: float = 1.0       # s

        # Noise and Jitter
        self.noise_enabled: bool = False
        self.noise_level: float = 0.005      # Vpp noise amplitude (5 mV default)
        self.jitter: float = 0.0             # Timing/phase jitter in seconds (e.g. 20e-12)

        self._register_handlers()

    def get_idn(self) -> str:
        return "ComfyLAB,Virtual Signal Generator,VSG1,1.0.0"

    def reset(self) -> None:
        self.frequency = 1000.0
        self.amplitude = 2.0
        self.offset = 0.0
        self.phase = 0.0
        self.duty_cycle = 50.0
        self.wave_type = "SINUSOID"
        self.output_enabled = True
        self.chirp_enabled = False
        self.chirp_variation = 100.0
        self.chirp_period = 1.0
        self.noise_enabled = False
        self.noise_level = 0.005
        self.jitter = 0.0

    def _register_handlers(self) -> None:
        # Standard SCPI :SOURce1:... commands
        self.register_command("source1:function", self._set_function)
        self.register_query("source1:function?", lambda args: self.wave_type)
        self.register_command("source1:frequency", self._set_frequency)
        self.register_query("source1:frequency?", lambda args: f"{self.frequency:.6e}")
        self.register_command("source1:voltage", self._set_voltage)
        self.register_query("source1:voltage?", lambda args: f"{self.amplitude:.6e}")
        self.register_command("source1:voltage:offset", self._set_offset)
        self.register_query("source1:voltage:offset?", lambda args: f"{self.offset:.6e}")
        self.register_command("source1:phase", self._set_phase)
        self.register_query("source1:phase?", lambda args: f"{self.phase:.2f}")
        self.register_command("source1:pulse:dcycle", self._set_duty_cycle)
        self.register_query("source1:pulse:dcycle?", lambda args: f"{self.duty_cycle:.2f}")

        # Chirp commands
        self.register_command("source1:frequency:chirp", self._set_chirp)
        self.register_query("source1:frequency:chirp?", lambda args: "1" if self.chirp_enabled else "0")
        self.register_command("source1:frequency:cvar", self._set_chirp_var)
        self.register_query("source1:frequency:cvar?", lambda args: f"{self.chirp_variation:.2f}")
        self.register_command("source1:frequency:cper", self._set_chirp_per)
        self.register_query("source1:frequency:cper?", lambda args: f"{self.chirp_period:.6f}")

        # Standard SCPI :OUTPut1:... commands
        self.register_command("output1:state", self._set_output)
        self.register_query("output1:state?", lambda args: "1" if self.output_enabled else "0")

        # Noise & Jitter commands
        self.register_command("source1:noise:state", self._set_noise_state)
        self.register_query("source1:noise:state?", lambda args: "1" if self.noise_enabled else "0")
        self.register_command("source1:noise:level", self._set_noise_level)
        self.register_query("source1:noise:level?", lambda args: f"{self.noise_level:.6e}")
        self.register_command("source1:jitter", self._set_jitter)
        self.register_query("source1:jitter?", lambda args: f"{self.jitter:.6e}")

        # Backward compatibility with legacy SimVISA commands
        self.register_command("wave:wave", self._set_function)
        self.register_query("wave:wave?", lambda args: self.wave_type.lower())
        self.register_command("freq:freq", self._set_frequency)
        self.register_query("freq:freq?", lambda args: f"{self.frequency}")
        self.register_command("amp:amp", self._set_voltage)
        self.register_query("amp:amp?", lambda args: f"{self.amplitude}")
        self.register_command("amp:offs", self._set_offset)
        self.register_query("amp:offs?", lambda args: f"{self.offset}")
        self.register_command("wave:phas", self._set_phase)
        self.register_query("wave:phas?", lambda args: f"{self.phase}")
        self.register_command("wave:dc", self._set_duty_cycle)
        self.register_query("wave:dc?", lambda args: f"{self.duty_cycle}")
        self.register_command("freq:chrp", self._set_chirp)
        self.register_query("freq:chrp?", lambda args: "1" if self.chirp_enabled else "0")
        self.register_command("freq:cvar", self._set_chirp_var)
        self.register_query("freq:cvar?", lambda args: f"{self.chirp_variation}")
        self.register_command("freq:cper", self._set_chirp_per)
        self.register_query("freq:cper?", lambda args: f"{self.chirp_period}")
        self.register_command("out", self._set_output)
        self.register_query("out?", lambda args: "1" if self.output_enabled else "0")
        self.register_command("noise:state", self._set_noise_state)
        self.register_query("noise:state?", lambda args: "1" if self.noise_enabled else "0")
        self.register_command("noise:level", self._set_noise_level)
        self.register_query("noise:level?", lambda args: f"{self.noise_level}")
        self.register_command("jitter", self._set_jitter)
        self.register_query("jitter?", lambda args: f"{self.jitter}")

    def _set_function(self, args: List[str]) -> None:
        if not args:
            return
        val = args[0].upper()
        if val in ("SIN", "SINE", "SINUSOID"):
            self.wave_type = "SINUSOID"
        elif val in ("SQU", "SQUARE"):
            self.wave_type = "SQUARE"
        elif val in ("TRI", "TRIANGLE"):
            self.wave_type = "TRIANGLE"
        elif val in ("RAMP", "SAW", "SAWTOOTH"):
            self.wave_type = "RAMP"
        elif val in ("RSAW", "REVRAMP", "REVSAW"):
            self.wave_type = "RSAW"
        elif val in ("PULSE", "PULS"):
            self.wave_type = "PULSE"
        else:
            self.wave_type = val

    def _set_frequency(self, args: List[str]) -> None:
        if args:
            try:
                self.frequency = max(1e-3, float(args[0]))
            except ValueError:
                pass

    def _set_voltage(self, args: List[str]) -> None:
        if args:
            try:
                self.amplitude = max(0.0, float(args[0]))
            except ValueError:
                pass

    def _set_offset(self, args: List[str]) -> None:
        if args:
            try:
                self.offset = float(args[0])
            except ValueError:
                pass

    def _set_phase(self, args: List[str]) -> None:
        if args:
            try:
                self.phase = float(args[0])
            except ValueError:
                pass

    def _set_duty_cycle(self, args: List[str]) -> None:
        if args:
            try:
                self.duty_cycle = min(100.0, max(0.0, float(args[0])))
            except ValueError:
                pass

    def _set_chirp(self, args: List[str]) -> None:
        if args:
            v = args[0].strip().lower()
            self.chirp_enabled = v in ("1", "true", "on")

    def _set_chirp_var(self, args: List[str]) -> None:
        if args:
            try:
                self.chirp_variation = float(args[0])
            except ValueError:
                pass

    def _set_chirp_per(self, args: List[str]) -> None:
        if args:
            try:
                self.chirp_period = max(1e-6, float(args[0]))
            except ValueError:
                pass

    def _set_output(self, args: List[str]) -> None:
        if args:
            v = args[0].strip().lower()
            self.output_enabled = v in ("1", "true", "on")

    def _set_noise_state(self, args: List[str]) -> None:
        if args:
            v = args[0].strip().lower()
            self.noise_enabled = v in ("1", "true", "on")

    def _set_noise_level(self, args: List[str]) -> None:
        if args:
            try:
                self.noise_level = max(0.0, float(args[0]))
                if self.noise_level > 0 and not self.noise_enabled:
                    self.noise_enabled = True
            except ValueError:
                pass

    def _set_jitter(self, args: List[str]) -> None:
        if args:
            try:
                self.jitter = max(0.0, float(args[0]))
            except ValueError:
                pass

    def calculate_signal(self, t_array: np.ndarray, phase_offset: float = 0.0) -> np.ndarray:
        """
        On-demand signal computation for a given time array and trigger phase offset.
        Returns array of voltages (V).
        """
        if not self.output_enabled or len(t_array) == 0:
            return np.zeros_like(t_array) + self.offset

        freq = self.frequency
        if self.chirp_enabled and self.chirp_period > 0:
            freq = self.frequency * (1.0 + (self.chirp_variation / 100.0) * np.sin(2.0 * np.pi * t_array / self.chirp_period))

        # Timing / phase jitter simulation
        if self.jitter > 0:
            jitter_sample = float(np.random.uniform(-self.jitter / 2.0, self.jitter / 2.0))
            t_eff = t_array + jitter_sample
        else:
            t_eff = t_array

        rad_phase = np.radians(self.phase) + phase_offset
        arg = 2.0 * np.pi * freq * t_eff + rad_phase
        amp = self.amplitude

        shape = self.wave_type.upper()
        if shape in ("SINUSOID", "SINE"):
            wf = 0.5 * amp * np.sin(arg)
        elif shape in ("SQUARE", "SQU"):
            wf = 0.5 * amp * np.sign(np.sin(arg))
        elif shape in ("TRIANGLE", "TRI"):
            wf = 0.5 * amp * (2.0 / np.pi) * np.arcsin(np.sin(arg))
        elif shape in ("RAMP", "SAW", "SAWTOOTH"):
            # Normal sawtooth: climbs from -amp/2 to +amp/2
            mod = (arg / (2.0 * np.pi)) % 1.0
            wf = amp * (mod - 0.5)
        elif shape in ("RSAW", "REVRAMP"):
            # Reverse sawtooth: drops from +amp/2 to -amp/2
            mod = (arg / (2.0 * np.pi)) % 1.0
            wf = -amp * (mod - 0.5)
        elif shape in ("PULSE", "PULS"):
            dc_norm = self.duty_cycle / 100.0
            mod = (arg / (2.0 * np.pi)) % 1.0
            wf = np.where(mod < dc_norm, 0.5 * amp, -0.5 * amp)
        else:
            wf = 0.5 * amp * np.sin(arg)

        # Amplitude noise simulation
        if self.noise_enabled and self.noise_level > 0:
            noise = np.random.uniform(-self.noise_level / 2.0, self.noise_level / 2.0, size=len(t_array))
            wf = wf + noise

        return wf + self.offset
