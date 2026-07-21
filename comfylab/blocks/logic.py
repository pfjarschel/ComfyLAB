# Copyright (C) 2026 Paulo Felipe Jarschel

from typing import Any
import numpy as np

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, DataIn, DataOut, ExecIn, ExecOut, ExecutionContext

def format_logic_output(res: Any) -> Any:
    if isinstance(res, np.ndarray):
        if res.ndim == 0:
            return bool(res)
        return res
    return bool(res)

@register_block("logic/and")
class LogicAndBlock(BaseBlock):
    """Boolean AND operation."""
    icon = "∧"
    display_name = "AND Gate"
    description = "Performs a logical AND operation between A and B."
    
    inputs_def = [
        DataIn("A", type_hint=Any, default=False, widget="checkbox"),
        DataIn("B", type_hint=Any, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            res = np.logical_and(np.asarray(a, dtype=bool), np.asarray(b, dtype=bool))
            return format_logic_output(res)
        return None

@register_block("logic/or")
class LogicOrBlock(BaseBlock):
    """Boolean OR operation."""
    icon = "∨"
    display_name = "OR Gate"
    description = "Performs a logical OR operation between A and B."
    
    inputs_def = [
        DataIn("A", type_hint=Any, default=False, widget="checkbox"),
        DataIn("B", type_hint=Any, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            res = np.logical_or(np.asarray(a, dtype=bool), np.asarray(b, dtype=bool))
            return format_logic_output(res)
        return None

@register_block("logic/not")
class LogicNotBlock(BaseBlock):
    """Boolean NOT operation."""
    icon = "¬"
    display_name = "NOT Gate"
    description = "Performs a logical NOT operation on A."
    
    inputs_def = [
        DataIn("A", type_hint=Any, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            res = np.logical_not(np.asarray(a, dtype=bool))
            return format_logic_output(res)
        return None

@register_block("logic/xor")
class LogicXorBlock(BaseBlock):
    """Boolean XOR operation."""
    icon = "⊻"
    display_name = "XOR Gate"
    description = "Performs a logical XOR (exclusive OR) operation between A and B."
    
    inputs_def = [
        DataIn("A", type_hint=Any, default=False, widget="checkbox"),
        DataIn("B", type_hint=Any, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            res = np.logical_xor(np.asarray(a, dtype=bool), np.asarray(b, dtype=bool))
            return format_logic_output(res)
        return None

@register_block("logic/nand")
class LogicNandBlock(BaseBlock):
    """Boolean NAND operation."""
    icon = "⊼"
    display_name = "NAND Gate"
    description = "Performs a logical NAND (NOT AND) operation between A and B."
    
    inputs_def = [
        DataIn("A", type_hint=Any, default=False, widget="checkbox"),
        DataIn("B", type_hint=Any, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            res = np.logical_not(np.logical_and(np.asarray(a, dtype=bool), np.asarray(b, dtype=bool)))
            return format_logic_output(res)
        return None

@register_block("logic/nor")
class LogicNorBlock(BaseBlock):
    """Boolean NOR operation."""
    icon = "⊽"
    display_name = "NOR Gate"
    description = "Performs a logical NOR (NOT OR) operation between A and B."
    
    inputs_def = [
        DataIn("A", type_hint=Any, default=False, widget="checkbox"),
        DataIn("B", type_hint=Any, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            res = np.logical_not(np.logical_or(np.asarray(a, dtype=bool), np.asarray(b, dtype=bool)))
            return format_logic_output(res)
        return None

@register_block("logic/xnor")
class LogicXnorBlock(BaseBlock):
    """Boolean XNOR operation."""
    icon = "≡"
    display_name = "XNOR Gate"
    description = "Performs a logical XNOR (exclusive NOR) operation between A and B."
    
    inputs_def = [
        DataIn("A", type_hint=Any, default=False, widget="checkbox"),
        DataIn("B", type_hint=Any, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            res = np.logical_not(np.logical_xor(np.asarray(a, dtype=bool), np.asarray(b, dtype=bool)))
            return format_logic_output(res)
        return None

@register_block("logic/flip_flop")
class FlipFlopBlock(BaseBlock):
    """Toggles state on each execution."""
    icon = "↕"
    display_name = "Flip-Flop"
    description = "Alternates a boolean state (True/False) on every execution trigger."
    
    inputs_def = [
        ExecIn("Toggle"),
        DataIn("Initial", type_hint=bool, default=False, widget="checkbox", optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("State", type_hint=bool)
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = None

    async def execute(self, context: ExecutionContext, pin_name: str):
        if self._state is None:
            initial = await context.pull(self.id, "Initial")
            self._state = bool(initial) if initial is not None else False
            
        self._state = not self._state
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "State":
            if self._state is None:
                initial = await context.pull(self.id, "Initial")
                self._state = bool(initial) if initial is not None else False
            return self._state
        return None
