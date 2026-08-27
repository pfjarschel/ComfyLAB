# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
ComfyLAB Virtual Instruments Package.
Pure Python headless simulation of VISA/SCPI instruments.
"""

from comfylab.virtual.scpi_base import VirtualSCPIInstrument
from comfylab.virtual.signal_generator import VirtualSignalGenerator
from comfylab.virtual.rc_circuit import VirtualRCCircuit
from comfylab.virtual.oscilloscope import VirtualOscilloscope
from comfylab.virtual.manager import VirtualInstrumentManager

__all__ = [
    "VirtualSCPIInstrument",
    "VirtualSignalGenerator",
    "VirtualRCCircuit",
    "VirtualOscilloscope",
    "VirtualInstrumentManager",
]
