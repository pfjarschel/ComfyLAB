# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
National Instruments (NI) DAQmx Data Acquisition Driver.
Pure Python — no ComfyLAB UI or block dependencies.
Raises explicit RuntimeError if NI-DAQmx C-drivers are not installed on system.
"""

from typing import Any, List, Tuple, Optional
import numpy as np

try:
    import nidaqmx
    from nidaqmx.constants import AcquisitionType, TerminalConfiguration
    NIDAQMX_AVAILABLE = True
except Exception:
    NIDAQMX_AVAILABLE = False


class NIDAQmxDevice:
    """
    Driver wrapper for National Instruments DAQ devices via official nidaqmx library.
    Exposes Analog Input sampling, Analog Output voltage generation, and Digital I/O lines.
    """

    def __init__(self, device_name: str = "Dev1"):
        if not NIDAQMX_AVAILABLE:
            raise RuntimeError("The 'nidaqmx' Python package or NI-DAQmx C-runtime driver is not installed on this system.")
        
        self.device_name = device_name
        # Verify local NI-DAQmx system
        try:
            sys_info = nidaqmx.system.System.local()
            dev_names = [d.name for d in sys_info.devices]
            if device_name and device_name not in dev_names and len(dev_names) > 0:
                # If exact name not found, use first available device
                self.device_name = dev_names[0]
        except Exception as e:
            raise RuntimeError(f"Failed to access NI-DAQmx C-driver system: {e}")

    def read_analog_input(
        self,
        channel: str = "ai0",
        min_val: float = -10.0,
        max_val: float = 10.0,
        samples: int = 1000,
        sample_rate: float = 10000.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Acquires finite sample block of Analog Input voltage from channel (e.g. 'ai0' or 'ai0:1').
        Returns tuple of (time_vector_seconds, voltage_array_volts).
        """
        chan_path = f"{self.device_name}/{channel}"
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(
                chan_path,
                min_val=min_val,
                max_val=max_val,
                terminal_config=TerminalConfiguration.DEFAULT
            )
            task.timing.cfg_samp_clk_timing(
                rate=sample_rate,
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=samples
            )
            data = task.read(number_of_samples_per_channel=samples, timeout=10.0)

        volts = np.array(data, dtype=float)
        time_vec = np.arange(len(volts)) / float(sample_rate)
        return time_vec, volts

    def write_analog_output(self, channel: str = "ao0", voltage: float = 0.0) -> None:
        """Writes DC analog voltage to specified output channel (e.g. 'ao0')."""
        chan_path = f"{self.device_name}/{channel}"
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(chan_path)
            task.write(voltage, auto_start=True)
