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
import scipy.ndimage as ndimage

logger = logging.getLogger("comfylab.nodes.plots")

from comfylab.engine.registry import register_node
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext


@register_node("outputs/plots/xy_plot")
class XYPlotNode(BaseNode):
    """Receives X and Y array data and streams them to the UI for XY graphing."""
    icon = "📊"
    display_name = "XY Plot"
    description = "Receives X and Y data lists and streams them to the UI for XY plotting."
    default_width = 300
    default_height = 300
    ui_behavior = {"custom_widget": "xy_plot"}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("X", type_hint=list),
        DataIn("Y", type_hint=list),
        DataIn("XLabel", type_hint=str, default="X", optional=True),
        DataIn("YLabel", type_hint=str, default="Y", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        x = await context.pull(self.id, "X")
        y = await context.pull(self.id, "Y")
        x_label = await context.pull(self.id, "XLabel")
        y_label = await context.pull(self.id, "YLabel")

        # Send telemetry payload
        payload = {
            "x": x if isinstance(x, list) else [],
            "y": y if isinstance(y, list) else [],
            "x_label": str(x_label) if x_label else "X",
            "y_label": str(y_label) if y_label else "Y"
        }
        await context.send_telemetry(self.id, payload)
        return "Out"


@register_node("outputs/plots/plot")
class PlotNode(BaseNode):
    """Receives data values and streams them to the UI for live graphing."""
    icon = "📉"
    display_name = "Time Plot"
    description = "Receives data values and streams them to the UI for live graphing."
    default_width = 210
    default_height = 220
    ui_behavior = {"accumulate_history": True, "custom_widget": "time_plot"}
    
    inputs_def = [
        ExecIn("Plot"),
        DataIn("InputData")
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        val = await context.pull(self.id, "InputData")
        # Send numerical or array telemetry package
        await context.send_telemetry(self.id, {"value": val})
        return "Out"


@register_node("outputs/plots/heatmap_plot")
class HeatmapPlotNode(BaseNode):
    """Receives a 2D array and streams it to the UI for heatmap or contour visualization."""
    icon = "🗺️"
    display_name = "Heatmap Plot"
    description = "Plots a 2D array of values with optional extents and color mapping."
    default_width = 320
    default_height = 340
    ui_behavior = {"custom_widget": "heatmap_plot", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("Z", type_hint=list),
        DataIn("X", type_hint=list, optional=True),
        DataIn("Y", type_hint=list, optional=True),
        DataIn("XLabel", type_hint=str, default="X", optional=True),
        DataIn("YLabel", type_hint=str, default="Y", optional=True),
        DataIn("PlotType", type_hint=str, default="Heatmap", widget="dropdown",
               options=["Heatmap", "Contour"]),
        DataIn("Colormap", type_hint=str, default="Viridis", widget="dropdown", 
               options=["Plotly3", "Viridis", "Cividis", "Hot", "Inferno", "Turbo", "Agsunset", "Picnic", "Phase"]),
        DataIn("Interpolation", type_hint=str, default="None", widget="dropdown",
               options=["None", "Fast (linear)", "Good (bilinear)", "Best (spline36)"])
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

        z_out = z if isinstance(z, list) else []
        x_out = x if isinstance(x, list) else None
        y_out = y if isinstance(y, list) else None

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

        payload = {
            "z": z_out,
            "x": x_out,
            "y": y_out,
            "x_label": str(x_label) if x_label else "X",
            "y_label": str(y_label) if y_label else "Y",
            "colormap": str(colormap) if colormap else "Viridis",
            "interpolation": "False", # Tell frontend not to smooth it since we pre-smoothed it
            "plot_type": str(plot_type) if plot_type else "Heatmap"
        }
        await context.send_telemetry(self.id, payload)
        return "Out"
