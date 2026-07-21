# Copyright (C) 2026 Paulo Felipe Jarschel

import logging
import math
import numpy as np
from scipy.optimize import curve_fit
from typing import Any, Optional, Dict

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, DataIn, DataOut, ExecutionContext

logger = logging.getLogger("comfylab.blocks.math_fit")

def format_output(res: Any) -> Any:
    if isinstance(res, np.ndarray):
        res = np.nan_to_num(res, nan=0.0, posinf=1e99, neginf=-1e99)
        if res.ndim == 0:
            return float(res)
        return res
    elif isinstance(res, float):
        if math.isnan(res): return 0.0
        if math.isinf(res): return 1e99 if res > 0 else -1e99
        return res
    return res

@register_block("math/analysis/curve_fit")
class CurveFitBlock(BaseBlock):
    """Fits X and Y data to common mathematical functions."""
    icon = "📈"
    display_name = "Curve Fit"
    description = "Fits X and Y data to common mathematical functions using least squares."
    default_width = 240
    
    inputs_def = [
        DataIn("X", type_hint=np.ndarray),
        DataIn("Y", type_hint=np.ndarray),
        DataIn("FunctionType", type_hint=str, default="Linear", widget="dropdown", 
               options=["Linear", "Polynomial", "Exponential", "Logarithmic", "Power", "Sigmoid", "Gaussian", "Lorentzian", "Sine"]),
        DataIn("PolyDegree", type_hint=int, default=2, widget="number"),
        DataIn("InitialGuesses", type_hint=list, default=None)
    ]
    outputs_def = [
        DataOut("Parameters", type_hint=np.ndarray),
        DataOut("FitY", type_hint=np.ndarray)
    ]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        x = await context.pull(self.id, "X")
        y = await context.pull(self.id, "Y")
        
        if x is None or y is None:
            return [] if pin_name == "Parameters" else []
            
        x_np = np.asarray(x, dtype=float)
        y_np = np.asarray(y, dtype=float)
        
        if x_np.size == 0 or y_np.size == 0 or x_np.size != y_np.size:
            return [] if pin_name == "Parameters" else []
            
        func_type = await context.pull(self.id, "FunctionType")
        poly_degree = int(await context.pull(self.id, "PolyDegree"))
        p0_input = await context.pull(self.id, "InitialGuesses")
        
        p0 = None
        if p0_input is not None:
            if isinstance(p0_input, (list, tuple, np.ndarray)):
                p0 = [float(p) for p in p0_input]
            else:
                p0 = [float(p0_input)]

        def func_linear(x, a, b): return a * x + b
        def func_exp(x, a, b, c): return a * np.exp(b * x) + c
        def func_log(x, a, b, c): 
            x_safe = np.where(x > 0, x, 1e-10)
            return a * np.log(b * x_safe) + c
        def func_power(x, a, b, c): 
            x_safe = np.where(x > 0, x, 1e-10)
            return a * np.power(x_safe, b) + c
        def func_sigmoid(x, a, b, c, d): return a / (1 + np.exp(-c * (x - d))) + b
        def func_gaussian(x, a, b, c): return a * np.exp(-((x - b)**2) / (2 * c**2 + 1e-10))
        def func_lorentzian(x, a, b, c): return a * (c**2 / ((x - b)**2 + c**2 + 1e-10))
        def func_sine(x, a, b, c, d): return a * np.sin(b * x + c) + d

        fit_func = None
        if func_type == "Linear":
            fit_func = func_linear
            num_params = 2
        elif func_type == "Exponential":
            fit_func = func_exp
            num_params = 3
        elif func_type == "Logarithmic":
            fit_func = func_log
            num_params = 3
        elif func_type == "Power":
            fit_func = func_power
            num_params = 3
        elif func_type == "Sigmoid":
            fit_func = func_sigmoid
            num_params = 4
        elif func_type == "Gaussian":
            fit_func = func_gaussian
            num_params = 3
        elif func_type == "Lorentzian":
            fit_func = func_lorentzian
            num_params = 3
        elif func_type == "Sine":
            fit_func = func_sine
            num_params = 4
        elif func_type == "Polynomial":
            pass
        else:
            fit_func = func_linear
            num_params = 2

        try:
            if func_type == "Polynomial":
                deg = max(1, poly_degree)
                coeffs = np.polyfit(x_np, y_np, deg)
                y_fit = np.polyval(coeffs, x_np)
                params = coeffs # highest degree first
            else:
                if p0 is not None and len(p0) != num_params:
                    if len(p0) < num_params:
                        p0 = p0 + [1.0] * (num_params - len(p0))
                    else:
                        p0 = p0[:num_params]
                
                popt, _ = curve_fit(fit_func, x_np, y_np, p0=p0, maxfev=10000)
                y_fit = fit_func(x_np, *popt)
                params = popt
                
        except Exception as e:
            logger.error(f"Curve fitting failed for {func_type}: {e}")
            if func_type == "Polynomial":
                params = np.zeros(poly_degree + 1)
            else:
                params = np.zeros(num_params)
            y_fit = np.zeros_like(x_np)

        if pin_name == "Parameters":
            return params
        elif pin_name == "FitY":
            return format_output(y_fit)

        return None


