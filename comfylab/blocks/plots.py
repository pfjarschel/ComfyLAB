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
from typing import Optional
import time
import numpy as np
import scipy.ndimage as ndimage

logger = logging.getLogger("comfylab.blocks.plots")

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, ExecutionContext


@register_block("outputs/plots/xy_plot")
class XYPlotBlock(BaseBlock):
    """Receives X and Y array data and streams them to the UI for XY graphing."""
    icon = "📊"
    display_name = "XY Plot"
    description = "Receives X and Y data lists and streams them to the UI for XY plotting."
    default_width = 300
    default_height = 300
    ui_behavior = {"custom_widget": "xy_plot", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("X", type_hint=np.ndarray),
        DataIn("Y", type_hint=np.ndarray),
        DataIn("XLabel", type_hint=str, default="X", optional=True),
        DataIn("YLabel", type_hint=str, default="Y", optional=True),
        DataIn("Labels", type_hint=list, optional=True),
        DataIn("XMin", type_hint=float, optional=True),
        DataIn("XMax", type_hint=float, optional=True),
        DataIn("YMin", type_hint=float, optional=True),
        DataIn("YMax", type_hint=float, optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        x = await context.pull(self.id, "X")
        y = await context.pull(self.id, "Y")
        x_label = await context.pull(self.id, "XLabel")
        y_label = await context.pull(self.id, "YLabel")

        # Convert to list for JSON serialization
        x_list = x.tolist() if isinstance(x, np.ndarray) else (x if isinstance(x, list) else [])
        y_list = y.tolist() if isinstance(y, np.ndarray) else (y if isinstance(y, list) else [])
        
        labels = await context.pull(self.id, "Labels")
        labels_list = labels.tolist() if isinstance(labels, np.ndarray) else (labels if isinstance(labels, list) else None)

        x_min = await context.pull(self.id, "XMin")
        x_max = await context.pull(self.id, "XMax")
        y_min = await context.pull(self.id, "YMin")
        y_max = await context.pull(self.id, "YMax")

        # Send telemetry payload
        payload = {
            "x": x_list,
            "y": y_list,
            "x_label": str(x_label) if x_label else "X",
            "y_label": str(y_label) if y_label else "Y",
            "x_min": float(x_min) if x_min is not None else None,
            "x_max": float(x_max) if x_max is not None else None,
            "y_min": float(y_min) if y_min is not None else None,
            "y_max": float(y_max) if y_max is not None else None,
            "labels": labels_list
        }
        await context.send_telemetry(self.id, payload)
        return "Out"


@register_block("outputs/plots/plot")
class PlotBlock(BaseBlock):
    """Receives data values and streams them to the UI for live graphing."""
    icon = "📉"
    display_name = "Time Plot"
    description = "Receives data values and streams them to the UI for live graphing."
    default_width = 210
    default_height = 220
    ui_behavior = {"accumulate_history": True, "custom_widget": "time_plot", "render_standard_inputs": True}
    
    inputs_def = [
        ExecIn("Plot"),
        DataIn("InputData"),
        DataIn("MaxHistory", type_hint=int, default=0, widget="number"),
        DataIn("Labels", type_hint=list, optional=True),
        DataIn("YLabel", type_hint=str, default="Value", optional=True),
        DataIn("UseTime", type_hint=bool, default=False, widget="checkbox"),
        DataIn("XMin", type_hint=float, optional=True),
        DataIn("XMax", type_hint=float, optional=True),
        DataIn("YMin", type_hint=float, optional=True),
        DataIn("YMax", type_hint=float, optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        val = await context.pull(self.id, "InputData")
        max_history = await context.pull(self.id, "MaxHistory")
        
        try:
            max_history = int(max_history) if max_history is not None else 0
        except Exception:
            max_history = 0

        x_min = await context.pull(self.id, "XMin")
        x_max = await context.pull(self.id, "XMax")
        y_min = await context.pull(self.id, "YMin")
        y_max = await context.pull(self.id, "YMax")

        # Convert np.ndarray to list for JSON telemetry serialization
        val_serialized = val.tolist() if isinstance(val, np.ndarray) else val
        
        labels = await context.pull(self.id, "Labels")
        labels_list = labels.tolist() if isinstance(labels, np.ndarray) else (labels if isinstance(labels, list) else None)
        
        y_label = await context.pull(self.id, "YLabel")
        use_time = await context.pull(self.id, "UseTime")
        timestamp = time.time() if use_time else None

        # Send numerical or array telemetry package
        await context.send_telemetry(self.id, {
            "value": val_serialized,
            "max_history": max_history,
            "x_min": float(x_min) if x_min is not None else None,
            "x_max": float(x_max) if x_max is not None else None,
            "y_min": float(y_min) if y_min is not None else None,
            "y_max": float(y_max) if y_max is not None else None,
            "labels": labels_list,
            "y_label": str(y_label) if y_label else "Value",
            "timestamp": timestamp
        })
        return "Out"


@register_block("outputs/plots/heatmap_plot")
class HeatmapPlotBlock(BaseBlock):
    """Receives a 2D array and streams it to the UI for heatmap or contour visualization."""
    icon = "🗺️"
    display_name = "Heatmap Plot"
    description = "Plots a 2D array of values with optional extents and color mapping."
    default_width = 320
    default_height = 340
    ui_behavior = {"custom_widget": "heatmap_plot", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("Z", type_hint=np.ndarray),
        DataIn("X", type_hint=np.ndarray, optional=True),
        DataIn("Y", type_hint=np.ndarray, optional=True),
        DataIn("Colormap", type_hint=str, default="Viridis", widget="dropdown", 
               options=["Plotly3", "Viridis", "Cividis", "Hot", "Inferno", "Turbo", "Agsunset", "Picnic", "Phase", "Greys", "Bluered"]),
        DataIn("XLabel", type_hint=str, default="X", optional=True),
        DataIn("YLabel", type_hint=str, default="Y", optional=True),
        DataIn("ZLabel", type_hint=str, default="Z", optional=True),
        DataIn("PlotType", type_hint=str, default="Heatmap", widget="dropdown",
               options=["Heatmap", "Contour"], optional=True),
        DataIn("Interpolation", type_hint=str, default="None", widget="dropdown",
               options=["None", "Fast (linear)", "Good (bilinear)", "Best (spline36)"], optional=True),
        DataIn("XMin", type_hint=float, optional=True),
        DataIn("XMax", type_hint=float, optional=True),
        DataIn("YMin", type_hint=float, optional=True),
        DataIn("YMax", type_hint=float, optional=True),
        DataIn("ZMin", type_hint=float, optional=True),
        DataIn("ZMax", type_hint=float, optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        z = await context.pull(self.id, "Z")
        x = await context.pull(self.id, "X")
        y = await context.pull(self.id, "Y")
        x_label = await context.pull(self.id, "XLabel")
        y_label = await context.pull(self.id, "YLabel")
        colormap = await context.pull(self.id, "Colormap")
        interpolation = await context.pull(self.id, "Interpolation")
        plot_type = await context.pull(self.id, "PlotType")

        z_out = z.tolist() if isinstance(z, np.ndarray) else (z if isinstance(z, list) else [])
        x_out = x.tolist() if isinstance(x, np.ndarray) else (x if isinstance(x, list) else None)
        y_out = y.tolist() if isinstance(y, np.ndarray) else (y if isinstance(y, list) else None)

        interp_str = str(interpolation) if interpolation else "None"

        if interp_str != "None" and z_out:
            try:
                z_arr = np.array(z_out)
                if z_arr.ndim == 2:
                    scale = 4
                    order = 1
                    if "Good" in interp_str:
                        scale = 6
                        order = 3
                    elif "Best" in interp_str:
                        scale = 8
                        order = 5

                    z_zoomed = ndimage.zoom(z_arr, scale, order=order)
                    z_out = z_zoomed.tolist()

                    if x_out and len(x_out) == z_arr.shape[1]:
                        x_arr = np.array(x_out)
                        x_zoomed = ndimage.zoom(x_arr, scale, order=1)
                        x_out = x_zoomed.tolist()
                    
                    if y_out and len(y_out) == z_arr.shape[0]:
                        y_arr = np.array(y_out)
                        y_zoomed = ndimage.zoom(y_arr, scale, order=1)
                        y_out = y_zoomed.tolist()
            except Exception as e:
                logger.error(f"Error interpolating Heatmap Z array: {e}")

        x_min = await context.pull(self.id, "XMin")
        x_max = await context.pull(self.id, "XMax")
        y_min = await context.pull(self.id, "YMin")
        y_max = await context.pull(self.id, "YMax")
        z_min = await context.pull(self.id, "ZMin")
        z_max = await context.pull(self.id, "ZMax")
        z_label = await context.pull(self.id, "ZLabel")

        payload = {
            "z": z_out,
            "x": x_out,
            "y": y_out,
            "x_label": str(x_label) if x_label else "X",
            "y_label": str(y_label) if y_label else "Y",
            "colormap": str(colormap) if colormap else "Viridis",
            "interpolation": "False", # Tell frontend not to smooth it since we pre-smoothed it
            "plot_type": str(plot_type) if plot_type else "Heatmap",
            "x_min": float(x_min) if x_min is not None else None,
            "x_max": float(x_max) if x_max is not None else None,
            "y_min": float(y_min) if y_min is not None else None,
            "y_max": float(y_max) if y_max is not None else None,
            "z_min": float(z_min) if z_min is not None else None,
            "z_max": float(z_max) if z_max is not None else None,
            "z_label": str(z_label) if z_label else "Z"
        }
        await context.send_telemetry(self.id, payload)
        return "Out"
