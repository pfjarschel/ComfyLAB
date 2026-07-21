# Copyright (C) 2026 Paulo Felipe Jarschel

from typing import Any
import numpy as np

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, DataIn, DataOut, ExecutionContext

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
