# Copyright (C) 2026 Paulo Felipe Jarschel

import logging
import math
from typing import Any
import numpy as np
import scipy.signal
import scipy.special

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, DataIn, DataOut, ExecutionContext, format_output

logger = logging.getLogger("comfylab.blocks.math_functions")

@register_block("math/functions/gaussian")
class GaussianBlock(BaseBlock):
    """Gaussian function generator."""
    icon = "🔔"
    display_name = "Gaussian"
    description = "Evaluates a Gaussian function: Amplitude * exp(-((X - Center)^2) / (2 * Width^2))"
    
    inputs_def = [
        DataIn("X", type_hint=Any, default=0.0),
        DataIn("Amplitude", type_hint=float, default=1.0, widget="number"),
        DataIn("Center", type_hint=float, default=0.0, widget="number"),
        DataIn("Width", type_hint=float, default=1.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            if x is None: return 0.0
            x_np = np.asarray(x, dtype=float)
            amp = float(await context.pull(self.id, "Amplitude"))
            center = float(await context.pull(self.id, "Center"))
            width = float(await context.pull(self.id, "Width"))
            
            if width == 0:
                return format_output(np.where(x_np == center, amp, 0.0))
            
            res = amp * np.exp(-((x_np - center)**2) / (2 * width**2))
            return format_output(res)
        return None

@register_block("math/functions/lorentzian")
class LorentzianBlock(BaseBlock):
    """Lorentzian function generator."""
    icon = "📈"
    display_name = "Lorentzian"
    description = "Evaluates a Lorentzian function: Amplitude * (Gamma^2 / ((X - Center)^2 + Gamma^2))"
    
    inputs_def = [
        DataIn("X", type_hint=Any, default=0.0),
        DataIn("Amplitude", type_hint=float, default=1.0, widget="number"),
        DataIn("Center", type_hint=float, default=0.0, widget="number"),
        DataIn("Gamma", type_hint=float, default=1.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            if x is None: return 0.0
            x_np = np.asarray(x, dtype=float)
            amp = float(await context.pull(self.id, "Amplitude"))
            center = float(await context.pull(self.id, "Center"))
            gamma = float(await context.pull(self.id, "Gamma"))
            
            if gamma == 0:
                return format_output(np.where(x_np == center, amp, 0.0))
                
            res = amp * (gamma**2 / ((x_np - center)**2 + gamma**2))
            return format_output(res)
        return None

@register_block("math/functions/pulse")
class PulseBlock(BaseBlock):
    """Pulse wave generator."""
    icon = "🎛️"
    display_name = "Pulse Wave"
    description = "Generates a periodic pulse/square wave."
    
    inputs_def = [
        DataIn("X", type_hint=Any, default=0.0),
        DataIn("Frequency", type_hint=float, default=1.0, widget="number"),
        DataIn("Amplitude", type_hint=float, default=1.0, widget="number"),
        DataIn("DutyCycle", type_hint=float, default=50.0, widget="number"),
        DataIn("Phase", type_hint=float, default=0.0, widget="number"),
        DataIn("Offset", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            if x is None: return 0.0
            x_np = np.asarray(x, dtype=float)
            freq = float(await context.pull(self.id, "Frequency"))
            amp = float(await context.pull(self.id, "Amplitude"))
            duty = float(await context.pull(self.id, "DutyCycle")) / 100.0
            phase = float(await context.pull(self.id, "Phase"))
            offset = float(await context.pull(self.id, "Offset"))
            
            duty = max(0.0, min(1.0, duty)) # Clamp duty cycle
            
            # scipy.signal.square returns values in [-1, 1]
            wave = scipy.signal.square(2 * np.pi * freq * x_np + phase, duty=duty)
            # Map [-1, 1] to [0, Amplitude] and add Offset
            res = (wave + 1) / 2 * amp + offset
            return format_output(res)
        return None

@register_block("math/functions/step")
class StepBlock(BaseBlock):
    """Step function generator."""
    icon = "⏭️"
    display_name = "Step Function"
    description = "Generates a single step or pulse between Start and End points."
    
    inputs_def = [
        DataIn("X", type_hint=Any, default=0.0),
        DataIn("Start", type_hint=float, default=0.0, widget="number"),
        DataIn("End", type_hint=float, default=None, widget="number"),
        DataIn("Amplitude", type_hint=float, default=1.0, widget="number"),
        DataIn("Invert", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            if x is None: return 0.0
            x_np = np.asarray(x, dtype=float)
            start = float(await context.pull(self.id, "Start"))
            end_val = await context.pull(self.id, "End")
            end = float(end_val) if end_val is not None else float('inf')
            amp = float(await context.pull(self.id, "Amplitude"))
            invert = bool(await context.pull(self.id, "Invert"))
            
            cond = (x_np >= start) & (x_np <= end)
            if invert:
                res = np.where(cond, 0.0, amp)
            else:
                res = np.where(cond, amp, 0.0)
                
            return format_output(res)
        return None

@register_block("math/functions/triangle")
class TriangleBlock(BaseBlock):
    """Triangle wave generator."""
    icon = "◮"
    display_name = "Triangle Wave"
    description = "Generates a periodic triangle wave."
    
    inputs_def = [
        DataIn("X", type_hint=Any, default=0.0),
        DataIn("Frequency", type_hint=float, default=1.0, widget="number"),
        DataIn("Amplitude", type_hint=float, default=1.0, widget="number"),
        DataIn("Phase", type_hint=float, default=0.0, widget="number"),
        DataIn("Offset", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            if x is None: return 0.0
            x_np = np.asarray(x, dtype=float)
            freq = float(await context.pull(self.id, "Frequency"))
            amp = float(await context.pull(self.id, "Amplitude"))
            phase = float(await context.pull(self.id, "Phase"))
            offset = float(await context.pull(self.id, "Offset"))
            
            # scipy.signal.sawtooth with width=0.5 makes a triangle wave [-1, 1]
            wave = scipy.signal.sawtooth(2 * np.pi * freq * x_np + phase, 0.5)
            res = wave * amp + offset
            return format_output(res)
        return None

@register_block("math/functions/sawtooth")
class SawtoothBlock(BaseBlock):
    """Sawtooth wave generator."""
    icon = "◢"
    display_name = "Sawtooth Wave"
    description = "Generates a periodic sawtooth wave."
    
    inputs_def = [
        DataIn("X", type_hint=Any, default=0.0),
        DataIn("Frequency", type_hint=float, default=1.0, widget="number"),
        DataIn("Amplitude", type_hint=float, default=1.0, widget="number"),
        DataIn("Phase", type_hint=float, default=0.0, widget="number"),
        DataIn("Offset", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            if x is None: return 0.0
            x_np = np.asarray(x, dtype=float)
            freq = float(await context.pull(self.id, "Frequency"))
            amp = float(await context.pull(self.id, "Amplitude"))
            phase = float(await context.pull(self.id, "Phase"))
            offset = float(await context.pull(self.id, "Offset"))
            
            # scipy.signal.sawtooth with width=1 makes a sawtooth wave [-1, 1]
            wave = scipy.signal.sawtooth(2 * np.pi * freq * x_np + phase, 1)
            res = wave * amp + offset
            return format_output(res)
        return None

@register_block("math/functions/sine")
class SineBlock(BaseBlock):
    """Sine wave generator."""
    icon = "∿"
    display_name = "Sine Wave"
    description = "Generates a periodic sine wave."
    
    inputs_def = [
        DataIn("X", type_hint=Any, default=0.0),
        DataIn("Frequency", type_hint=float, default=1.0, widget="number"),
        DataIn("Amplitude", type_hint=float, default=1.0, widget="number"),
        DataIn("Phase", type_hint=float, default=0.0, widget="number"),
        DataIn("Offset", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            if x is None: return 0.0
            x_np = np.asarray(x, dtype=float)
            freq = float(await context.pull(self.id, "Frequency"))
            amp = float(await context.pull(self.id, "Amplitude"))
            phase = float(await context.pull(self.id, "Phase"))
            offset = float(await context.pull(self.id, "Offset"))
            
            res = amp * np.sin(2 * np.pi * freq * x_np + phase) + offset
            return format_output(res)
        return None

@register_block("math/functions/bessel")
class BesselBlock(BaseBlock):
    """Bessel function generator."""
    icon = "𝑱"
    display_name = "Bessel Function"
    description = "Evaluates Bessel functions of the first (J) or second (Y) kind."
    
    inputs_def = [
        DataIn("X", type_hint=Any, default=0.0),
        DataIn("Order", type_hint=float, default=0.0, widget="number"),
        DataIn("Kind", type_hint=str, default="first (J)", widget="dropdown", options=["first (J)", "second (Y)"])
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            if x is None: return 0.0
            x_np = np.asarray(x, dtype=float)
            order = float(await context.pull(self.id, "Order"))
            kind = await context.pull(self.id, "Kind")
            
            if kind == "first (J)":
                res = scipy.special.jv(order, x_np)
            else:
                res = scipy.special.yv(order, x_np)
                
            return format_output(res)
        return None

@register_block("math/functions/polynom")
class PolynomBlock(BaseBlock):
    """Polynomial function generator."""
    icon = "𝑃"
    display_name = "Polynomial"
    description = "Evaluates a polynomial using an array of coefficients (highest degree first)."
    
    inputs_def = [
        DataIn("X", type_hint=Any, default=0.0),
        DataIn("Coefficients", type_hint=list, default=[1.0, 0.0])
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            if x is None: return 0.0
            x_np = np.asarray(x, dtype=float)
            coeffs = await context.pull(self.id, "Coefficients")
            if not isinstance(coeffs, (list, tuple, np.ndarray)):
                coeffs = [float(coeffs)]
                
            # Reverse coeffs so index 0 is the constant, index 1 is x, index 2 is x^2...
            coeffs = list(coeffs)[::-1]
            
            res = np.polyval(coeffs, x_np)
            return format_output(res)
        return None

@register_block("math/functions/log")
class LogBlock(BaseBlock):
    """Logarithm function generator."""
    icon = "㏒"
    display_name = "Logarithm"
    description = "Evaluates the logarithm of X with a given Base."
    
    inputs_def = [
        DataIn("X", type_hint=Any, default=1.0),
        DataIn("Base", type_hint=float, default=math.e, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            if x is None: return 1.0
            x_np = np.asarray(x, dtype=float)
            base = float(await context.pull(self.id, "Base"))
            
            if base == math.e:
                res = np.log(x_np)
            elif base == 10:
                res = np.log10(x_np)
            elif base == 2:
                res = np.log2(x_np)
            else:
                res = np.log(x_np) / np.log(base)
                
            return format_output(res)
        return None

@register_block("math/functions/exponential")
class ExponentialBlock(BaseBlock):
    """Exponential function generator."""
    icon = "𝑒^"
    display_name = "Exponential"
    description = "Evaluates an exponential function: Amplitude * (Base ^ X)"
    
    inputs_def = [
        DataIn("X", type_hint=Any, default=0.0),
        DataIn("Amplitude", type_hint=float, default=1.0, widget="number"),
        DataIn("Base", type_hint=float, default=math.e, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            if x is None: return 0.0
            x_np = np.asarray(x, dtype=float)
            amp = float(await context.pull(self.id, "Amplitude"))
            base = float(await context.pull(self.id, "Base"))
            
            if base == math.e:
                res = amp * np.exp(x_np)
            else:
                res = amp * (base ** x_np)
                
            return format_output(res)
        return None
