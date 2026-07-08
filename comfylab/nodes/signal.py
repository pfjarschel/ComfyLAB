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

logger = logging.getLogger("comfylab.nodes.signal")

from comfylab.engine.registry import register_node
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext


@register_node("math/signal_processing/fft")
class FFTNode(BaseNode):
    """Computes a Discrete Fourier Transform (spectrum magnitude) of a signal."""
    icon = "📈"
    display_name = "FFT Spectrum"
    description = "Computes a Discrete Fourier Transform (spectrum magnitude) of a signal."

    inputs_def = [
        ExecIn("Analyze"),
        DataIn("Signal", type_hint=list),
        DataIn("X", type_hint=list, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Spectrum", type_hint=list),
        DataOut("Phase", type_hint=list),
        DataOut("Frequencies", type_hint=list),
        DataOut("Length", type_hint=int)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._last_spectrum: List[float] = []
        self._last_phase: List[float] = []
        self._last_freqs: Optional[List[float]] = None
        self._last_length: int = 0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        signal_input = await context.pull(self.id, "Signal")
        x_input = await context.pull(self.id, "X")

        if signal_input is None or not isinstance(signal_input, list) or len(signal_input) == 0:
            self._last_spectrum = []
            self._last_phase = []
            self._last_freqs = None
            self._last_length = 0
            return "Out"

        try:
            sig = np.asarray(signal_input, dtype=float)
        except (ValueError, TypeError):
            self._last_spectrum = []
            self._last_phase = []
            self._last_freqs = None
            self._last_length = 0
            return "Out"

        N = len(sig)
        fft_result = np.fft.rfft(sig)
        magnitude = np.abs(fft_result) / N
        phase = np.angle(fft_result)
        
        self._last_spectrum = magnitude.tolist()
        self._last_phase = phase.tolist()
        self._last_length = N

        if x_input is not None and isinstance(x_input, list) and len(x_input) == N and N >= 2:
            try:
                x = np.asarray(x_input, dtype=float)
                dx = float(x[1] - x[0])
                self._last_freqs = np.fft.rfftfreq(N, d=dx).tolist()
            except (ValueError, TypeError, IndexError):
                self._last_freqs = None
        else:
            self._last_freqs = None

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Spectrum":
            return self._last_spectrum
        if pin_name == "Phase":
            return self._last_phase
        if pin_name == "Frequencies":
            return self._last_freqs
        if pin_name == "Length":
            return self._last_length
        return None

    async def clear_data(self) -> None:
        self._last_spectrum = []
        self._last_phase = []
        self._last_freqs = None
        self._last_length = 0


@register_node("math/signal_processing/ifft")
class IFFTNode(BaseNode):
    """Computes an Inverse Discrete Fourier Transform to reconstruct a time-domain signal."""
    icon = "📉"
    display_name = "Inverse FFT"
    description = "Reconstructs a time-domain signal from Magnitude (Spectrum) and Phase arrays."

    inputs_def = [
        ExecIn("Reconstruct"),
        DataIn("Spectrum", type_hint=list),
        DataIn("Phase", type_hint=list, optional=True),
        DataIn("Length", type_hint=int, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Signal", type_hint=list)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._last_signal: List[float] = []

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        mag_input = await context.pull(self.id, "Spectrum")
        phase_input = await context.pull(self.id, "Phase")
        length_input = await context.pull(self.id, "Length")

        if mag_input is None or not isinstance(mag_input, list) or len(mag_input) == 0:
            self._last_signal = []
            return "Out"

        try:
            mag = np.asarray(mag_input, dtype=float)
            
            if phase_input is not None and isinstance(phase_input, list) and len(phase_input) == len(mag):
                phase = np.asarray(phase_input, dtype=float)
            else:
                phase = np.zeros_like(mag)
                
            n_recon = int(length_input) if length_input is not None else 2 * (len(mag) - 1)
            
            # The FFTNode scales magnitude by dividing by N. We must multiply it back.
            mag_scaled = mag * n_recon
            complex_spectrum = mag_scaled * np.exp(1j * phase)
            
            sig = np.fft.irfft(complex_spectrum, n=n_recon)
            self._last_signal = sig.tolist()
        except (ValueError, TypeError, Exception) as e:
            logger.error(f"Error in IFFTNode '{self.id}': {e}")
            self._last_signal = []

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Signal":
            return self._last_signal
        return None

    async def clear_data(self) -> None:
        self._last_signal = []


@register_node("math/signal_processing/filter")
class FilterNode(BaseNode):
    """Filters a signal using moving average or Butterworth low/high/band-pass filter."""
    icon = "📈"
    display_name = "Signal Filter"
    description = "Filters a 1D array using moving average or Butterworth filters with normalized frequency."

    inputs_def = [
        ExecIn("Filter"),
        DataIn("Signal", type_hint=list),
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
        DataOut("Filtered", type_hint=list)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._filtered: List[float] = []

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "Filter":
            sig_data = await context.pull(self.id, "Signal")
            if not sig_data or not isinstance(sig_data, list):
                self._filtered = []
                return "Out"

            filter_type = await context.pull(self.id, "FilterType")

            try:
                arr = np.asarray(sig_data, dtype=float)
            except (ValueError, TypeError):
                self._filtered = []
                return "Out"

            if len(arr) == 0:
                self._filtered = []
                return "Out"

            if filter_type == "Moving Average":
                window = int(await context.pull(self.id, "Window"))
                window = max(1, min(window, len(arr)))
                if window <= 1:
                    self._filtered = arr.tolist()
                    return "Out"

                kernel = np.ones(window) / window
                padded = np.pad(arr, (window // 2, (window - 1) // 2), mode='edge')
                self._filtered = np.convolve(padded, kernel, mode='valid').tolist()
                return "Out"

            # Butterworth filters
            order = int(await context.pull(self.id, "Order"))
            order = max(1, min(order, 10))

            if len(arr) <= 3 * order:
                self._filtered = arr.tolist()
                return "Out"

            try:
                if filter_type == "Low-pass":
                    cutoff = float(await context.pull(self.id, "Cutoff"))
                    cutoff = max(0.01, min(cutoff, 0.99))
                    sos = signal.butter(order, cutoff, btype='low', output='sos')
                    self._filtered = signal.sosfiltfilt(sos, arr).tolist()
                elif filter_type == "High-pass":
                    cutoff = float(await context.pull(self.id, "Cutoff"))
                    cutoff = max(0.01, min(cutoff, 0.99))
                    sos = signal.butter(order, cutoff, btype='high', output='sos')
                    self._filtered = signal.sosfiltfilt(sos, arr).tolist()
                elif filter_type == "Band-pass":
                    low_cutoff = float(await context.pull(self.id, "LowCutoff"))
                    high_cutoff = float(await context.pull(self.id, "HighCutoff"))
                    low_cutoff = max(0.01, min(low_cutoff, 0.98))
                    high_cutoff = max(low_cutoff + 0.01, min(high_cutoff, 0.99))
                    sos = signal.butter(order, [low_cutoff, high_cutoff], btype='bandpass', output='sos')
                    self._filtered = signal.sosfiltfilt(sos, arr).tolist()
                else:
                    self._filtered = arr.tolist()
            except Exception as e:
                logger.error(f"Error in FilterNode '{self.id}': {e}")
                self._filtered = arr.tolist()

            return "Out"
        return None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Filtered":
            return self._filtered
        return None

    async def clear_data(self) -> None:
        self._filtered = []

@register_node("math/signal_processing/interpolate_1d")
class Interpolate1DNode(BaseNode):
    """Interpolates a 1D signal onto a new X-axis."""
    icon = "📉"
    display_name = "1D Interpolation"
    description = "Interpolates a 1D signal onto a new X-axis."

    inputs_def = [
        ExecIn("Execute"),
        DataIn("Y", type_hint=list),
        DataIn("X", type_hint=list),
        DataIn("New X", type_hint=list),
        DataIn("Method", type_hint=str, default="linear", widget="dropdown",
               options=["linear", "nearest", "nearest-up", "zero", "slinear", "quadratic", "cubic", "previous", "next"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Interpolated Y", type_hint=list)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._interpolated: List[float] = []

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "Execute":
            y = await context.pull(self.id, "Y")
            x = await context.pull(self.id, "X")
            new_x = await context.pull(self.id, "New X")
            method = await context.pull(self.id, "Method")
            
            if not isinstance(y, list) or not isinstance(x, list) or not isinstance(new_x, list):
                self._interpolated = []
                return "Out"
            
            if len(y) == 0 or len(x) == 0 or len(y) != len(x):
                self._interpolated = []
                return "Out"

            try:
                f = interpolate.interp1d(x, y, kind=method, fill_value="extrapolate")
                self._interpolated = f(new_x).tolist()
            except Exception as e:
                logger.error(f"Error in Interpolate1DNode '{self.id}': {e}")
                self._interpolated = []

            return "Out"
        return None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Interpolated Y":
            return self._interpolated
        return None

    async def clear_data(self) -> None:
        self._interpolated = []

@register_node("math/signal_processing/interpolate_2d")
class Interpolate2DNode(BaseNode):
    """Interpolates a 2D array to a new size."""
    icon = "🖼️"
    display_name = "2D Interpolation"
    description = "Resizes a 2D array (matrix) using interpolation."

    inputs_def = [
        ExecIn("Execute"),
        DataIn("Z", type_hint=list),
        DataIn("New Size", type_hint=list),
        DataIn("Order", type_hint=int, default=3, widget="dropdown",
               options=[0, 1, 3, 5])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Interpolated Z", type_hint=list)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._interpolated: List[List[float]] = []

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "Execute":
            z = await context.pull(self.id, "Z")
            new_size = await context.pull(self.id, "New Size")
            order = await context.pull(self.id, "Order")
            
            if not isinstance(z, list) or len(z) == 0:
                self._interpolated = []
                return "Out"
            
            if not isinstance(new_size, list) or len(new_size) != 2:
                self._interpolated = []
                return "Out"

            try:
                z_arr = np.array(z)
                if z_arr.ndim != 2:
                    self._interpolated = []
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
                
                z_zoomed = ndimage.zoom(z_arr, zoom_factors, order=order_val)
                self._interpolated = z_zoomed.tolist()
            except Exception as e:
                logger.error(f"Error in Interpolate2DNode '{self.id}': {e}")
                self._interpolated = []

            return "Out"
        return None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Interpolated Z":
            return self._interpolated
        return None

    async def clear_data(self) -> None:
        self._interpolated = []
