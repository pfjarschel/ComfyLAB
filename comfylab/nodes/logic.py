# Copyright (C) 2026 Paulo Felipe Jarschel

from typing import Any
import numpy as np

from comfylab.engine.registry import register_node
from comfylab.nodes.base import BaseNode, DataIn, DataOut, ExecutionContext

def format_logic_output(res: Any) -> Any:
    if isinstance(res, np.ndarray):
        if res.ndim == 0:
            return bool(res)
        return res
    return bool(res)

@register_node("logic/and")
class LogicAndNode(BaseNode):
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

@register_node("logic/or")
class LogicOrNode(BaseNode):
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

@register_node("logic/not")
class LogicNotNode(BaseNode):
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

@register_node("logic/xor")
class LogicXorNode(BaseNode):
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

@register_node("logic/nand")
class LogicNandNode(BaseNode):
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

@register_node("logic/nor")
class LogicNorNode(BaseNode):
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

@register_node("logic/xnor")
class LogicXnorNode(BaseNode):
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
