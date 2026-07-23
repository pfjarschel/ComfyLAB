# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
BK Precision 4052 Dual-Channel Function Generator Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

from typing import Any, Optional
from comfylab.devices.base import BaseInstrumentDriver


class BK4052(BaseInstrumentDriver):
    """
    Driver for BK Precision 4052 dual-channel function/arbitrary waveform generator.
    Uses Siglent-compatible SCPI syntax (C1:BSWV, C1:OUTP, etc.).
    """

    def set_channel_wave(
        self,
        channel: int = 1,
        shape: Optional[str] = None,
        frequency: Optional[float] = None,
        amplitude: Optional[float] = None,
        offset: Optional[float] = None,
        phase: Optional[float] = None,
        duty: Optional[float] = None,
        symmetry: Optional[float] = None
    ) -> None:
        """Configures waveform shape, frequency (Hz), amplitude (Vpp), offset (V), phase (deg), duty cycle, and symmetry."""
        if channel not in (1, 2):
            raise ValueError(f"Invalid channel selection: {channel}. Must be 1 or 2.")

        ch_prefix = f"C{channel}:BSWV"
        params = []

        if shape is not None:
            shape_upper = shape.upper()
            if shape_upper in ("SINE", "SIN"):
                wv_str = "SINE"
            elif shape_upper in ("SQUARE", "SQU"):
                wv_str = "SQUARE"
            elif shape_upper in ("RAMP", "TRIANGLE"):
                wv_str = "RAMP"
            elif shape_upper in ("PULSE", "PULS"):
                wv_str = "PULSE"
            elif shape_upper in ("NOISE", "NOIS"):
                wv_str = "NOISE"
            elif shape_upper in ("DC",):
                wv_str = "DC"
            else:
                wv_str = shape_upper
            params.append(f"WVTP,{wv_str}")

        if frequency is not None:
            params.append(f"FRQ,{frequency}")

        if amplitude is not None:
            params.append(f"AMP,{amplitude}")

        if offset is not None:
            params.append(f"OFST,{offset}")

        if phase is not None:
            params.append(f"PHSE,{phase}")

        if duty is not None:
            params.append(f"DUTY,{duty}")

        if symmetry is not None:
            params.append(f"SYM,{symmetry}")

        if params:
            cmd = f"{ch_prefix} {','.join(params)}"
            self.write(cmd)

    def set_output(self, channel: int = 1, enable: bool = True, load: Optional[str] = None) -> None:
        """Enables or disables output state for channel 1 or 2. Optionally sets load impedance ('50' or 'HZ')."""
        if channel not in (1, 2):
            raise ValueError(f"Invalid channel selection: {channel}. Must be 1 or 2.")
        
        state = "ON" if enable else "OFF"
        if load is not None:
            load_str = "HZ" if load.upper() in ("HZ", "HIGHZ", "INF") else "50"
            self.write(f"C{channel}:OUTP {state},LOAD,{load_str}")
        else:
            self.write(f"C{channel}:OUTP {state}")
