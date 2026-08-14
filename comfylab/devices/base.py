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

import re
import csv
import io
import struct
import numpy as np
from typing import Any, Tuple, Optional, List, Dict

_FLOAT_REGEX = re.compile(r"[-+]?(?:(?:\d+\.?\d*)|(?:\.\d+))(?:[eE][-+]?\d+)?")


def extract_float(text: Any, default: float = 0.0) -> float:
    """
    Robustly extracts a floating point number from a SCPI string response.
    Handles responses with command headers (':WFMPRE:XINCR 1.25E-6'),
    assignments ('TD2=2500', 'xvoltage=[50.0]'), prefixes with channel numbers ('AIN 0 2.50'),
    and units ('1550.0NM', '12.345 mm', '-10.5 dBm').
    """
    if text is None:
        return default
    if isinstance(text, (int, float)):
        return float(text)
    
    text_str = str(text).strip().strip('"\'')
    if not text_str:
        return default

    # If there is an assignment '=...', parse the value after the '='
    if "=" in text_str:
        text_str = text_str.split("=")[-1].strip()

    # Find all float matches in text_str
    matches = _FLOAT_REGEX.findall(text_str)
    if not matches:
        return default

    # In SCPI responses with labels/channels (e.g. 'AIN 0 2.50' or ':READ2:POW 1.25e-3'),
    # the actual measurement value is the last numeric token.
    try:
        return float(matches[-1])
    except ValueError:
        return default


def extract_floats(text: Any) -> List[float]:
    """
    Extracts all floating point numbers from a comma/semicolon/space separated SCPI response.
    Ignores headers, trace names, and unit identifiers.
    """
    if text is None:
        return []
    text_str = str(text).strip()
    if not text_str:
        return []

    # If text is comma or semicolon separated
    if "," in text_str or ";" in text_str:
        chunks = text_str.replace(";", ",").replace("\n", ",").split(",")
        res = []
        for chunk in chunks:
            chunk_clean = chunk.strip()
            if not chunk_clean:
                continue
            # If chunk is just a trace identifier like 'TRACE1' or 'TRA' without decimal or sign
            # and is before data, ignore it if preceded by command header
            if re.match(r"^(?:[A-Za-z_:]+\s+)?(?:TRACE[1-9]|TR[A-G]|CH[1-4])$", chunk_clean, re.IGNORECASE):
                continue
            val = extract_float(chunk_clean, default=None)
            if val is not None:
                res.append(val)
        return res

    # Space-separated numbers
    matches = _FLOAT_REGEX.findall(text_str)
    res = []
    for m in matches:
        try:
            res.append(float(m))
        except ValueError:
            continue
    return res


def parse_ieee_block(data: bytes) -> bytes:
    """
    Parses an IEEE 488.2 arbitrary block header (#N...data...) and returns the raw binary payload.
    Robust against leading SCPI headers (e.g. b':CURV #42500...'), trailing newlines,
    and both definite (#N...) and indefinite (#0...) length blocks.
    """
    if not data:
        return data

    # Find the IEEE block start character '#'
    hash_idx = data.find(b'#')
    if hash_idx == -1:
        # Strip trailing newlines if plain data
        return data.rstrip(b'\r\n')

    try:
        header_len_char = chr(data[hash_idx + 1])
        if header_len_char == '0':
            # Indefinite length block (#0<payload><NL>)
            start_idx = hash_idx + 2
            return data[start_idx:].rstrip(b'\r\n')
        
        header_len_digits = int(header_len_char)
        start_digits = hash_idx + 2
        end_digits = start_digits + header_len_digits
        num_bytes = int(data[start_digits:end_digits].decode('ascii'))
        start_idx = end_digits
        return data[start_idx:start_idx + num_bytes]
    except Exception:
        # Fallback if header format doesn't match standard IEEE header
        return data[hash_idx:].rstrip(b'\r\n')


