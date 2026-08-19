# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Keysight InfiniiVision DSO-X 1204A / 1000 X-Series Oscilloscope Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Dict, Optional, Tuple
import numpy as np

from comfylab.devices.base import (
    BaseInstrumentDriver,
    extract_float,
    extract_floats,
    parse_ieee_block
)


class KeysightDSOX1204A(BaseInstrumentDriver):
    """
    Driver for Keysight InfiniiVision DSOX 1204A (and 1000 X-Series) 4-channel Oscilloscopes.
    Includes built-in 20 MHz WaveGen Function Generator control.
    Communicates via VISA USB TMC or TCPIP LAN interfaces.
    """

    def __init__(self, visa_device: Any):
        super().__init__(visa_device)
        try:
            self.device.timeout = 10000
            self.device.chunk_size = 1048576  # 1 MB buffer
        except Exception:
            pass

    def set_timebase(self, scale: Optional[float] = None, position: Optional[float] = None) -> None:
        """Sets horizontal timebase scale (seconds/div) and position offset (seconds)."""
        if scale is not None:
            self.write(f":TIMebase:SCALe {scale}")
        if position is not None:
            self.write(f":TIMebase:POSition {position}")

    def get_timebase_scale(self) -> float:
        """Returns horizontal timebase scale in seconds/div."""
        val = self.query(":TIMebase:SCALe?")
        return extract_float(val, default=0.001)

    def set_channel(
        self,
        channel: int = 1,
        enable: Optional[bool] = None,
        scale: Optional[float] = None,
        offset: Optional[float] = None,
        coupling: Optional[str] = None,
        probe: Optional[float] = None
    ) -> None:
        """Configures channel vertical parameters (enable, scale V/div, offset V, coupling, probe attenuation)."""
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
        if probe is not None:
            self.write(f"{ch_str}:PROBe {probe}")

    def set_trigger(
        self,
        source: Optional[str] = "CHAN1",
        level: Optional[float] = None,
        slope: Optional[str] = "POS",
        sweep: Optional[str] = "AUTO"
    ) -> None:
        """Configures edge trigger parameters."""
        if sweep is not None:
            self.write(f":TRIGger:SWEEp {sweep.upper()}")

        if source is not None:
            src_str = source.upper()
            if src_str in ("CH1", "CHAN1", "1"):
                src_val = "CHANnel1"
            elif src_str in ("CH2", "CHAN2", "2"):
                src_val = "CHANnel2"
            elif src_str in ("CH3", "CHAN3", "3"):
                src_val = "CHANnel3"
            elif src_str in ("CH4", "CHAN4", "4"):
                src_val = "CHANnel4"
            elif src_str in ("EXT", "EXTERNAL"):
                src_val = "EXTernal"
            elif src_str in ("LINE",):
                src_val = "LINE"
            elif src_str in ("WGEN", "WAVEGEN"):
                src_val = "WGEN"
            else:
                src_val = src_str
            self.write(f":TRIGger:EDGE:SOURce {src_val}")

        if slope is not None:
            slope_str = "NEGative" if slope.upper() in ("NEG", "FALL", "FALLING", "NEGATIVE") else "POSitive"
            self.write(f":TRIGger:EDGE:SLOPe {slope_str}")

        if level is not None:
            self.write(f":TRIGger:EDGE:LEVel {level}")

    def run(self) -> None:
        """Starts acquisition."""
        self.write(":RUN")

    def stop(self) -> None:
        """Stops acquisition."""
        self.write(":STOP")

    def acquire_waveform(self, channel: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Acquires vertical voltage waveform array (V) and horizontal time vector (s) for specified channel.
        """
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel number: {channel}. Must be 1-4.")

        self.write(f":WAVeform:SOURce CHANnel{channel}")
        self.write(":WAVeform:FORMat WORD")
        self.write(":WAVeform:UNSigned 1")
        self.write(":WAVeform:BYTEorder MSBF")

        # Query preamble
        pre_str = self.query(":WAVeform:PREamble?")
        pre_vals = extract_floats(pre_str)

        x_incr = pre_vals[4] if len(pre_vals) > 4 else 1e-6
        x_orig = pre_vals[5] if len(pre_vals) > 5 else 0.0
        x_ref  = pre_vals[6] if len(pre_vals) > 6 else 0.0
        y_incr = pre_vals[7] if len(pre_vals) > 7 else 0.01
        y_orig = pre_vals[8] if len(pre_vals) > 8 else 0.0
        y_ref  = pre_vals[9] if len(pre_vals) > 9 else 0.0

        raw_bytes = self.query_raw(":WAVeform:DATA?")
        payload = parse_ieee_block(raw_bytes)

        if not payload:
            return np.array([]), np.array([])

        raw_vals = np.frombuffer(payload, dtype=">u2")

        volts = (raw_vals.astype(float) - y_ref) * y_incr + y_orig
        time_vec = ((np.arange(len(raw_vals)) - x_ref) * x_incr) + x_orig

        return time_vec, volts

    def measure(self, channel: int = 1, prop: str = "VPP") -> float:
        """
        Queries scalar measurement on specified channel.
        Supported properties: 'VPP', 'FREQ', 'RMS', 'AVERAGE', 'MAX', 'MIN', 'PERIOD'.
        """
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel number: {channel}. Must be 1-4.")

        ch_str = f"CHANnel{channel}"
        prop_upper = prop.upper()

        cmd_map = {
            "VPP": f":MEASure:VPP? {ch_str}",
            "FREQ": f":MEASure:FREQuency? {ch_str}",
            "FREQUENCY": f":MEASure:FREQuency? {ch_str}",
            "RMS": f":MEASure:VRMS? DISPlay,{ch_str}",
            "AVERAGE": f":MEASure:VAVerage? DISPlay,{ch_str}",
            "MEAN": f":MEASure:VAVerage? DISPlay,{ch_str}",
            "MAX": f":MEASure:VMAX? {ch_str}",
            "MIN": f":MEASure:VMIN? {ch_str}",
            "PERIOD": f":MEASure:PERiod? {ch_str}"
        }

        cmd = cmd_map.get(prop_upper, f":MEASure:VPP? {ch_str}")
        val_str = self.query(cmd)
        return extract_float(val_str, default=0.0)

    def set_wavegen(
        self,
        shape: Optional[str] = "SIN",
        frequency: Optional[float] = 1000.0,
        amplitude: Optional[float] = 1.0,
        offset: Optional[float] = 0.0,
        enable: bool = True
    ) -> None:
        """Configures built-in WaveGen Function Generator output."""
        if shape is not None:
            s_up = shape.upper()
            if s_up in ("SIN", "SINE", "SINUSOID"):
                f_str = "SIN"
            elif s_up in ("SQU", "SQUARE"):
                f_str = "SQU"
            elif s_up in ("RAMP",):
                f_str = "RAMP"
            elif s_up in ("PULS", "PULSE"):
                f_str = "PULS"
            elif s_up in ("NOIS", "NOISE"):
                f_str = "NOIS"
            elif s_up in ("DC",):
                f_str = "DC"
            else:
                f_str = s_up
            self.write(f":WGEN:FUNCtion {f_str}")

        if frequency is not None:
            self.write(f":WGEN:FREQuency {frequency}")
        if amplitude is not None:
            self.write(f":WGEN:VOLTage {amplitude}")
        if offset is not None:
            self.write(f":WGEN:VOLTage:OFFSet {offset}")

        state = "ON" if enable else "OFF"
        self.write(f":WGEN:OUTPut {state}")
