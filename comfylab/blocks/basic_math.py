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

import math
import random
import logging
from typing import Any, Optional, Dict
import numpy as np
from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, DataIn, DataOut, ExecutionContext, format_output, parse_shape

logger = logging.getLogger("comfylab.blocks.basic_math")


@register_block("math/basic/add")
class AddBlock(BaseBlock):
    """Pulls two numbers, A and B, and outputs their sum."""
    icon = "➕"
    display_name = "Add"
    description = "Pulls two numbers, A and B, and outputs their sum."
    
    inputs_def = [
        DataIn("A", type_hint=float, default=0.0, widget="number"),
        DataIn("B", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            return float(a) + float(b)
        return None


@register_block("math/basic/subtract")
class SubtractBlock(BaseBlock):
    """Pulls two numbers, A and B, and outputs A - B."""
    icon = "➖"
    display_name = "Subtract"
    description = "Pulls two numbers, A and B, and outputs A - B."
    
    inputs_def = [
        DataIn("A", type_hint=float, default=0.0, widget="number"),
        DataIn("B", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            return float(a) - float(b)
        return None


@register_block("math/basic/multiply")
class MultiplyBlock(BaseBlock):
    """Pulls two numbers, A and B, and outputs their product."""
    icon = "✖️"
    display_name = "Multiply"
    description = "Pulls two numbers, A and B, and outputs their product."
    
    inputs_def = [
        DataIn("A", type_hint=float, default=1.0, widget="number"),
        DataIn("B", type_hint=float, default=1.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            return float(a) * float(b)
        return None


@register_block("math/basic/divide")
class DivideBlock(BaseBlock):
    """Pulls two numbers, A and B, and outputs A / B."""
    icon = "➗"
    display_name = "Divide"
    description = "Pulls two numbers, A and B, and outputs A / B."
    
    inputs_def = [
        DataIn("A", type_hint=float, default=1.0, widget="number"),
        DataIn("B", type_hint=float, default=1.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            denom = float(b)
            if denom == 0.0:
                raise ZeroDivisionError("Division by zero in math/basic/divide block.")
            return float(a) / denom
        return None


@register_block("math/basic/power")
class PowerBlock(BaseBlock):
    """Raises base A to exponent B (A^B)."""
    icon = "🔋"
    display_name = "Power"
    description = "Raises base A to exponent B (A^B)."
    
    inputs_def = [
        DataIn("Base", type_hint=float, default=2.0, widget="number"),
        DataIn("Exponent", type_hint=float, default=3.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            base = await context.pull(self.id, "Base")
            exp = await context.pull(self.id, "Exponent")
            return float(base) ** float(exp)
        return None


@register_block("math/basic/trig")
class TrigBlock(BaseBlock):
    """Computes trig functions (sin, cos, tan, and their inverses/hyperbolics)."""
    icon = "📐"
    display_name = "Trigonometry"
    description = "Computes trig and hyperbolic functions in radians or degrees. Supports arrays."
    
    inputs_def = [
        DataIn("Value", type_hint=Any, default=0.0),
        DataIn("Function", type_hint=str, default="sin", widget="dropdown", options=[
            "sin", "cos", "tan", "asin", "acos", "atan",
            "sinh", "cosh", "tanh", "asinh", "acosh", "atanh"
        ]),
        DataIn("UseDegrees", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            val = await context.pull(self.id, "Value")
            if val is None:
                val = 0.0
            func = await context.pull(self.id, "Function")
            deg = bool(await context.pull(self.id, "UseDegrees"))
            
            # Convert to numpy array to transparently handle scalars and arrays
            val_np = np.asarray(val, dtype=float)
            
            angle = val_np
            is_direct = func in ["sin", "cos", "tan"]
            if deg and is_direct:
                angle = np.radians(angle)
                
            res = None
            if func == "sin": res = np.sin(angle)
            elif func == "cos": res = np.cos(angle)
            elif func == "tan": res = np.tan(angle)
            elif func == "asin": res = np.arcsin(angle)
            elif func == "acos": res = np.arccos(angle)
            elif func == "atan": res = np.arctan(angle)
            elif func == "sinh": res = np.sinh(angle)
            elif func == "cosh": res = np.cosh(angle)
            elif func == "tanh": res = np.tanh(angle)
            elif func == "asinh": res = np.arcsinh(angle)
            elif func == "acosh": res = np.arccosh(angle)
            elif func == "atanh": res = np.arctanh(angle)
            else: res = val_np * 0.0
            
            is_inverse = func in ["asin", "acos", "atan"]
            if deg and is_inverse:
                res = np.degrees(res)

            return format_output(res)
        return None


@register_block("math/random/random")
class RandomBlock(BaseBlock):
    """Outputs a random float or int in the range [Min, Max]."""
    icon = "🎲"
    display_name = "Random Number"
    description = "Outputs a random number in the range [Min, Max]."
    
    inputs_def = [
        DataIn("Min", type_hint=float, default=0.0, widget="number"),
        DataIn("Max", type_hint=float, default=1.0, widget="number"),
        DataIn("IntegerMode", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Value", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            min_val = float(await context.pull(self.id, "Min"))
            max_val = float(await context.pull(self.id, "Max"))
            int_mode = bool(await context.pull(self.id, "IntegerMode"))
            
            if int_mode:
                return float(random.randint(int(min_val), int(max_val)))
            return random.uniform(min_val, max_val)
        return None


@register_block("math/random/random_array")
class RandomArrayBlock(BaseBlock):
    """Outputs a random numeric array (NDArray) in the range [Min, Max] with a given shape."""
    icon = "🎲"
    display_name = "Random Array"
    description = "Outputs a random NDArray in the range [Min, Max]."
    
    inputs_def = [
        DataIn("Shape", type_hint=Any, default="100", widget="text"),
        DataIn("Min", type_hint=float, default=0.0, widget="number"),
        DataIn("Max", type_hint=float, default=1.0, widget="number"),
        DataIn("IntegerMode", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Array", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Array":
            shape_raw = await context.pull(self.id, "Shape")
            min_val = float(await context.pull(self.id, "Min"))
            max_val = float(await context.pull(self.id, "Max"))
            int_mode = bool(await context.pull(self.id, "IntegerMode"))

            shape = parse_shape(shape_raw)

            if int_mode:
                return np.random.randint(int(min_val), int(max_val) + 1, size=shape)
            return np.random.uniform(min_val, max_val, size=shape)
        return None


@register_block("math/basic/calculator")
class CalculatorBlock(BaseBlock):
    """Evaluates a mathematical expression with dynamic variable inputs."""
    icon = "🧮"
    display_name = "Calculator"
    description = "Evaluates a mathematical expression with variable inputs."
    default_width = 240
    ui_behavior = {"custom_widget": "calculator", "render_standard_inputs": True}

    inputs_def = []
    outputs_def = [
        DataOut("Result", type_hint=float)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        variables = self.properties.get("variables", ["a", "b"])
        if isinstance(variables, str):
            variables = [v.strip() for v in variables.split(",") if v.strip()]
        
        for var in variables:
            self.inputs[var] = DataIn(var, type_hint=float, default=0.0, widget="number")

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            expression = self.properties.get("expression", self.properties.get("Expression", "a + b"))
            if not expression:
                return 0.0

            expr_processed = expression.replace("^", "**")

            variables = self.properties.get("variables", ["a", "b"])
            if isinstance(variables, str):
                variables = [v.strip() for v in variables.split(",") if v.strip()]

            local_vars = {}
            for var in variables:
                val = await context.pull(self.id, var)
                try:
                    local_vars[var] = float(val) if val is not None else 0.0
                except (ValueError, TypeError):
                    local_vars[var] = 0.0

            math_namespace = {
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'asin': math.asin, 'acos': math.acos, 'atan': math.atan, 'atan2': math.atan2,
                'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
                'exp': math.exp, 'log': math.log, 'log10': math.log10,
                'sqrt': math.sqrt, 'abs': abs, 'pi': math.pi, 'e': math.e,
                'min': min, 'max': max, 'round': round, 'floor': math.floor, 'ceil': math.ceil
            }
            eval_namespace = {**math_namespace, **local_vars}

            try:
                result = eval(expr_processed, {"__builtins__": {}}, eval_namespace)
                return float(result)
            except Exception as e:
                logger.error(f"Error evaluating Calculator expression '{expression}': {e}")
                raise e
        return None


@register_block("math/operations/linear_scale")
class LinearScaleBlock(BaseBlock):
    """Scales an input value or list of values using y = ax + b."""
    icon = "⚖️"
    display_name = "Linear Scale"
    description = "Scales a value or array linearly: ax + b."

    inputs_def = [
        DataIn("X", type_hint=Any),
        DataIn("A", type_hint=float, default=1.0, widget="number"),
        DataIn("B", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [
        DataOut("Result", type_hint=Any)
    ]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            a = float(await context.pull(self.id, "A"))
            b = float(await context.pull(self.id, "B"))

            if x is None:
                return None

            if isinstance(x, np.ndarray):
                return x * a + b
            elif isinstance(x, list):
                try:
                    return [float(item) * a + b for item in x]
                except (ValueError, TypeError):
                    pass
            try:
                return float(x) * a + b
            except (ValueError, TypeError):
                return None
        return None