def parse_tektronix_preamble(preamble_str: str) -> Dict[str, Any]:
    """
    Parses full Tektronix WFMPRe? / WFMOPre? response string into a structured dictionary.
    Handles semicolon separation and quoted strings (e.g. WFID with commas and date/time stamps).
    
    Standard Tektronix Preamble fields (16 fields):
    0: BYT_Nr (int)
    1: BIT_Nr (int)
    2: ENCdg (str: 'BIN', 'ASC')
    3: BN_Fmt (str: 'RI', 'RP')
    4: BYT_Or (str: 'MSB', 'LSB')
    5: NR_Pt (int: number of points)
    6: WFID (str: channel info, coupling, scale, date/time)
    7: PT_Fmt (str: 'Y', 'ENV')
    8: XINcr (float: horizontal sample interval)
    9: PT_Off (float/int: point offset)
    10: XZERo (float: horizontal origin time)
    11: XUNit (str: 's', 'Hz', etc.)
    12: YMUlt (float: vertical scale factor)
    13: YZERo (float: vertical offset in Volts)
    14: YOFF (float: vertical position in digitizing levels)
    15: YUNit (str: 'Volts', etc.)
    """
    clean_str = preamble_str.strip()
    if clean_str.upper().startswith(":WFMPRE:"):
        clean_str = clean_str[8:]
    elif clean_str.upper().startswith("WFMPRE:"):
        clean_str = clean_str[7:]
    elif clean_str.upper().startswith(":WFMOPRE:"):
        clean_str = clean_str[9:]
    elif clean_str.upper().startswith("WFMOPRE:"):
        clean_str = clean_str[8:]

    # Parse semicolon-separated fields respecting quotes
    reader = csv.reader(io.StringIO(clean_str), delimiter=';', quotechar='"')
    try:
        fields = next(reader)
    except Exception:
        fields = clean_str.split(";")

    fields = [f.strip().strip('"') for f in fields if f.strip()]

    result: Dict[str, Any] = {
        "byt_nr": 1,
        "bit_nr": 8,
        "encdg": "BIN",
        "bn_fmt": "RI",
        "byt_or": "MSB",
        "nr_pt": 2500,
        "wfid": "",
        "pt_fmt": "Y",
        "x_incr": 1e-6,
        "pt_off": 0.0,
        "x_zero": 0.0,
        "x_unit": "s",
        "y_mult": 1.0,
        "y_zero": 0.0,
        "y_off": 0.0,
        "y_unit": "Volts"
    }

    if len(fields) >= 16:
        result["byt_nr"] = int(extract_float(fields[0], 1))
        result["bit_nr"] = int(extract_float(fields[1], 8))
        result["encdg"] = fields[2]
        result["bn_fmt"] = fields[3]
        result["byt_or"] = fields[4]
        result["nr_pt"] = int(extract_float(fields[5], 2500))
        result["wfid"] = fields[6]
        result["pt_fmt"] = fields[7]
        result["x_incr"] = extract_float(fields[8], 1e-6)
        result["pt_off"] = extract_float(fields[9], 0.0)
        result["x_zero"] = extract_float(fields[10], 0.0)
        result["x_unit"] = fields[11]
        result["y_mult"] = extract_float(fields[12], 1.0)
        result["y_zero"] = extract_float(fields[13], 0.0)
        result["y_off"] = extract_float(fields[14], 0.0)
        result["y_unit"] = fields[15]
    elif len(fields) > 0:
        # Fallback if fewer fields returned
        if len(fields) > 6:
            result["wfid"] = fields[6]
        if len(fields) > 8:
            result["x_incr"] = extract_float(fields[8], 1e-6)
        if len(fields) > 10:
            result["x_zero"] = extract_float(fields[10], 0.0)
        if len(fields) > 12:
            result["y_mult"] = extract_float(fields[12], 1.0)
        if len(fields) > 13:
            result["y_zero"] = extract_float(fields[13], 0.0)
        if len(fields) > 14:
            result["y_off"] = extract_float(fields[14], 0.0)

    return result


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
