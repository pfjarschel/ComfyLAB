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

logger = logging.getLogger("comfylab.nodes.plots")

from comfylab.engine.registry import register_node
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext


@register_node("outputs/plots/xy_plot")
class XYPlotNode(BaseNode):
    """Receives X and Y array data and streams them to the UI for XY graphing."""
    icon = "📊"
    display_name = "XY Plot"
    description = "Receives X and Y data lists and streams them to the UI for XY plotting."
    default_width = 290
    default_height = 220

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

    inputs_def = [
        ExecIn("Plot"),
        DataIn("Z", type_hint=list),
        DataIn("X", type_hint=list, optional=True),
        DataIn("Y", type_hint=list, optional=True),
        DataIn("XLabel", type_hint=str, default="X", optional=True),
        DataIn("YLabel", type_hint=str, default="Y", optional=True),
        DataIn("Colormap", type_hint=str, default="Viridis", widget="dropdown", 
               options=["Viridis", "Plasma", "Hot", "Cividis", "Gray", "Jet", "Rainbow", "Inferno", "Bone", "Wave"])
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        z = await context.pull(self.id, "Z")
        x = await context.pull(self.id, "X")
        y = await context.pull(self.id, "Y")
        x_label = await context.pull(self.id, "XLabel")
        y_label = await context.pull(self.id, "YLabel")
        colormap = await context.pull(self.id, "Colormap")

        payload = {
            "z": z if isinstance(z, list) else [],
            "x": x if isinstance(x, list) else None,
            "y": y if isinstance(y, list) else None,
            "x_label": str(x_label) if x_label else "X",
            "y_label": str(y_label) if y_label else "Y",
            "colormap": str(colormap) if colormap else "Viridis"
        }
        await context.send_telemetry(self.id, payload)
        return "Out"
