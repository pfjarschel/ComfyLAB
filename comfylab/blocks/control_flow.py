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

import asyncio
from typing import Any, Optional, Dict
from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext


@register_block("control_flow/basic/if_else")
class IfElseBlock(BaseBlock):
    """Branches execution path based on a pulled boolean condition."""
    icon = "🔀"
    display_name = "If/Else"
    description = "Branches execution path based on a pulled boolean condition."
    
    inputs_def = [
        ExecIn("In"),
        DataIn("Condition", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [
        ExecOut("True"),
        ExecOut("False")
    ]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        cond = await context.pull(self.id, "Condition")
        return "True" if bool(cond) else "False"


@register_block("control_flow/loops/for_loop")
class ForLoopBlock(BaseBlock):
    """Iterates a specified number of times, triggering a loop body branch."""
    icon = "🔁"
    display_name = "For Loop"
    description = "Iterates a specified number of times, triggering a loop body branch."
    
    inputs_def = [
        ExecIn("Start"),
        DataIn("Count", type_hint=int, default=10, widget="number", min_val=1)
    ]
    outputs_def = [
        ExecOut("LoopBody"),
        ExecOut("Done"),
        DataOut("Index", type_hint=int)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._index = 0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        count = await context.pull(self.id, "Count")
        for i in range(int(count)):
            if context.engine.state == "ABORTED":
                break
            await asyncio.sleep(0) # Yield to event loop to prevent CPU blocking (no artificial delay)
            self._index = i
            # Trigger execution of the LoopBody sub-graph
            await context.engine.trigger_exec(self.id, "LoopBody", context)
        return "Done"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Index":
            return self._index
        return None

    async def clear_data(self) -> None:
        self._index = 0


@register_block("control_flow/loops/while_loop")
class WhileLoopBlock(BaseBlock):
    """Iterates while a pulled condition remains True."""
    icon = "🔁"
    display_name = "While Loop"
    description = "Iterates while a pulled condition remains True."
    
    inputs_def = [
        ExecIn("Start"),
        DataIn("Condition", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [
        ExecOut("LoopBody"),
        ExecOut("Done")
    ]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        while True:
            if context.engine.state == "ABORTED":
                break
            await asyncio.sleep(0) # Yield to event loop to prevent CPU blocking (no artificial delay)
            context.clear_cache()
            cond = await context.pull(self.id, "Condition")
            if not bool(cond):
                break
            await context.engine.trigger_exec(self.id, "LoopBody", context)
        return "Done"
