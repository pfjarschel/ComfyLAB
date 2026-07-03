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
        DataOut("Frequencies", type_hint=list)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._last_spectrum: List[float] = []
        self._last_freqs: Optional[List[float]] = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        signal_input = await context.pull(self.id, "Signal")
        x_input = await context.pull(self.id, "X")

        if signal_input is None or not isinstance(signal_input, list) or len(signal_input) == 0:
            self._last_spectrum = []
            self._last_freqs = None
            return "Out"

        try:
            sig = np.asarray(signal_input, dtype=float)
        except (ValueError, TypeError):
            self._last_spectrum = []
            self._last_freqs = None
            return "Out"

        N = len(sig)
        magnitude = np.abs(np.fft.rfft(sig)) / N
        self._last_spectrum = magnitude.tolist()

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
        if pin_name == "Frequencies":
            return self._last_freqs
        return None

    async def clear_data(self) -> None:
        self._last_spectrum = []
        self._last_freqs = None


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

