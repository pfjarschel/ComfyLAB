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
import math
import random
import logging
import time
from typing import Any, Optional, Dict, List
import numpy as np

logger = logging.getLogger("comfylab.nodes.standard")

from comfylab.engine.registry import register_node
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext

@register_node("constants/number")
class NumberNode(BaseNode):
    """Outputs a static numerical value defined in properties."""
    icon = "#️⃣"
    display_name = "Number"
    description = "Outputs a constant numerical value."
    default_width = 160
    ui_behavior = {"custom_widget": "constant_number"}
    
    outputs_def = [DataOut("Value", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return float(self.properties.get("value", 0.0))
        return None


@register_node("math/basic/add")
class AddNode(BaseNode):
    """Pulls two numbers, A and B, and outputs their sum."""
    icon = "➕"
    display_name = "Add"
    description = "Pulls two numbers, A and B, and outputs their sum."
    
    inputs_def = [
        DataIn("A", type_hint=float, default=0.0, widget="number"),
        DataIn("B", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            return float(a) + float(b)
        return None


@register_node("logic/compare")
class CompareNode(BaseNode):
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


@register_node("outputs/basic/print")
class PrintNode(BaseNode):
    """Prints a pulled value to standard output and continues execution."""
    icon = " >_ "
    display_name = "Print Node"
    description = "Prints a pulled value to standard output and continues execution."
    
    inputs_def = [
        ExecIn("In"),
        DataIn("Value", type_hint=Any, default="", widget="text")
    ]
    outputs_def = [ExecOut("Out")]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self.last_printed: Any = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        val = await context.pull(self.id, "Value")
        self.last_printed = val
        logger.info(f"[ComfyLAB Print Node '{self.id}'] >>> {val}")
        print(f"[ComfyLAB Print Node '{self.id}'] >>> {val}")
        return "Out"

    async def clear_data(self) -> None:
        self.last_printed = None



@register_node("control_flow/basic/if_else")
class IfElseNode(BaseNode):
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


@register_node("control_flow/loops/for_loop")
class ForLoopNode(BaseNode):
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

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._index = 0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        count = await context.pull(self.id, "Count")
        for i in range(int(count)):
            if context.engine.state == "ABORTED":
                break
            await asyncio.sleep(0.01) # Yield to event loop to prevent CPU blocking
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



@register_node("control_flow/loops/while_loop")
class WhileLoopNode(BaseNode):
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
            await asyncio.sleep(0.01) # Yield to event loop to prevent CPU blocking
            context.clear_cache()
            cond = await context.pull(self.id, "Condition")
            if not bool(cond):
                break
            await context.engine.trigger_exec(self.id, "LoopBody", context)
        return "Done"


@register_node("constants/boolean")
class BooleanNode(BaseNode):
    """Outputs a static boolean value (e.g. from an on/off toggle button)."""
    icon = "🔘"
    display_name = "Boolean"
    description = "Outputs a constant boolean value (True/False)."
    default_width = 160
    ui_behavior = {"custom_widget": "constant_boolean"}
    
    outputs_def = [DataOut("Value", type_hint=bool)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return bool(self.properties.get("value", False))
        return None


@register_node("outputs/basic/display")
class DisplayNode(BaseNode):
    """Displays a pulled value on the node itself by broadcasting telemetry."""
    icon = "🖥️"
    display_name = "Display Value"
    description = "Displays the incoming value in the UI."
    ui_behavior = {"custom_widget": "display_area"}
    
    inputs_def = [
        ExecIn("In"),
        DataIn("Value", type_hint=Any, default="", widget="any")
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        val = await context.pull(self.id, "Value")
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            display_val = val
        else:
            display_val = str(val)
        await context.send_telemetry(self.id, {"value": display_val})
        return "Out"


@register_node("constants/string")
class StringNode(BaseNode):
    """Outputs a static string value defined in properties."""
    icon = "🔤"
    display_name = "String"
    description = "Outputs a constant string."
    default_width = 160
    ui_behavior = {"custom_widget": "constant_string"}
    
    outputs_def = [DataOut("Value", type_hint=str)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return str(self.properties.get("value", ""))
        return None



@register_node("math/basic/subtract")
class SubtractNode(BaseNode):
    """Pulls two numbers, A and B, and outputs A - B."""
    icon = "➖"
    display_name = "Subtract"
    description = "Pulls two numbers, A and B, and outputs A - B."
    
    inputs_def = [
        DataIn("A", type_hint=float, default=0.0, widget="number"),
        DataIn("B", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            return float(a) - float(b)
        return None


@register_node("math/basic/multiply")
class MultiplyNode(BaseNode):
    """Pulls two numbers, A and B, and outputs their product."""
    icon = "✖️"
    display_name = "Multiply"
    description = "Pulls two numbers, A and B, and outputs their product."
    
    inputs_def = [
        DataIn("A", type_hint=float, default=1.0, widget="number"),
        DataIn("B", type_hint=float, default=1.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            return float(a) * float(b)
        return None


@register_node("math/basic/divide")
class DivideNode(BaseNode):
    """Pulls two numbers, A and B, and outputs A / B."""
    icon = "➗"
    display_name = "Divide"
    description = "Pulls two numbers, A and B, and outputs A / B."
    
    inputs_def = [
        DataIn("A", type_hint=float, default=1.0, widget="number"),
        DataIn("B", type_hint=float, default=1.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "A")
            b = await context.pull(self.id, "B")
            denom = float(b)
            if denom == 0.0:
                raise ZeroDivisionError("Division by zero in math/basic/divide node.")
            return float(a) / denom
        return None


@register_node("math/basic/power")
class PowerNode(BaseNode):
    """Raises base A to exponent B (A^B)."""
    icon = "🔋"
    display_name = "Power"
    description = "Raises base A to exponent B (A^B)."
    
    inputs_def = [
        DataIn("Base", type_hint=float, default=2.0, widget="number"),
        DataIn("Exponent", type_hint=float, default=3.0, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            base = await context.pull(self.id, "Base")
            exp = await context.pull(self.id, "Exponent")
            return float(base) ** float(exp)
        return None


@register_node("math/basic/trig")
class TrigNode(BaseNode):
    """Computes trig functions (sin, cos, tan, and their inverses/hyperbolics)."""
    icon = "📐"
    display_name = "Trigonometry"
    description = "Computes trig and hyperbolic functions in radians or degrees. Supports arrays."
    
    inputs_def = [
        DataIn("Value", type_hint=Any, default=0.0),
        DataIn("Function", type_hint=str, default="sin", widget="dropdown", options=[
            "sin", "cos", "tan", "asin", "acos", "atan",
            "sinh", "cosh", "tanh", "asinh", "acosh", "atanh"
        ]),
        DataIn("UseDegrees", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            val = await context.pull(self.id, "Value")
            if val is None:
                val = 0.0
            func = await context.pull(self.id, "Function")
            deg = bool(await context.pull(self.id, "UseDegrees"))
            
            # Convert to numpy array to transparently handle scalars and arrays
            val_np = np.asarray(val, dtype=float)
            
            angle = val_np
            is_direct = func in ["sin", "cos", "tan"]
            if deg and is_direct:
                angle = np.radians(angle)
                
            res = None
            if func == "sin": res = np.sin(angle)
            elif func == "cos": res = np.cos(angle)
            elif func == "tan": res = np.tan(angle)
            elif func == "asin": res = np.arcsin(angle)
            elif func == "acos": res = np.arccos(angle)
            elif func == "atan": res = np.arctan(angle)
            elif func == "sinh": res = np.sinh(angle)
            elif func == "cosh": res = np.cosh(angle)
            elif func == "tanh": res = np.tanh(angle)
            elif func == "asinh": res = np.arcsinh(angle)
            elif func == "acosh": res = np.arccosh(angle)
            elif func == "atanh": res = np.arctanh(angle)
            else: res = val_np * 0.0
            
            is_inverse = func in ["asin", "acos", "atan"]
            if deg and is_inverse:
                res = np.degrees(res)
                
            res = np.nan_to_num(res, nan=0.0, posinf=1e99, neginf=-1e99)
            
            if res.ndim == 0:
                return float(res)
            return res
        return None


@register_node("math/random/random")
class RandomNode(BaseNode):
    """Outputs a random float or int in the range [Min, Max]."""
    icon = "🎲"
    display_name = "Random Number"
    description = "Outputs a random number in the range [Min, Max]."
    
    inputs_def = [
        DataIn("Min", type_hint=float, default=0.0, widget="number"),
        DataIn("Max", type_hint=float, default=1.0, widget="number"),
        DataIn("IntegerMode", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Value", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            min_val = float(await context.pull(self.id, "Min"))
            max_val = float(await context.pull(self.id, "Max"))
            int_mode = bool(await context.pull(self.id, "IntegerMode"))
            
            if int_mode:
                return float(random.randint(int(min_val), int(max_val)))
            return random.uniform(min_val, max_val)
        return None


@register_node("math/random/random_array")
class RandomArrayNode(BaseNode):
    """Outputs a random numeric array (NDArray) in the range [Min, Max] with a given shape."""
    icon = "🎲"
    display_name = "Random Array"
    description = "Outputs a random NDArray in the range [Min, Max]."
    
    inputs_def = [
        DataIn("Shape", type_hint=Any, default="100", widget="text"),
        DataIn("Min", type_hint=float, default=0.0, widget="number"),
        DataIn("Max", type_hint=float, default=1.0, widget="number"),
        DataIn("IntegerMode", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Array", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Array":
            shape_raw = await context.pull(self.id, "Shape")
            min_val = float(await context.pull(self.id, "Min"))
            max_val = float(await context.pull(self.id, "Max"))
            int_mode = bool(await context.pull(self.id, "IntegerMode"))
            
            shape = []
            if isinstance(shape_raw, str):
                try:
                    shape = [int(x.strip()) for x in shape_raw.split(',') if x.strip()]
                except Exception:
                    shape = [100]
            elif isinstance(shape_raw, (list, tuple, np.ndarray)):
                shape = [int(x) for x in shape_raw]
            elif isinstance(shape_raw, (int, float)):
                shape = [int(shape_raw)]
            
            if not shape:
                shape = [100]
                
            if int_mode:
                return np.random.randint(int(min_val), int(max_val) + 1, size=shape)
            return np.random.uniform(min_val, max_val, size=shape)
        return None


@register_node("Lists/manipulation/accumulate")
class AccumulateListNode(BaseNode):
    """Accumulates input values into a standard list over multiple execution steps."""
    icon = "📥"
    display_name = "Accumulate List"
    description = "Accumulates input values into a list. Has an Append pin to add items and a Reset pin to clear them."
    ui_behavior = {"custom_widget": "display_area"}

    inputs_def = [
        ExecIn("Append"),
        ExecIn("Reset"),
        DataIn("Value", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        ExecOut("Skipped"),
        DataOut("List", type_hint=list)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._list: List[Any] = []

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        output_pin = "Out"
        if trigger_pin == "Reset":
            self._list = []
            output_pin = "Skipped"
        elif trigger_pin == "Append":
            val = await context.pull(self.id, "Value")
            if val is not None:
                self._list.append(val)
        
        display_str = f"[{', '.join(str(x) for x in self._list)}]" if len(self._list) <= 3 else f"List ({len(self._list)} items)"
        await context.send_telemetry(self.id, {"value": display_str})
        return output_pin

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "List":
            return self._list
        return None

    async def clear_data(self) -> None:
        self._list = []


@register_node("Lists/manipulation/create")
class CreateListNode(BaseNode):
    """Creates a list from a comma-separated string."""
    icon = "📥"
    display_name = "Create List"
    description = "Creates a list from a comma-separated string of numbers or texts."
    
    ui_behavior = {"dynamic_inputs": {"prefix": "Row", "type": "str", "widget": "text", "default_count": 1}}
    
    inputs_def = [
        DataIn("ParseNumbers", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("List", type_hint=list)]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        item_count = int(self.properties.get("itemCount", 1))
        for i in range(item_count):
            self.inputs[f"Row {i}"] = DataIn(f"Row {i}", type_hint=str, default="")

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "List":
            parse_num = bool(await context.pull(self.id, "ParseNumbers"))
            item_count = int(self.properties.get("itemCount", 1))
            
            parsed_rows = []
            for i in range(item_count):
                csv_str = await context.pull(self.id, f"Row {i}")
                if not csv_str:
                    continue
                    
                items = [item.strip() for item in csv_str.split(",")]
                if parse_num:
                    parsed = []
                    for item in items:
                        try:
                            val = float(item)
                            if val == int(val):
                                val = int(val)
                            parsed.append(val)
                        except ValueError:
                            parsed.append(item)
                    parsed_rows.append(parsed)
                else:
                    parsed_rows.append(items)
            
            if len(parsed_rows) == 1 and item_count == 1:
                return parsed_rows[0]
            return parsed_rows
        return None


@register_node("Lists/manipulation/pack")
class PackListNode(BaseNode):
    """Packs multiple inputs into a single List."""
    icon = "📦"
    display_name = "Pack List"
    description = "Packs multiple evaluated inputs into a standard python list."

    ui_behavior = {"dynamic_inputs": {"prefix": "Item", "type": "any", "default_count": 2}}
    
    inputs_def = []
    outputs_def = [DataOut("List", type_hint=list)]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        item_count = int(self.properties.get("itemCount", 2))
        for i in range(item_count):
            self.inputs[f"Item {i}"] = DataIn(f"Item {i}", type_hint=Any, default=None)

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "List":
            item_count = int(self.properties.get("itemCount", 2))
            result = []
            for i in range(item_count):
                val = await context.pull(self.id, f"Item {i}")
                result.append(val)
            return result
        return None


@register_node("Lists/operations/get")
class GetListItemNode(BaseNode):
    """Retrieves a list item at a specific index."""
    icon = "🔍"
    display_name = "Get List Item"
    description = "Retrieves a list item at a specific index."
    
    inputs_def = [
        DataIn("List", type_hint=list),
        DataIn("Index", type_hint=int, default=0, widget="number")
    ]
    outputs_def = [DataOut("Item", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Item":
            arr = await context.pull(self.id, "List")
            idx = int(await context.pull(self.id, "Index"))
            
            if not arr or not isinstance(arr, list):
                return None
                
            if 0 <= idx < len(arr):
                return arr[idx]
            elif -len(arr) <= idx < 0:
                return arr[idx]
            return None
        return None


@register_node("Lists/operations/length")
class ListLengthNode(BaseNode):
    """Returns the size of a list."""
    icon = "📏"
    display_name = "List Length"
    description = "Returns the size of the list."
    
    inputs_def = [
        DataIn("List", type_hint=list)
    ]
    outputs_def = [DataOut("Length", type_hint=int)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Length":
            arr = await context.pull(self.id, "List")
            if not arr or not isinstance(arr, list):
                return 0
            return len(arr)
        return None


@register_node("Lists/manipulation/concat")
class ConcatListsNode(BaseNode):
    """Concatenates two lists."""
    icon = "🔗"
    display_name = "Concatenate Lists"
    description = "Concatenates list A and list B."
    
    inputs_def = [
        DataIn("ListA", type_hint=list),
        DataIn("ListB", type_hint=list)
    ]
    outputs_def = [DataOut("Result", type_hint=list)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "ListA")
            b = await context.pull(self.id, "ListB")
            
            arr_a = a if isinstance(a, list) else ([a] if a is not None else [])
            arr_b = b if isinstance(b, list) else ([b] if b is not None else [])
            
            return arr_a + arr_b
        return None


@register_node("Lists/manipulation/transpose")
class TransposeListNode(BaseNode):
    """Transposes a 1D or 2D nested list."""
    icon = "🔄"
    display_name = "Transpose List"
    description = "Transposes a list or 2D nested list (list of lists)."
    
    inputs_def = [
        DataIn("List", type_hint=list)
    ]
    outputs_def = [DataOut("Transposed", type_hint=list)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Transposed":
            arr = await context.pull(self.id, "List")
            if not isinstance(arr, list):
                return arr
            
            if len(arr) > 0 and isinstance(arr[0], list):
                return list(map(list, zip(*arr)))
            else:
                return [[x] for x in arr]
        return None


@register_node("Lists/manipulation/append")
class AppendListNode(BaseNode):
    """Appends a value to a list and outputs the new list."""
    icon = "➕"
    display_name = "Append List"
    description = "Appends a value to a list and returns the new list."

    inputs_def = [
        DataIn("List", type_hint=list),
        DataIn("Value", type_hint=Any)
    ]
    outputs_def = [DataOut("Result", type_hint=list)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            lst = await context.pull(self.id, "List")
            val = await context.pull(self.id, "Value")
            if not isinstance(lst, list):
                lst = [lst] if lst is not None else []
            return lst + [val]
        return None


@register_node("Lists/operations/sort")
class SortListNode(BaseNode):
    """Sorts a list."""
    icon = "🔀"
    display_name = "Sort List"
    description = "Sorts a list in ascending or descending order."

    inputs_def = [
        DataIn("List", type_hint=list),
        DataIn("Reverse", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Sorted", type_hint=list)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Sorted":
            lst = await context.pull(self.id, "List")
            rev = bool(await context.pull(self.id, "Reverse"))
            if not isinstance(lst, list):
                return []
            try:
                return sorted(lst, reverse=rev)
            except Exception:
                return lst
        return None


@register_node("Lists/operations/slice")
class SliceListNode(BaseNode):
    """Returns a range slice of a list."""
    icon = "✂️"
    display_name = "Slice List"
    description = "Slices a list from Start to Stop with a Step."

    inputs_def = [
        DataIn("List", type_hint=list),
        DataIn("Start", type_hint=int, default=0, optional=True, widget="number"),
        DataIn("Stop", type_hint=int, default=None, optional=True, widget="number"),
        DataIn("Step", type_hint=int, default=1, widget="number")
    ]
    outputs_def = [DataOut("Sliced", type_hint=list)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Sliced":
            lst = await context.pull(self.id, "List")
            start = await context.pull(self.id, "Start")
            stop = await context.pull(self.id, "Stop")
            step = await context.pull(self.id, "Step")

            if not isinstance(lst, list):
                return []

            start_val = int(start) if start is not None else 0
            stop_val = int(stop) if stop is not None else len(lst)
            step_val = int(step) if step is not None else 1

            return lst[start_val:stop_val:step_val]
        return None


@register_node("Lists/operations/take")
class TakeListNode(BaseNode):
    """Takes specific elements from a list given indices."""
    icon = "👈"
    display_name = "Take List Items"
    description = "Extracts elements from a list based on an list of indices (useful for reordering)."

    inputs_def = [
        DataIn("List", type_hint=list),
        DataIn("Indices", type_hint=list)
    ]
    outputs_def = [DataOut("Result", type_hint=list)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            lst = await context.pull(self.id, "List")
            indices = await context.pull(self.id, "Indices")

            if not isinstance(lst, list) or not isinstance(indices, list):
                return []

            result = []
            for idx in indices:
                try:
                    idx_val = int(idx)
                    if 0 <= idx_val < len(lst) or -len(lst) <= idx_val < 0:
                        result.append(lst[idx_val])
                except (ValueError, TypeError):
                    pass
            return result
        return None


@register_node("Numeric Arrays/manipulation/create_filled")
class CreateFilledNdarrayNode(BaseNode):
    """Outputs a constant NDArray filled with a specific value, given a shape."""
    icon = "🟩"
    display_name = "Create Filled Array"
    description = "Outputs an NDArray filled with a single value."
    
    inputs_def = [
        DataIn("Shape", type_hint=Any, default="100", widget="text"),
        DataIn("Value", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [DataOut("Array", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Array":
            shape_raw = await context.pull(self.id, "Shape")
            val = float(await context.pull(self.id, "Value"))
            
            shape = []
            if isinstance(shape_raw, str):
                try:
                    shape = [int(x.strip()) for x in shape_raw.split(',') if x.strip()]
                except Exception:
                    shape = [100]
            elif isinstance(shape_raw, (list, tuple, np.ndarray)):
                shape = [int(x) for x in shape_raw]
            elif isinstance(shape_raw, (int, float)):
                shape = [int(shape_raw)]
            
            if not shape:
                shape = [100]
                
            return np.full(shape, val, dtype=float)
        return None


@register_node("Numeric Arrays/manipulation/create")
class CreateNdarrayNode(BaseNode):
    """Creates a NumPy array from a comma-separated string."""
    icon = "📥"
    display_name = "Create NDArray"
    description = "Creates a NumPy numeric array from a comma-separated string of numbers."
    
    ui_behavior = {"dynamic_inputs": {"prefix": "Row", "type": "str", "widget": "text", "default_count": 1}}
    
    inputs_def = []
    outputs_def = [DataOut("Array", type_hint=np.ndarray)]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        item_count = int(self.properties.get("itemCount", 1))
        for i in range(item_count):
            self.inputs[f"Row {i}"] = DataIn(f"Row {i}", type_hint=str, default="")

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Array":
            item_count = int(self.properties.get("itemCount", 1))
            
            parsed_rows = []
            for i in range(item_count):
                csv_str = await context.pull(self.id, f"Row {i}")
                if not csv_str:
                    continue
                    
                items = [item.strip() for item in csv_str.split(",")]
                parsed = []
                for item in items:
                    try:
                        val = float(item)
                        parsed.append(val)
                    except ValueError:
                        parsed.append(np.nan)
                parsed_rows.append(parsed)
                
            if len(parsed_rows) == 1 and item_count == 1:
                return np.array(parsed_rows[0], dtype=float)
            return np.array(parsed_rows, dtype=float)
        return None


@register_node("Numeric Arrays/manipulation/pack")
class PackNdarrayNode(BaseNode):
    """Packs multiple inputs into a NumPy Array."""
    icon = "📦"
    display_name = "Pack NDArray"
    description = "Packs multiple evaluated inputs into a NumPy ndarray. Raises an error if dimensions are inconsistent."

    ui_behavior = {"dynamic_inputs": {"prefix": "Item", "type": "any", "default_count": 2}}
    
    inputs_def = []
    outputs_def = [DataOut("Array", type_hint=np.ndarray)]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        item_count = int(self.properties.get("itemCount", 2))
        for i in range(item_count):
            self.inputs[f"Item {i}"] = DataIn(f"Item {i}", type_hint=Any, default=None)

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Array":
            item_count = int(self.properties.get("itemCount", 2))
            result = []
            for i in range(item_count):
                val = await context.pull(self.id, f"Item {i}")
                result.append(val)
            
            try:
                return np.array(result, dtype=float)
            except Exception as e:
                raise ValueError(f"Inconsistent dimensions or types for Pack NDArray: {e}")
        return None


@register_node("Numeric Arrays/manipulation/accumulate")
class AccumulateNdarrayNode(BaseNode):
    """Accumulates values into a NumPy array over multiple execution steps."""
    icon = "📥"
    display_name = "Accumulate NDArray"
    description = "Accumulates values into a NumPy array. Has Append and Reset pins."
    ui_behavior = {"custom_widget": "display_area"}

    inputs_def = [
        ExecIn("Append"),
        ExecIn("Reset"),
        DataIn("Value", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        ExecOut("Skipped"),
        DataOut("Array", type_hint=np.ndarray)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._list: List[float] = []

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        output_pin = "Out"
        if trigger_pin == "Reset":
            self._list = []
            output_pin = "Skipped"
        elif trigger_pin == "Append":
            val = await context.pull(self.id, "Value")
            if val is not None:
                try:
                    self._list.append(float(val))
                except (ValueError, TypeError):
                    pass
        
        display_str = f"NDArray([{', '.join(str(x) for x in self._list)}])" if len(self._list) <= 3 else f"NDArray ({len(self._list)} items)"
        await context.send_telemetry(self.id, {"value": display_str})
        return output_pin

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Array":
            return np.array(self._list, dtype=float)
        return None

    async def clear_data(self) -> None:
        self._list = []


@register_node("Numeric Arrays/manipulation/concat")
class ConcatNdarraysNode(BaseNode):
    """Concatenates two NumPy arrays."""
    icon = "🔗"
    display_name = "Concatenate NDArrays"
    description = "Concatenates two NumPy arrays."
    
    inputs_def = [
        DataIn("ArrayA", type_hint=np.ndarray),
        DataIn("ArrayB", type_hint=np.ndarray)
    ]
    outputs_def = [DataOut("Result", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "ArrayA")
            b = await context.pull(self.id, "ArrayB")
            
            if a is None:
                return b if isinstance(b, np.ndarray) else np.array([])
            if b is None:
                return a if isinstance(a, np.ndarray) else np.array([])
                
            arr_a = a if isinstance(a, np.ndarray) else np.array(a if isinstance(a, list) else [a])
            arr_b = b if isinstance(b, np.ndarray) else np.array(b if isinstance(b, list) else [b])
            
            try:
                return np.concatenate((arr_a, arr_b))
            except Exception:
                return arr_a
        return None


@register_node("Numeric Arrays/manipulation/transpose")
class TransposeNdarrayNode(BaseNode):
    """Transposes a NumPy array."""
    icon = "🔄"
    display_name = "Transpose NDArray"
    description = "Transposes a 1D or 2D NumPy array."
    
    inputs_def = [
        DataIn("Array", type_hint=np.ndarray)
    ]
    outputs_def = [DataOut("Transposed", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Transposed":
            arr = await context.pull(self.id, "Array")
            if not isinstance(arr, np.ndarray):
                return np.array([])
            return arr.T
        return None


@register_node("Numeric Arrays/manipulation/append")
class AppendNdarrayNode(BaseNode):
    """Appends a value to a NumPy array."""
    icon = "➕"
    display_name = "Append NDArray"
    description = "Appends a value to a NumPy array."

    inputs_def = [
        DataIn("Array", type_hint=np.ndarray),
        DataIn("Value", type_hint=Any)
    ]
    outputs_def = [DataOut("Result", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            arr = await context.pull(self.id, "Array")
            val = await context.pull(self.id, "Value")
            if not isinstance(arr, np.ndarray):
                arr = np.array([])
            try:
                return np.append(arr, val)
            except Exception:
                return arr
        return None


@register_node("Numeric Arrays/operations/get")
class GetNdarrayItemNode(BaseNode):
    """Retrieves a NumPy array item at a specific index."""
    icon = "🔍"
    display_name = "Get NDArray Item"
    description = "Retrieves an item at a specific index from a NumPy array."
    
    inputs_def = [
        DataIn("Array", type_hint=np.ndarray),
        DataIn("Index", type_hint=int, default=0, widget="number")
    ]
    outputs_def = [DataOut("Item", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Item":
            arr = await context.pull(self.id, "Array")
            idx = int(await context.pull(self.id, "Index"))
            
            if not isinstance(arr, np.ndarray):
                return None
                
            try:
                val = arr[idx]
                if hasattr(val, "item"):
                    return val.item()
                return val
            except Exception:
                return None
        return None


@register_node("Numeric Arrays/operations/length")
class NdarrayLengthNode(BaseNode):
    """Returns the size of a NumPy array."""
    icon = "📏"
    display_name = "NDArray Length"
    description = "Returns the size/length of a NumPy array."
    
    inputs_def = [
        DataIn("Array", type_hint=np.ndarray)
    ]
    outputs_def = [DataOut("Length", type_hint=int)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Length":
            arr = await context.pull(self.id, "Array")
            if not isinstance(arr, np.ndarray):
                return 0
            return len(arr)
        return None


@register_node("Numeric Arrays/operations/sort")
class SortNdarrayNode(BaseNode):
    """Sorts a NumPy array."""
    icon = "🔀"
    display_name = "Sort NDArray"
    description = "Sorts a NumPy array in ascending order."

    inputs_def = [
        DataIn("Array", type_hint=np.ndarray)
    ]
    outputs_def = [DataOut("Sorted", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Sorted":
            arr = await context.pull(self.id, "Array")
            if not isinstance(arr, np.ndarray):
                return np.array([])
            return np.sort(arr)
        return None


@register_node("Numeric Arrays/operations/slice")
class SliceNdarrayNode(BaseNode):
    """Returns a slice of a NumPy array."""
    icon = "✂️"
    display_name = "Slice NDArray"
    description = "Slices a NumPy array from Start to Stop with a Step."

    inputs_def = [
        DataIn("Array", type_hint=np.ndarray),
        DataIn("Start", type_hint=int, default=0, optional=True, widget="number"),
        DataIn("Stop", type_hint=int, default=None, optional=True, widget="number"),
        DataIn("Step", type_hint=int, default=1, widget="number")
    ]
    outputs_def = [DataOut("Sliced", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Sliced":
            arr = await context.pull(self.id, "Array")
            start = await context.pull(self.id, "Start")
            stop = await context.pull(self.id, "Stop")
            step = await context.pull(self.id, "Step")

            if not isinstance(arr, np.ndarray):
                return np.array([])

            start_val = int(start) if start is not None else 0
            stop_val = int(stop) if stop is not None else len(arr)
            step_val = int(step) if step is not None else 1

            return arr[start_val:stop_val:step_val]
        return None


@register_node("Numeric Arrays/operations/take")
class TakeNdarrayNode(BaseNode):
    """Selects specific elements from a NumPy array given indices."""
    icon = "👈"
    display_name = "Take NDArray Items"
    description = "Extracts elements from an array based on an array/list of indices (useful for reordering)."

    inputs_def = [
        DataIn("Array", type_hint=np.ndarray),
        DataIn("Indices", type_hint=list)
    ]
    outputs_def = [DataOut("Result", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            arr = await context.pull(self.id, "Array")
            indices = await context.pull(self.id, "Indices")

            if not isinstance(arr, np.ndarray):
                return np.array([])

            try:
                # Support list of ints or np.ndarray of ints
                idx_arr = np.array(indices, dtype=int)
                return arr[idx_arr]
            except Exception:
                return arr
        return None


@register_node("Numeric Arrays/operations/add_subtract")
class AddSubtractNdarrayNode(BaseNode):
    """Element-wise or constant addition/subtraction on an ndarray."""
    icon = "➕"
    display_name = "NDArray Add/Sub"
    description = "Adds or subtracts a constant or another array to/from an ndarray."

    inputs_def = [
        DataIn("Array", type_hint=np.ndarray),
        DataIn("Operand", type_hint=Any, default=1.0),
        DataIn("Operation", type_hint=str, default="add", widget="dropdown", options=["add", "subtract"])
    ]
    outputs_def = [DataOut("Result", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            arr = await context.pull(self.id, "Array")
            operand = await context.pull(self.id, "Operand")
            op = await context.pull(self.id, "Operation")

            if not isinstance(arr, np.ndarray):
                return np.array([])

            try:
                # check if operand is array-like or number
                if isinstance(operand, (list, np.ndarray)):
                    operand = np.array(operand, dtype=float)
                else:
                    operand = float(operand)

                if op == "subtract":
                    return arr - operand
                return arr + operand
            except Exception:
                return arr
        return None


@register_node("Numeric Arrays/operations/multiply_divide")
class MultiplyDivideNdarrayNode(BaseNode):
    """Element-wise or constant multiplication/division on an ndarray."""
    icon = "✖️"
    display_name = "NDArray Mul/Div"
    description = "Multiplies or divides an ndarray by a constant or another array."

    inputs_def = [
        DataIn("Array", type_hint=np.ndarray),
        DataIn("Operand", type_hint=Any, default=2.0),
        DataIn("Operation", type_hint=str, default="multiply", widget="dropdown", options=["multiply", "divide"])
    ]
    outputs_def = [DataOut("Result", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            arr = await context.pull(self.id, "Array")
            operand = await context.pull(self.id, "Operand")
            op = await context.pull(self.id, "Operation")

            if not isinstance(arr, np.ndarray):
                return np.array([])

            try:
                if isinstance(operand, (list, np.ndarray)):
                    operand = np.array(operand, dtype=float)
                else:
                    operand = float(operand)

                if op == "divide":
                    return arr / operand
                return arr * operand
            except Exception:
                return arr
        return None


@register_node("Numeric Arrays/operations/inner_product")
class InnerProductNdarrayNode(BaseNode):
    """Computes the inner (dot) product of two arrays."""
    icon = "⚫"
    display_name = "Inner Product"
    description = "Computes the inner (dot) product of two numeric arrays."

    inputs_def = [
        DataIn("ArrayA", type_hint=np.ndarray),
        DataIn("ArrayB", type_hint=np.ndarray)
    ]
    outputs_def = [DataOut("Product", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Product":
            a = await context.pull(self.id, "ArrayA")
            b = await context.pull(self.id, "ArrayB")

            if not isinstance(a, np.ndarray) or not isinstance(b, np.ndarray):
                return 0.0

            try:
                res = np.inner(a, b)
                if hasattr(res, "item"):
                    return res.item()
                return float(res)
            except Exception:
                return 0.0
        return None


@register_node("Numeric Arrays/operations/outer_product")
class OuterProductNdarrayNode(BaseNode):
    """Computes the outer product of two arrays."""
    icon = "⚪"
    display_name = "Outer Product"
    description = "Computes the outer product of two numeric arrays."

    inputs_def = [
        DataIn("ArrayA", type_hint=np.ndarray),
        DataIn("ArrayB", type_hint=np.ndarray)
    ]
    outputs_def = [DataOut("Product", type_hint=np.ndarray)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Product":
            a = await context.pull(self.id, "ArrayA")
            b = await context.pull(self.id, "ArrayB")

            if not isinstance(a, np.ndarray) or not isinstance(b, np.ndarray):
                return np.array([])

            try:
                return np.outer(a, b)
            except Exception:
                return np.array([])
        return None


@register_node("Numeric Arrays/operations/shape")
class ShapeNdarrayNode(BaseNode):
    """Returns the dimensions (shape) of an array."""
    icon = "📐"
    display_name = "NDArray Shape"
    description = "Returns the shape of a NumPy array as a list of dimensions."

    inputs_def = [
        DataIn("Array", type_hint=np.ndarray)
    ]
    outputs_def = [DataOut("Shape", type_hint=list)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Shape":
            arr = await context.pull(self.id, "Array")
            if not isinstance(arr, np.ndarray):
                return []
            return list(arr.shape)
        return None



@register_node("string/format")
class FormatStringNode(BaseNode):
    """Templates a string replacing {0}, {1}, {2} etc. placeholders."""
    icon = "🖹"
    display_name = "Format String"
    description = "Templates a string replacing {0} style placeholders."
    
    inputs_def = [
        DataIn("Template", type_hint=str, default="Value is {0}", widget="text"),
        DataIn("Arg0", type_hint=Any, default="", widget="text", optional=True),
        DataIn("Arg1", type_hint=Any, default="", widget="text", optional=True),
        DataIn("Arg2", type_hint=Any, default="", widget="text", optional=True)
    ]
    outputs_def = [DataOut("Result", type_hint=str)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            template = str(await context.pull(self.id, "Template"))
            arg0 = await context.pull(self.id, "Arg0")
            arg1 = await context.pull(self.id, "Arg1")
            arg2 = await context.pull(self.id, "Arg2")
            
            try:
                return template.format(arg0, arg1, arg2, arg0=arg0, arg1=arg1, arg2=arg2)
            except Exception as e:
                return f"[Format Error: {e}]"
        return None


@register_node("cluster/boundary/input")
class ClusterInputNode(BaseNode):
    """Anchor node representing a cluster input pin inside its sub-graph."""
    icon = "📥"
    display_name = "Cluster Input"
    description = "Exposes a cluster input boundary pin. Connect this to nodes inside the cluster."

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
            if hasattr(context, "parent_context") and hasattr(context, "_cluster_node_id"):
                pin_name_config = await context.pull(self.id, "Name")
                return await context.parent_context.pull(context._cluster_node_id, pin_name_config)
            return None
        return None


@register_node("cluster/boundary/output")
class ClusterOutputNode(BaseNode):
    """Anchor node representing a cluster output pin inside its sub-graph."""
    icon = "📤"
    display_name = "Cluster Output"
    description = "Exposes a cluster output boundary pin. Connect nodes inside the cluster to this."

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


@register_node("utility/passthrough")
class PassthroughNode(BaseNode):
    """Passes input data directly to output. Useful for organizing wires."""
    icon = "➔"
    display_name = "Passthrough"
    description = "Passes input data directly to output. Useful for organizing wires."
    default_width = 14
    default_height = 14
    is_passthrough = True

    inputs_def = [
        DataIn("In", type_hint=Any)
    ]
    outputs_def = [
        DataOut("Out", type_hint=Any)
    ]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Out":
            return await context.pull(self.id, "In")
        return None


@register_node("utility/exec_passthrough")
class ExecPassthroughNode(BaseNode):
    """Passes execution trigger directly to output. Useful for organizing exec wires."""
    icon = "➜"
    display_name = "Exec Passthrough"
    description = "Passes execution trigger directly to output. Useful for organizing exec wires."
    default_width = 14
    default_height = 14
    is_passthrough = True

    inputs_def = [
        ExecIn("In")
    ]
    outputs_def = [
        ExecOut("Out")
    ]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "In":
            return "Out"
        return None


@register_node("logic/has_changed")
class HasChangedNode(BaseNode):
    """Stateful node that triggers when a value changes since the last execution."""
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

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
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
            import numpy as np
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


@register_node("math/basic/calculator")
class CalculatorNode(BaseNode):
    """Evaluates a mathematical expression with dynamic variable inputs."""
    icon = "🧮"
    display_name = "Calculator"
    description = "Evaluates a mathematical expression with variable inputs."
    default_width = 240
    ui_behavior = {"custom_widget": "calculator", "render_standard_inputs": True}

    inputs_def = []
    outputs_def = [
        DataOut("Result", type_hint=float)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        variables = self.properties.get("variables", ["a", "b"])
        if isinstance(variables, str):
            variables = [v.strip() for v in variables.split(",") if v.strip()]
        
        for var in variables:
            self.inputs[var] = DataIn(var, type_hint=float, default=0.0, widget="number")

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            expression = self.properties.get("expression", self.properties.get("Expression", "a + b"))
            if not expression:
                return 0.0

            expr_processed = expression.replace("^", "**")

            variables = self.properties.get("variables", ["a", "b"])
            if isinstance(variables, str):
                variables = [v.strip() for v in variables.split(",") if v.strip()]

            local_vars = {}
            for var in variables:
                val = await context.pull(self.id, var)
                try:
                    local_vars[var] = float(val) if val is not None else 0.0
                except (ValueError, TypeError):
                    local_vars[var] = 0.0

            import math
            math_namespace = {
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'asin': math.asin, 'acos': math.acos, 'atan': math.atan, 'atan2': math.atan2,
                'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
                'exp': math.exp, 'log': math.log, 'log10': math.log10,
                'sqrt': math.sqrt, 'abs': abs, 'pi': math.pi, 'e': math.e,
                'min': min, 'max': max, 'round': round, 'floor': math.floor, 'ceil': math.ceil
            }
            eval_namespace = {**math_namespace, **local_vars}

            try:
                result = eval(expr_processed, {"__builtins__": {}}, eval_namespace)
                return float(result)
            except Exception as e:
                logger.error(f"Error evaluating Calculator expression '{expression}': {e}")
                raise e
        return None


@register_node("math/operations/linear_scale")
class LinearScaleNode(BaseNode):
    """Scales an input value or list of values using y = ax + b."""
    icon = "⚖️"
    display_name = "Linear Scale"
    description = "Scales a value or array linearly: ax + b."

    inputs_def = [
        DataIn("X", type_hint=Any),
        DataIn("A", type_hint=float, default=1.0, widget="number"),
        DataIn("B", type_hint=float, default=0.0, widget="number")
    ]
    outputs_def = [
        DataOut("Result", type_hint=Any)
    ]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            x = await context.pull(self.id, "X")
            a = float(await context.pull(self.id, "A"))
            b = float(await context.pull(self.id, "B"))

            if x is None:
                return None

            if isinstance(x, np.ndarray):
                return x * a + b
            elif isinstance(x, list):
                try:
                    return [float(item) * a + b for item in x]
                except (ValueError, TypeError):
                    pass
            try:
                return float(x) * a + b
            except (ValueError, TypeError):
                return None
        return None


@register_node("Numeric Arrays/manipulation/linspace")
class LinspaceNode(BaseNode):
    """Generates a linear sequence of values, equivalent to numpy.linspace."""
    icon = "📈"
    display_name = "Linspace"
    description = "Generates an ndarray of evenly spaced numbers over a specified interval."

    inputs_def = [
        DataIn("Start", type_hint=float, default=0.0, widget="number"),
        DataIn("Stop", type_hint=float, default=10.0, widget="number"),
        DataIn("Steps", type_hint=int, default=11, widget="number", min_val=1)
    ]
    outputs_def = [
        DataOut("Array", type_hint=np.ndarray)
    ]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Array":
            start = float(await context.pull(self.id, "Start"))
            stop = float(await context.pull(self.id, "Stop"))
            steps = int(await context.pull(self.id, "Steps"))

            steps = max(1, steps)
            if steps == 1:
                return np.array([start], dtype=float)

            import numpy as np
            return np.linspace(start, stop, steps)
        return None


@register_node("outputs/basic/led_indicator")
class LEDNode(BaseNode):
    """Circular passthrough node displaying state (green/red) dynamically."""
    icon = "🔴"
    display_name = "LED Status"
    description = "Circular passthrough status indicator showing green (True) or red (False) dynamically."
    default_width = 40
    default_height = 40
    is_passthrough = True

    inputs_def = [
        ExecIn("In"),
        DataIn("State", type_hint=bool, default=False)
    ]
    outputs_def = [
        ExecOut("Out")
    ]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "In":
            state = bool(await context.pull(self.id, "State"))
            await context.send_telemetry(self.id, {"state": state})
            return "Out"
        return None


