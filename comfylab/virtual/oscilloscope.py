# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Pure-Python, headless Virtual 4-Channel Oscilloscope complying with standard SCPI commands.
Supports both dedicated ComfyLAB virtual blocks and standard GenericOscilloscope driver.
Port: 51234
IDN: ComfyLAB,Virtual Oscilloscope,VOSC1,1.0.0
"""

import numpy as np
from typing import List, Optional, Tuple, Dict, Any, Union
from comfylab.virtual.scpi_base import VirtualSCPIInstrument


class VirtualOscilloscope(VirtualSCPIInstrument):
    """
    Headless 4-Channel Oscilloscope instrument.
    Calculates waveforms strictly on demand upon receiving query commands.
    Channel 1 is connected to Signal Generator.
    Channel 2 is connected to RC Circuit.
    """

    def __init__(
        self,
        port: int = 51234,
        name: str = "Virtual Oscilloscope",
        ch1_source: Optional[Any] = None,
        ch2_source: Optional[Any] = None,
        verbose: bool = False
    ):
        super().__init__(port=port, name=name, verbose=verbose)

        # Signal Sources
        self.ch1_source = ch1_source
        self.ch2_source = ch2_source
        self.ch3_source = None
        self.ch4_source = None

        # Horizontal Timebase
        self.timediv: float = 0.001       # seconds / division (1 ms/div)
        self.timeoffs: float = 0.0        # horizontal position / offset in seconds
        self.points: int = 1000           # number of acquisition points
        self.averages: int = 1            # 1 = no averaging

        # State & Trigger
        self.running: bool = True
        self.trigger_mode: str = "AUTO"   # "AUTO" or "FREE"

        # Waveform Transfer
        self.waveform_source: int = 1     # Channel 1..4
        self.waveform_format: str = "ASCII"  # "ASCII" or "BYTE"

        # Vertical Channels (1-indexed: 1, 2, 3, 4)
        self.ch_enabled: Dict[int, bool] = {1: True, 2: True, 3: False, 4: False}
        self.ch_scale: Dict[int, float] = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}        # V/div
        self.ch_offset: Dict[int, float] = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}       # Volts
        self.ch_coupling: Dict[int, str] = {1: "DC", 2: "DC", 3: "DC", 4: "DC"}   # "DC", "AC", "GND"

        self._register_handlers()

    def get_idn(self) -> str:
        return "ComfyLAB,Virtual Oscilloscope,VOSC1,1.0.0"

    def reset(self) -> None:
        self.timediv = 0.001
        self.timeoffs = 0.0
        self.points = 1000
        self.averages = 1
        self.running = True
        self.trigger_mode = "AUTO"
        self.waveform_source = 1
        self.waveform_format = "ASCII"
        self.ch_enabled = {1: True, 2: True, 3: False, 4: False}
        self.ch_scale = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}
        self.ch_offset = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        self.ch_coupling = {1: "DC", 2: "DC", 3: "DC", 4: "DC"}

    def set_sources(self, ch1: Optional[Any] = None, ch2: Optional[Any] = None) -> None:
        self.ch1_source = ch1
        self.ch2_source = ch2

    def _register_handlers(self) -> None:
        # Run / Stop controls
        self.register_command("run", lambda args: setattr(self, "running", True))
        self.register_command("stop", lambda args: setattr(self, "running", False))
        self.register_query("run?", lambda args: "1" if self.running else "0")

        # Timebase commands (:TIMebase:...)
        self.register_command("timebase:scale", self._set_hscale)
        self.register_query("timebase:scale?", lambda args: f"{self.timediv:.6e}")
        self.register_command("timebase:position", self._set_hoffset)
        self.register_query("timebase:position?", lambda args: f"{self.timeoffs:.6e}")
        self.register_command("timebase:offset", self._set_hoffset)
        self.register_query("timebase:offset?", lambda args: f"{self.timeoffs:.6e}")
        self.register_query("timebase:data?", self._get_hdata)

        # Acquisition commands (:ACQuire:...)
        self.register_command("acquire:points", self._set_points)
        self.register_query("acquire:points?", lambda args: f"{self.points}")
        self.register_command("acquire:averages", self._set_averages)
        self.register_query("acquire:averages?", lambda args: f"{self.averages}")

        # Trigger commands (:TRIGger:...)
        self.register_command("trigger:mode", self._set_trigger_mode)
        self.register_query("trigger:mode?", lambda args: self.trigger_mode)
        self.register_command("trigger:sweep", self._set_trigger_mode)
        self.register_query("trigger:sweep?", lambda args: self.trigger_mode)

        # Waveform setup commands (:WAVeform:...)
        self.register_command("waveform:source", self._set_waveform_source)
        self.register_query("waveform:source?", lambda args: f"CHANnel{self.waveform_source}")
        self.register_command("waveform:format", self._set_waveform_format)
        self.register_query("waveform:format?", lambda args: self.waveform_format)
        self.register_command("waveform:points", self._set_points)
        self.register_query("waveform:points?", lambda args: f"{self.points}")
        self.register_query("waveform:data?", self._get_waveform_data)

        # Per-channel commands (:CHANnel1..4:...)
        for ch in (1, 2, 3, 4):
            self.register_command(f"channel{ch}:display", lambda args, c=ch: self._set_ch_display(c, args))
            self.register_query(f"channel{ch}:display?", lambda args, c=ch: "1" if self.ch_enabled[c] else "0")
            self.register_command(f"channel{ch}:enable", lambda args, c=ch: self._set_ch_display(c, args))
            self.register_query(f"channel{ch}:enable?", lambda args, c=ch: "1" if self.ch_enabled[c] else "0")

            self.register_command(f"channel{ch}:scale", lambda args, c=ch: self._set_ch_scale(c, args))
            self.register_query(f"channel{ch}:scale?", lambda args, c=ch: f"{self.ch_scale[c]:.6e}")

            self.register_command(f"channel{ch}:offset", lambda args, c=ch: self._set_ch_offset(c, args))
            self.register_query(f"channel{ch}:offset?", lambda args, c=ch: f"{self.ch_offset[c]:.6e}")

            self.register_command(f"channel{ch}:coupling", lambda args, c=ch: self._set_ch_coupling(c, args))
            self.register_query(f"channel{ch}:coupling?", lambda args, c=ch: self.ch_coupling[c])

            self.register_query(f"channel{ch}:data?", lambda args, c=ch: self._get_ch_data_ascii(c))

        # Legacy SimVISA compatibility commands
        self.register_command("horiz:scale", self._set_hscale)
        self.register_query("horiz:scale?", lambda args: f"{self.timediv}")
        self.register_command("horiz:offset", self._set_hoffset)
        self.register_query("horiz:offset?", lambda args: f"{self.timeoffs}")
        self.register_query("horiz:data?", self._get_hdata)
        self.register_command("acq:points", self._set_points)
        self.register_query("acq:points?", lambda args: f"{self.points}")
        self.register_command("trig:auto", lambda args: setattr(self, "trigger_mode", "AUTO"))
        self.register_command("trig:free", lambda args: setattr(self, "trigger_mode", "FREE"))

    # Parameter Setters
    def _set_hscale(self, args: List[str]) -> None:
        if args:
            try:
                self.timediv = max(1e-12, float(args[0]))
            except ValueError:
                pass

    def _set_hoffset(self, args: List[str]) -> None:
        if args:
            try:
                self.timeoffs = float(args[0])
            except ValueError:
                pass

    def _set_points(self, args: List[str]) -> None:
        if args:
            try:
                self.points = min(100000, max(10, int(float(args[0]))))
            except ValueError:
                pass

    def _set_averages(self, args: List[str]) -> None:
        if args:
            try:
                self.averages = max(1, int(float(args[0])))
            except ValueError:
                pass

    def _set_trigger_mode(self, args: List[str]) -> None:
        if args:
            val = args[0].strip().upper()
            if val in ("AUTO", "NORM", "NORMAL"):
                self.trigger_mode = "AUTO"
            else:
                self.trigger_mode = "FREE"

    def _set_waveform_source(self, args: List[str]) -> None:
        if args:
            val = args[0].strip().upper()
            for ch in (1, 2, 3, 4):
                if str(ch) in val:
                    self.waveform_source = ch
                    return

    def _set_waveform_format(self, args: List[str]) -> None:
        if args:
            val = args[0].strip().upper()
            if "BYTE" in val or "BIN" in val:
                self.waveform_format = "BYTE"
            else:
                self.waveform_format = "ASCII"

    def _set_ch_display(self, ch: int, args: List[str]) -> None:
        if args:
            v = args[0].strip().lower()
            self.ch_enabled[ch] = v in ("1", "true", "on")

    def _set_ch_scale(self, ch: int, args: List[str]) -> None:
        if args:
            try:
                self.ch_scale[ch] = max(1e-6, float(args[0]))
            except ValueError:
                pass

    def _set_ch_offset(self, ch: int, args: List[str]) -> None:
        if args:
            try:
                self.ch_offset[ch] = float(args[0])
            except ValueError:
                pass

    def _set_ch_coupling(self, ch: int, args: List[str]) -> None:
        if args:
            v = args[0].strip().upper()
            if v in ("DC", "AC", "GND"):
                self.ch_coupling[ch] = v

    # Data Calculation & Acquisition (Strictly On-Demand)
    def _compute_channel_data(self, ch: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes time vector and voltage array on demand.
        Window length = 10 divisions * timediv.
        """
        n = self.points
        total_time = 10.0 * self.timediv
        t_array = np.linspace(self.timeoffs, self.timeoffs + total_time, n)

        if not self.running:
            return t_array, np.zeros(n)

        # Trigger phase synchronization
        siggen_freq = getattr(self.ch1_source, "frequency", 1000.0) if self.ch1_source else 1000.0
        if self.trigger_mode == "AUTO":
            # Phase is locked to timeoffs so wave does not jitter
            phase_offset = -2.0 * np.pi * siggen_freq * self.timeoffs
        else:
            # Free-running: random phase per query
            phase_offset = float(np.random.uniform(0.0, 2.0 * np.pi))

        if ch == 1:
            if self.ch1_source:
                volts = self.ch1_source.calculate_signal(t_array, phase_offset)
            else:
                volts = np.zeros(n)
        elif ch == 2:
            if self.ch1_source and self.ch2_source:
                v_in = self.ch1_source.calculate_signal(t_array, phase_offset)
                volts = self.ch2_source.calculate_signal(v_in, t_array)
            else:
                volts = np.zeros(n)
        else:
            volts = np.zeros(n)

        # Apply coupling
        coup = self.ch_coupling.get(ch, "DC")
        if coup == "GND":
            volts = np.zeros(n)
        elif coup == "AC":
            volts = volts - np.mean(volts)

        # Apply channel offset
        volts = volts + self.ch_offset.get(ch, 0.0)
        return t_array, volts

    def _get_hdata(self, args: List[str]) -> str:
        total_time = 10.0 * self.timediv
        t_array = np.linspace(self.timeoffs, self.timeoffs + total_time, self.points)
        return ",".join(f"{t:.6e}" for t in t_array)

    def _get_ch_data_ascii(self, ch: int) -> str:
        _, volts = self._compute_channel_data(ch)
        return ",".join(f"{v:.6e}" for v in volts)

    def _get_waveform_data(self, args: List[str]) -> Union[str, bytes]:
        """
        Handles :WAVeform:DATA?
        If waveform_format is ASCII: returns comma-separated string.
        If waveform_format is BYTE: returns IEEE 488.2 arbitrary block header (#8...data...\n).
        """
        ch = self.waveform_source
        _, volts = self._compute_channel_data(ch)

        if self.waveform_format == "BYTE":
            # GenericOscilloscope expectation:
            # volts = (raw_values.astype(float) - 128.0) * (t_scale / 25.0)
            # Therefore: raw_values = 128.0 + volts * (25.0 / t_scale)
            # where t_scale = timediv
            scale = max(1e-9, self.timediv)
            raw_values = np.clip(np.round(128.0 + volts * (25.0 / scale)), 14, 250).astype(np.uint8)
            # Ensure no 0x0A (\n) or 0x0D (\r) inside binary payload breaks line-based VISA reads
            raw_values[raw_values == 10] = 11
            raw_values[raw_values == 13] = 14
            payload = raw_values.tobytes()
            length_bytes = len(payload)
            len_str = str(length_bytes)
            num_digits = str(len(len_str))
            header = f"#{num_digits}{len_str}".encode("ascii")
            return header + payload + b"\n"
        else:
            return ",".join(f"{v:.6e}" for v in volts)
