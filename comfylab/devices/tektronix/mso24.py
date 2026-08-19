# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Tektronix MSO24 / 2 Series MSO Oscilloscope Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Dict, Optional, Tuple
import numpy as np

from comfylab.devices.base import (
    BaseInstrumentDriver,
    extract_float,
    parse_ieee_block,
    parse_tektronix_preamble
)


class TektronixMSO24(BaseInstrumentDriver):
    """
    Driver for Tektronix 2 Series MSO Oscilloscopes (MSO24 200 MHz, MSO22, etc.).
    Supports up to 4 analog channels, 2.5 GS/s sampling rate, and advanced measurements.
    Communicates via VISA USB TMC, TCPIP VXI-11, Socket, or HiSLIP.
    """

    def __init__(self, visa_device: Any):
        super().__init__(visa_device)
        try:
            self.device.timeout = 10000
            self.device.chunk_size = 1048576  # 1 MB buffer for high resolution waveforms
        except Exception:
            pass

        try:
            self.write("HEADER OFF")
        except Exception:
            pass

    def set_timebase(self, scale: Optional[float] = None, position: Optional[float] = None) -> None:
        """Sets horizontal timebase scale (s/div) and position/delay offset (%)."""
        if scale is not None:
            self.write(f"HORizontal:MODE:SCAle {scale}")
        if position is not None:
            self.write(f"HORizontal:POSition {position}")

    def get_timebase_scale(self) -> float:
        """Queries horizontal timebase scale in seconds/div."""
        val = self.query("HORizontal:MODE:SCAle?")
        return extract_float(val, default=0.001)

    def set_channel(
        self,
        channel: int = 1,
        enable: Optional[bool] = None,
        scale: Optional[float] = None,
        position: Optional[float] = None,
        offset: Optional[float] = None,
        coupling: Optional[str] = None
    ) -> None:
        """Configures channel vertical parameters (scale V/div, position div, offset V, coupling)."""
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel number: {channel}. Must be 1-4.")

        ch_str = f"CH{channel}"

        if enable is not None:
            state = "ON" if enable else "OFF"
            # 2 Series MSO supports both DISPLAY:GLOBAL:CH<n>:STATE and SELECT:CH<n>
            try:
                self.write(f"DISplay:GLObal:{ch_str}:STATE {state}")
            except Exception:
                self.write(f"SELECT:{ch_str} {state}")

        if scale is not None:
            self.write(f"{ch_str}:SCAle {scale}")
        if position is not None:
            self.write(f"{ch_str}:POSition {position}")
        if offset is not None:
            self.write(f"{ch_str}:OFFSet {offset}")
        if coupling is not None:
            self.write(f"{ch_str}:COUPling {coupling.upper()}")

    def set_trigger(
        self,
        source: Optional[str] = "CH1",
        level: Optional[float] = None,
        slope: Optional[str] = "RISE",
        mode: Optional[str] = "AUTO"
    ) -> None:
        """Configures edge trigger parameters."""
        if mode is not None:
            self.write(f"TRIGger:A:MODe {mode.upper()}")
        if source is not None:
            self.write(f"TRIGger:A:EDGE:SOURce {source.upper()}")
        if slope is not None:
            slope_str = "FALL" if slope.upper() in ("FALL", "FALLING", "NEG") else "RISE"
            self.write(f"TRIGger:A:EDGE:SLOPe {slope_str}")
        if level is not None:
            self.write(f"TRIGger:A:LEVel {level}")

    def run_acquisition(self) -> None:
        """Starts oscilloscope acquisition."""
        self.write("ACQuire:STATE RUN")

    def stop_acquisition(self) -> None:
        """Stops oscilloscope acquisition."""
        self.write("ACQuire:STATE STOP")

    def acquire_waveform(self, channel: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Acquires voltage waveform array (V) and horizontal time vector (s) for specified channel.
        Queries preamble parameters and parses binary curve.
        """
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel number: {channel}. Must be 1-4.")

        ch_str = f"CH{channel}"
        try:
            self.write("HEADER OFF")
        except Exception:
            pass

        self.write(f"DATa:SOURce {ch_str}")
        self.write("DATa:ENCdg SRIbinary")  # Signed integer binary
        self.write("DATa:WIDth 1")          # 1 byte per sample
        self.write("DATa:STARt 1")

        # Query record length
        rec_len = int(extract_float(self.query("HORizontal:MODE:RECOrdlength?"), default=10000))
        self.write(f"DATa:STOP {rec_len}")

        # Fetch preamble parameters
        x_incr = extract_float(self.query("WFMOPre:XINcr?"), default=1e-6)
        x_zero = extract_float(self.query("WFMOPre:XZERo?"), default=0.0)
        y_mult = extract_float(self.query("WFMOPre:YMUlt?"), default=1.0)
        y_off  = extract_float(self.query("WFMOPre:YOFF?"), default=0.0)
        y_zero = extract_float(self.query("WFMOPre:YZERo?"), default=0.0)

        # Query raw binary curve
        raw_bytes = self.query_raw("CURVe?")
        payload = parse_ieee_block(raw_bytes)

        if not payload:
            return np.array([]), np.array([])

        raw_values = np.frombuffer(payload, dtype=np.int8)

        volts = (raw_values.astype(float) - y_off) * y_mult + y_zero
        time_vec = (np.arange(len(raw_values)) * x_incr) + x_zero

        return time_vec, volts

    def measure(self, channel: int = 1, measurement_type: str = "PK2PK") -> float:
        """
        Triggers immediate measurement on channel.
        Supported types: 'PK2PK', 'FREQ', 'RMS', 'CRMS', 'MEAN', 'MAX', 'MIN', 'PERIOD'.
        """
        if not (1 <= channel <= 4):
            raise ValueError(f"Invalid channel number: {channel}. Must be 1-4.")

        ch_str = f"CH{channel}"
        mtype = measurement_type.upper()

        type_map = {
            "PK2PK": "PK2Pk",
            "VPP": "PK2Pk",
            "FREQ": "FREQuency",
            "FREQUENCY": "FREQuency",
            "RMS": "RMS",
            "CRMS": "CRMs",
            "MEAN": "MEAN",
            "MAX": "MAXimum",
            "MIN": "MINImum",
            "PERIOD": "PERIod"
        }
        mapped_type = type_map.get(mtype, "PK2Pk")

        self.write(f"MEASUrement:IMMed:TYPe {mapped_type}")
        self.write(f"MEASUrement:IMMed:SOURCE1 {ch_str}")
        val_str = self.query("MEASUrement:IMMed:VALue?")
        return extract_float(val_str, default=0.0)