@register_block("math/analysis/custom_curve_fit")
class CustomFunctionFitBlock(BaseBlock):
    """Fits X and Y data to a user-defined mathematical string expression."""
    icon = "📐"
    display_name = "Custom Function Fit"
    description = "Fits X and Y data to a user-defined mathematical string expression."
    default_width = 280
    ui_behavior = {"custom_widget": "calculator", "render_standard_inputs": True}
    
    inputs_def = [
        DataIn("X", type_hint=np.ndarray),
        DataIn("Y", type_hint=np.ndarray),
        DataIn("InitialGuesses", type_hint=list, default=None)
    ]
    outputs_def = [
        DataOut("Parameters", type_hint=np.ndarray),
        DataOut("FitY", type_hint=np.ndarray)
    ]
    
    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        x = await context.pull(self.id, "X")
        y = await context.pull(self.id, "Y")
        
        if x is None or y is None:
            return [] if pin_name == "Parameters" else []
            
        x_np = np.asarray(x, dtype=float)
        y_np = np.asarray(y, dtype=float)
        
        if x_np.size == 0 or y_np.size == 0 or x_np.size != y_np.size:
            return [] if pin_name == "Parameters" else []

        expression = self.properties.get("expression", self.properties.get("Expression", "a * x + b"))
        if not expression:
            return [] if pin_name == "Parameters" else []

        expr_processed = expression.replace("^", "**")

        variables = self.properties.get("variables", ["a", "b"])
        if isinstance(variables, str):
            variables = [v.strip() for v in variables.split(",") if v.strip()]
            
        if len(variables) == 0:
            return [] if pin_name == "Parameters" else []

        p0_input = await context.pull(self.id, "InitialGuesses")
        p0 = None
        if p0_input is not None:
            if isinstance(p0_input, (list, tuple, np.ndarray)):
                p0 = [float(p) for p in p0_input]
            else:
                p0 = [float(p0_input)]
                
        num_params = len(variables)
        if p0 is not None and len(p0) != num_params:
            if len(p0) < num_params:
                p0 = p0 + [1.0] * (num_params - len(p0))
            else:
                p0 = p0[:num_params]

        eval_namespace = {
            name: getattr(np, name) for name in dir(np) if not name.startswith("_")
        }
        
        def dynamic_fit_func(x_val, *params):
            local_vars = {"x": x_val, "X": x_val}
            for i, var_name in enumerate(variables):
                local_vars[var_name] = params[i]
                
            try:
                result = eval(expr_processed, {"__builtins__": {}}, {**eval_namespace, **local_vars})
                return result
            except Exception as e:
                # Return large penalty on failure
                return np.full_like(x_val, 1e10)

        try:
            popt, _ = curve_fit(dynamic_fit_func, x_np, y_np, p0=p0, maxfev=10000)
            y_fit = dynamic_fit_func(x_np, *popt)
            params = popt
        except Exception as e:
            logger.error(f"Custom curve fitting failed for expression '{expression}': {e}")
            params = np.zeros(num_params)
            y_fit = np.zeros_like(x_np)

        if pin_name == "Parameters":
            return params
        elif pin_name == "FitY":
            return format_output(y_fit)

        return None
