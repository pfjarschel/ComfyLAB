# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import logging
from typing import Any, Optional, Dict, List

import numpy as np
import scipy.signal as signal
import scipy.interpolate as interpolate
import scipy.ndimage as ndimage

logger = logging.getLogger("comfylab.blocks.signal")

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext


@register_block("math/signal_processing/fft")
class FFTBlock(BaseBlock):
    """Computes a Discrete Fourier Transform (spectrum magnitude) of a signal."""
    icon = "📈"
    display_name = "FFT Spectrum"
    description = "Computes a Discrete Fourier Transform (spectrum magnitude) of a signal."

    inputs_def = [
        ExecIn("Analyze"),
        DataIn("Signal", type_hint=np.ndarray),
        DataIn("X", type_hint=np.ndarray, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Spectrum", type_hint=np.ndarray),
        DataOut("Phase", type_hint=np.ndarray),
        DataOut("Frequencies", type_hint=np.ndarray),
        DataOut("Length", type_hint=int)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_spectrum: Optional[np.ndarray] = None
        self._last_phase: Optional[np.ndarray] = None
        self._last_freqs: Optional[np.ndarray] = None
        self._last_length: int = 0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        signal_input = await context.pull(self.id, "Signal")
        x_input = await context.pull(self.id, "X")

        if signal_input is None or not isinstance(signal_input, np.ndarray) or len(signal_input) == 0:
            self._last_spectrum = np.array([])
            self._last_phase = np.array([])
            self._last_freqs = np.array([])
            self._last_length = 0
            return "Out"

        sig = signal_input
        N = len(sig)
        fft_result = np.fft.rfft(sig)
        magnitude = np.abs(fft_result) / N
        phase = np.angle(fft_result)
        
        self._last_spectrum = magnitude
        self._last_phase = phase
        self._last_length = N

        if x_input is not None and isinstance(x_input, np.ndarray) and len(x_input) == N and N >= 2:
            try:
                dx = float(x_input[1] - x_input[0])
                self._last_freqs = np.fft.rfftfreq(N, d=dx)
            except Exception:
                self._last_freqs = np.array([])
        else:
            self._last_freqs = np.array([])

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Spectrum":
            return self._last_spectrum
        elif pin_name == "Phase":
            return self._last_phase
        elif pin_name == "Frequencies":
            return self._last_freqs
        elif pin_name == "Length":
            return self._last_length
        return None

    async def clear_data(self) -> None:
        self._last_spectrum = np.array([])
        self._last_phase = np.array([])
        self._last_freqs = np.array([])
        self._last_length = 0


@register_block("math/signal_processing/ifft")
class IFFTBlock(BaseBlock):
    """Computes an Inverse Discrete Fourier Transform to reconstruct a time-domain signal."""
    icon = "📉"
    display_name = "Inverse FFT"
    description = "Reconstructs a time-domain signal from Magnitude (Spectrum) and Phase arrays."

    inputs_def = [
        ExecIn("Reconstruct"),
        DataIn("Spectrum", type_hint=np.ndarray),
        DataIn("Phase", type_hint=np.ndarray, optional=True),
        DataIn("Length", type_hint=int, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Signal", type_hint=np.ndarray)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_signal: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        mag_input = await context.pull(self.id, "Spectrum")
        phase_input = await context.pull(self.id, "Phase")
        length_input = await context.pull(self.id, "Length")

        if mag_input is None or not isinstance(mag_input, np.ndarray) or len(mag_input) == 0:
            self._last_signal = np.array([])
            return "Out"

        try:
            mag = mag_input
            
            if phase_input is not None and isinstance(phase_input, np.ndarray) and len(phase_input) == len(mag):
                phase = phase_input
            else:
                phase = np.zeros_like(mag)
                
            n_recon = int(length_input) if length_input is not None else 2 * (len(mag) - 1)
            
            # The FFTBlock scales magnitude by dividing by N. We must multiply it back.
            mag_scaled = mag * n_recon
            complex_spectrum = mag_scaled * np.exp(1j * phase)
            
            self._last_signal = np.fft.irfft(complex_spectrum, n=n_recon)
        except Exception as e:
            logger.error(f"Error in IFFTBlock '{self.id}': {e}")
            self._last_signal = np.array([])

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Signal":
            return self._last_signal
        return None

    async def clear_data(self) -> None:
        self._last_signal = np.array([])


@register_block("math/signal_processing/filter")
class FilterBlock(BaseBlock):
    """Filters a signal using moving average or Butterworth low/high/band-pass filter."""
    icon = "📈"
    display_name = "Signal Filter"
    description = "Filters a 1D ndarray using moving average or Butterworth filters with normalized frequency."

    inputs_def = [
        ExecIn("Filter"),
        DataIn("Signal", type_hint=np.ndarray),
        DataIn("FilterType", type_hint=str, default="Moving Average", widget="dropdown", 
               options=["Moving Average", "Low-pass", "High-pass", "Band-pass"]),
        DataIn("Cutoff", type_hint=float, default=0.1, widget="number", min_val=0.01, max_val=0.99, optional=True),
        DataIn("LowCutoff", type_hint=float, default=0.1, widget="number", min_val=0.01, max_val=0.99, optional=True),
        DataIn("HighCutoff", type_hint=float, default=0.3, widget="number", min_val=0.01, max_val=0.99, optional=True),
        DataIn("Order", type_hint=int, default=2, widget="number", min_val=1, max_val=10, optional=True),
        DataIn("Window", type_hint=int, default=5, widget="number", min_val=1, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Filtered", type_hint=np.ndarray)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._filtered: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "Filter":
            sig_data = await context.pull(self.id, "Signal")
            if sig_data is None or not isinstance(sig_data, np.ndarray) or len(sig_data) == 0:
                self._filtered = np.array([])
                return "Out"

            filter_type = await context.pull(self.id, "FilterType")
            arr = sig_data

            if filter_type == "Moving Average":
                window = int(await context.pull(self.id, "Window"))
                window = max(1, min(window, len(arr)))
                if window <= 1:
                    self._filtered = arr
                    return "Out"

                kernel = np.ones(window) / window
                padded = np.pad(arr, (window // 2, (window - 1) // 2), mode='edge')
                self._filtered = np.convolve(padded, kernel, mode='valid')
                return "Out"

            # Butterworth filters
            order = int(await context.pull(self.id, "Order"))
            order = max(1, min(order, 10))

            if len(arr) <= 3 * order:
                self._filtered = arr
                return "Out"

            try:
                if filter_type == "Low-pass":
                    cutoff = float(await context.pull(self.id, "Cutoff"))
                    cutoff = max(0.01, min(cutoff, 0.99))
                    sos = signal.butter(order, cutoff, btype='low', output='sos')
                    self._filtered = signal.sosfiltfilt(sos, arr)
                elif filter_type == "High-pass":
                    cutoff = float(await context.pull(self.id, "Cutoff"))
                    cutoff = max(0.01, min(cutoff, 0.99))
                    sos = signal.butter(order, cutoff, btype='high', output='sos')
                    self._filtered = signal.sosfiltfilt(sos, arr)
                elif filter_type == "Band-pass":
                    low_cutoff = float(await context.pull(self.id, "LowCutoff"))
                    high_cutoff = float(await context.pull(self.id, "HighCutoff"))
                    low_cutoff = max(0.01, min(low_cutoff, 0.98))
                    high_cutoff = max(low_cutoff + 0.01, min(high_cutoff, 0.99))
                    sos = signal.butter(order, [low_cutoff, high_cutoff], btype='bandpass', output='sos')
                    self._filtered = signal.sosfiltfilt(sos, arr)
                else:
                    self._filtered = arr
            except Exception as e:
                logger.error(f"Error in FilterBlock '{self.id}': {e}")
                self._filtered = arr

            return "Out"
        return None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Filtered":
            return self._filtered
        return None

    async def clear_data(self) -> None:
        self._filtered = np.array([])

@register_block("math/signal_processing/interpolate_1d")
class Interpolate1DBlock(BaseBlock):
    """Interpolates a 1D signal onto a new X-axis."""
    icon = "📉"
    display_name = "1D Interpolation"
    description = "Interpolates a 1D ndarray onto a new X-axis."

    inputs_def = [
        ExecIn("Execute"),
        DataIn("Y", type_hint=np.ndarray),
        DataIn("X", type_hint=np.ndarray),
        DataIn("New X", type_hint=np.ndarray),
        DataIn("Method", type_hint=str, default="linear", widget="dropdown",
               options=["linear", "nearest", "nearest-up", "zero", "slinear", "quadratic", "cubic", "previous", "next"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Interpolated Y", type_hint=np.ndarray)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._interpolated: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "Execute":
            y = await context.pull(self.id, "Y")
            x = await context.pull(self.id, "X")
            new_x = await context.pull(self.id, "New X")
            method = await context.pull(self.id, "Method")
            
            if not isinstance(y, np.ndarray) or not isinstance(x, np.ndarray) or not isinstance(new_x, np.ndarray):
                self._interpolated = np.array([])
                return "Out"
            
            if len(y) == 0 or len(x) == 0 or len(y) != len(x):
                self._interpolated = np.array([])
                return "Out"

            try:
                f = interpolate.interp1d(x, y, kind=method, fill_value="extrapolate")
                self._interpolated = f(new_x)
            except Exception as e:
                logger.error(f"Error in Interpolate1DBlock '{self.id}': {e}")
                self._interpolated = np.array([])

            return "Out"
        return None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Interpolated Y":
            return self._interpolated
        return None

    async def clear_data(self) -> None:
        self._interpolated = np.array([])

@register_block("math/signal_processing/interpolate_2d")
class Interpolate2DBlock(BaseBlock):
    """Interpolates a 2D array to a new size."""
    icon = "🖼️"
    display_name = "2D Interpolation"
    description = "Resizes a 2D ndarray (matrix) using interpolation."

    inputs_def = [
        ExecIn("Execute"),
        DataIn("Z", type_hint=np.ndarray),
        DataIn("New Size", type_hint=np.ndarray),
        DataIn("Order", type_hint=int, default=3, widget="dropdown",
               options=[0, 1, 3, 5])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Interpolated Z", type_hint=np.ndarray)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._interpolated: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "Execute":
            z = await context.pull(self.id, "Z")
            new_size = await context.pull(self.id, "New Size")
            order = await context.pull(self.id, "Order")
            
            if not isinstance(z, np.ndarray) or len(z) == 0:
                self._interpolated = np.array([])
                return "Out"
            
            if not isinstance(new_size, np.ndarray) or len(new_size) != 2:
                self._interpolated = np.array([])
                return "Out"

            try:
                z_arr = z
                if z_arr.ndim != 2:
                    self._interpolated = np.array([])
                    return "Out"

                current_shape = z_arr.shape
                target_shape = (int(new_size[0]), int(new_size[1]))
                
                zoom_factors = (target_shape[0] / current_shape[0], target_shape[1] / current_shape[1])
                
                try:
                    order_val = int(order)
                except (ValueError, TypeError):
                    order_val = 3
                
                if order_val not in [0, 1, 3, 5]:
                    order_val = 3
                
                self._interpolated = ndimage.zoom(z_arr, zoom_factors, order=order_val)
            except Exception as e:
                logger.error(f"Error in Interpolate2DBlock '{self.id}': {e}")
                self._interpolated = np.array([])

            return "Out"
        return None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Interpolated Z":
            return self._interpolated
        return None

    async def clear_data(self) -> None:
        self._interpolated = np.array([])


import time
import math
import random

@register_block("utility/function_generator")
class FunctionGeneratorBlock(BaseBlock):
    """Generates an instantaneous signal value based on time."""
    icon = "〰"
    display_name = "Function Generator"
    description = "Calculates the instantaneous value of a waveform based on the current system time."
    
    inputs_def = [
        ExecIn("Generate"),
        DataIn("Wave Type", type_hint=str, default="sine", options=["sine", "square", "triangle", "sawtooth", "dc"], widget="dropdown"),
        DataIn("Amplitude", type_hint=float, default=1.0, widget="number"),
        DataIn("Offset", type_hint=float, default=0.0, widget="number"),
        DataIn("Frequency", type_hint=float, default=1.0, widget="number"),
        DataIn("Phase (deg)", type_hint=float, default=0.0, widget="number"),
        DataIn("Noise Amp", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Value", type_hint=float)
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_value = 0.0
        self._start_time = time.time()

    async def execute(self, context: ExecutionContext, pin_name: str):
        if pin_name == "Generate":
            wave_type = await context.pull(self.id, "Wave Type") or "sine"
            amp = float(await context.pull(self.id, "Amplitude") or 1.0)
            offset = float(await context.pull(self.id, "Offset") or 0.0)
            freq = float(await context.pull(self.id, "Frequency") or 1.0)
            phase_deg = float(await context.pull(self.id, "Phase (deg)") or 0.0)
            noise_amp = float(await context.pull(self.id, "Noise Amp") or 0.0)
            
            t = time.time() - self._start_time
            phase_rad = math.radians(phase_deg)
            
            wt = 2 * math.pi * freq * t + phase_rad
            
            val = 0.0
            if wave_type == "sine":
                val = math.sin(wt)
            elif wave_type == "square":
                val = 1.0 if math.sin(wt) >= 0 else -1.0
            elif wave_type == "triangle":
                val = 2.0 / math.pi * math.asin(math.sin(wt))
            elif wave_type == "sawtooth":
                # standard sawtooth from -1 to 1
                val = 2.0 * (t * freq - math.floor(0.5 + t * freq))
            elif wave_type == "dc":
                val = 0.0
                
            val = (val * amp) + offset
            
            if noise_amp > 0:
                val += random.uniform(-noise_amp, noise_amp)
                
            self._current_value = val
            return "Out"
        return None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return self._current_value
        return None
