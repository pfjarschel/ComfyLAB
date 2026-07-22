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

from typing import Any, Optional

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext

@register_block("cluster/boundary/input")
class ClusterInputBlock(BaseBlock):
    """Anchor block representing a cluster input pin inside its sub-graph."""
    icon = "📥"
    display_name = "Cluster Input"
    description = "Exposes a cluster input boundary pin. Connect this to blocks inside the cluster."

    inputs_def = [
        DataIn("Name", type_hint=str, default="InputPin", widget="text"),
        DataIn("Type", type_hint=str, default="data", widget="dropdown", options=["exec", "data"]),
        DataIn("DataType", type_hint=str, default="any", widget="dropdown", options=["number", "boolean", "text", "list", "any"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Value", type_hint=Any)
    ]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            if hasattr(context, "parent_context") and hasattr(context, "_cluster_block_id"):
                pin_name_config = await context.pull(self.id, "Name")
                return await context.parent_context.pull(context._cluster_block_id, pin_name_config)
            return None
        return None


@register_block("cluster/boundary/output")
class ClusterOutputBlock(BaseBlock):
    """Anchor block representing a cluster output pin inside its sub-graph."""
    icon = "📤"
    display_name = "Cluster Output"
    description = "Exposes a cluster output boundary pin. Connect blocks inside the cluster to this."

    inputs_def = [
        DataIn("Name", type_hint=str, default="OutputPin", widget="text"),
        DataIn("Type", type_hint=str, default="data", widget="dropdown", options=["exec", "data"]),
        ExecIn("In"),
        DataIn("Value", type_hint=Any, optional=False)
    ]
    outputs_def = []

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "In":
            if hasattr(context, "parent_context"):
                pin_name_config = await context.pull(self.id, "Name")
                # Record that this cluster output was triggered in the cluster execution context
                context._triggered_exec_out = pin_name_config
        return None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return await context.pull(self.id, "Value")
        return None
