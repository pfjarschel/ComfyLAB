# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Keysight InfiniiVision DSO-X 3024A / 3000 X-Series Oscilloscope Driver.
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


class KeysightDSOX3024A(BaseInstrumentDriver):
    """
    Driver for Keysight InfiniiVision DSOX 3024A (and 3000A / 3000T X-Series) Oscilloscopes.
    4 Analog Channels, up to 4 GSa/s, MegaZoom IV technology.
    Communicates via VISA USB TMC, TCPIP LAN, or GPIB interfaces.
    """

    def __init__(self, visa_device: Any):
        super().__init__(visa_device)
        try:
            self.device.timeout = 10000
            self.device.chunk_size = 1048576  # 1 MB buffer
        except Exception:
            pass

    def set_timebase(self, scale: Optional[float] = None, position: Optional[float] = None) -> None:
        """Sets horizontal timebase scale (seconds/div) and position delay offset (seconds)."""
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
        bw_limit: Optional[bool] = None
    ) -> None:
        """Configures channel vertical parameters (enable, scale V/div, offset V, coupling, 20MHz BW limit)."""
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
        if bw_limit is not None:
            bw_state = "ON" if bw_limit else "OFF"
            self.write(f"{ch_str}:BWLimit {bw_state}")

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
            else:
                src_val = src_str
            self.write(f":TRIGger:EDGE:SOURce {src_val}")

        if slope is not None:
            slope_str = "NEGative" if slope.upper() in ("NEG", "FALL", "FALLING", "NEGATIVE") else "POSitive"
            self.write(f":TRIGger:EDGE:SLOPe {slope_str}")

        if level is not None:
            self.write(f":TRIGger:EDGE:LEVel {level}")

    def run(self) -> None:
        """Starts continuous acquisition."""
        self.write(":RUN")

    def stop(self) -> None:
        """Stops acquisition."""
        self.write(":STOP")

    def single(self) -> None:
        """Triggers a single-shot acquisition."""
        self.write(":SINGle")

    def acquire_waveform(self, channel: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Acquires vertical voltage waveform array (V) and horizontal time vector (s) for specified channel.
        Queries preamble parameters and parses WORD (16-bit) binary payload.
        """
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel number: {channel}. Must be 1-4.")

        self.write(f":WAVeform:SOURce CHANnel{channel}")
        self.write(":WAVeform:FORMat WORD")
        self.write(":WAVeform:UNSigned 1")
        self.write(":WAVeform:BYTEorder MSBF")  # Most significant byte first

        # Query preamble: format, type, points, count, xincrement, xorigin, xreference, yincrement, yorigin, yreference
        pre_str = self.query(":WAVeform:PREamble?")
        pre_vals = extract_floats(pre_str)

        x_incr = pre_vals[4] if len(pre_vals) > 4 else 1e-6
        x_orig = pre_vals[5] if len(pre_vals) > 5 else 0.0
        x_ref  = pre_vals[6] if len(pre_vals) > 6 else 0.0
        y_incr = pre_vals[7] if len(pre_vals) > 7 else 0.01
        y_orig = pre_vals[8] if len(pre_vals) > 8 else 0.0
        y_ref  = pre_vals[9] if len(pre_vals) > 9 else 0.0

        # Query binary waveform data payload
        raw_bytes = self.query_raw(":WAVeform:DATA?")
        payload = parse_ieee_block(raw_bytes)

        if not payload:
            return np.array([]), np.array([])

        # 16-bit unsigned integers (big-endian >u2)
        raw_vals = np.frombuffer(payload, dtype=">u2")

        volts = (raw_vals.astype(float) - y_ref) * y_incr + y_orig
        time_vec = ((np.arange(len(raw_vals)) - x_ref) * x_incr) + x_orig

        return time_vec, volts

    def measure(self, channel: int = 1, prop: str = "VPP") -> float:
        """
        Queries scalar measurement on specified channel.
        Supported properties: 'VPP', 'FREQ', 'RMS', 'AVERAGE', 'MAX', 'MIN', 'PERIOD', 'DUTY'.
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
            "PERIOD": f":MEASure:PERiod? {ch_str}",
            "DUTY": f":MEASure:DUTYcycle? {ch_str}"
        }

        cmd = cmd_map.get(prop_upper, f":MEASure:VPP? {ch_str}")
        val_str = self.query(cmd)
        return extract_float(val_str, default=0.0)
