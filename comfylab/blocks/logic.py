# Copyright (C) 2026 Paulo Felipe Jarschel

from typing import Any, Dict, Optional
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


@register_block("logic/compare")
class CompareBlock(BaseBlock):
    """Pulls two values and compares them based on the operator property."""
    icon = "⚖️"
    display_name = "Compare"
    description = "Pulls two values and compares them based on an operator."
    
    inputs_def = [
        DataIn("A", type_hint=float, default=0.0, widget="number"),
        DataIn("B", type_hint=float, default=0.0, widget="number"),
        DataIn("Operator", type_hint=str, default="==", widget="dropdown", options=["==", "!=", ">", "<", ">=", "<="])
    ]

    outputs_def = [DataOut("Result", type_hint=bool)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            op = await context.pull(self.id, "Operator")

            try:
                # Attempt numerical conversion
                v1, v2 = float(a), float(b)
            except (ValueError, TypeError):
                # Fallback to string
                v1, v2 = str(a), str(b)

            if op == "==": return v1 == v2
            elif op == "!=": return v1 != v2
            elif op == ">": return v1 > v2
            elif op == "<": return v1 < v2
            elif op == ">=": return v1 >= v2
            elif op == "<=": return v1 <= v2
            return False
        return None


@register_block("logic/has_changed")
class HasChangedBlock(BaseBlock):
    """Stateful block that triggers when a value changes since the last execution."""
    icon = "🔄"
    display_name = "Has Changed"
    description = "Compares an input value to its previous execution value, and outputs whether it has changed."

    inputs_def = [
        ExecIn("In"),
        DataIn("Value", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Changed", type_hint=bool)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_value = None
        self._has_run = False
        self._changed = False

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        val = await context.pull(self.id, "Value")
        
        # If first run, check if last_value is different
        if not self._has_run:
            self._changed = True
            self._has_run = True
        else:
            # NumPy array cycles / comparison
            if isinstance(val, (list, np.ndarray)) or isinstance(self._last_value, (list, np.ndarray)):
                self._changed = not np.array_equal(val, self._last_value)
            else:
                self._changed = (val != self._last_value)

        self._last_value = val
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Changed":
            return self._changed
        return None

    async def clear_data(self) -> None:
        self._changed = False
