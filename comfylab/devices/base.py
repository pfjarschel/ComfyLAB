# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Base instrument driver interface and common SCPI utility functions.
Pure Python — no ComfyLAB UI or block engine imports allowed here!
"""

import struct
import numpy as np
from typing import Any, Tuple, Optional


def parse_ieee_block(data: bytes) -> bytes:
    """
    Parses an IEEE 488.2 arbitrary block header (#N...data...) and returns the raw binary payload.
    Example: b'#41000' + 1000 raw bytes -> returns 1000 raw bytes.
    """
    if not data or not data.startswith(b'#'):
        return data

    try:
        header_len_digits = int(chr(data[1]))
        num_bytes = int(data[2:2 + header_len_digits].decode('ascii'))
        start_idx = 2 + header_len_digits
        return data[start_idx:start_idx + num_bytes]
    except Exception:
        # Fallback if header format doesn't match standard IEEE header
        return data


class BaseInstrumentDriver:
    """
    Base class for pure Python instrument drivers.
    Wraps a PyVISA resource handle and exposes clean query/write operations.
    """

    def __init__(self, visa_device: Any):
        if visa_device is None:
            raise ValueError("A valid PyVISA resource instance must be supplied.")
        self.device = visa_device

    def write(self, command: str) -> Any:
        """Sends a write command to the instrument."""
        return self.device.write(command)

    def query(self, command: str) -> str:
        """Sends a query command to the instrument and returns the stripped string response."""
        res = self.device.query(command)
        return res.strip() if isinstance(res, str) else res

    def query_raw(self, command: str) -> bytes:
        """Queries raw binary bytes from the instrument."""
        self.device.write(command)
        return self.device.read_raw()

    def identify(self) -> str:
        """Queries standard IEEE 488.2 *IDN? response."""
        return self.query("*IDN?")

    def reset(self) -> None:
        """Sends standard IEEE 488.2 *RST command."""
        self.write("*RST")

    def wait(self) -> None:
        """Sends standard IEEE 488.2 *WAI command."""
        self.write("*WAI")
