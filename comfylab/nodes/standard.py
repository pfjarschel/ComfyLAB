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


@register_node("math/arithmetic/add")
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
    icon = "🖨️"
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



@register_node("math/arithmetic/subtract")
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


@register_node("math/arithmetic/multiply")
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


@register_node("math/arithmetic/divide")
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
                raise ZeroDivisionError("Division by zero in math/arithmetic/divide node.")
            return float(a) / denom
        return None


@register_node("math/arithmetic/power")
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


@register_node("math/trigonometry/trig")
class TrigNode(BaseNode):
    """Computes trig functions (sin, cos, tan)."""
    icon = "📐"
    display_name = "Trigonometry"
    description = "Computes trig functions (sin, cos, tan) in radians or degrees."
    
    inputs_def = [
        DataIn("Value", type_hint=float, default=0.0, widget="number"),
        DataIn("Function", type_hint=str, default="sin", widget="dropdown", options=["sin", "cos", "tan"]),
        DataIn("UseDegrees", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=float)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            val = float(await context.pull(self.id, "Value"))
            func = await context.pull(self.id, "Function")
            deg = bool(await context.pull(self.id, "UseDegrees"))
            
            angle = math.radians(val) if deg else val
            
            if func == "sin":
                return math.sin(angle)
            elif func == "cos":
                return math.cos(angle)
            elif func == "tan":
                return math.tan(angle)
            return 0.0
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


@register_node("arrays/manipulation/accumulate")
class AccumulateArrayNode(BaseNode):
    """Accumulates input values into an array over multiple execution steps."""
    icon = "📥"
    display_name = "Accumulate"
    description = "Accumulates input values into an array. Has an Append pin to add items and a Reset pin to clear them."
    ui_behavior = {"custom_widget": "display_area"}

    inputs_def = [
        ExecIn("Append"),
        ExecIn("Reset"),
        DataIn("Value", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Array", type_hint=list)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._array: List[Any] = []
    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "Reset":
            self._array = []
        elif trigger_pin == "Append":
            val = await context.pull(self.id, "Value")
            if val is not None:
                self._array.append(val)
        
        # Send the list count or contents to telemetry to display on the node
        display_str = f"[{', '.join(str(x) for x in self._array)}]" if len(self._array) <= 3 else f"Array ({len(self._array)} items)"
        await context.send_telemetry(self.id, {"value": display_str})
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Array":
            return self._array
        return None

    async def clear_data(self) -> None:
        self._array = []


@register_node("arrays/manipulation/create")
class CreateArrayNode(BaseNode):
    """Creates a list from a comma-separated string."""
    icon = "📥"
    display_name = "Create Array"
    description = "Creates an array from a comma-separated string of numbers or texts."
    
    inputs_def = [
        DataIn("CSVString", type_hint=str, default="1, 2, 3, 4, 5", widget="text"),
        DataIn("ParseNumbers", type_hint=bool, default=True, widget="checkbox")
    ]
    outputs_def = [DataOut("Array", type_hint=list)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Array":
            csv_str = await context.pull(self.id, "CSVString")
            parse_num = bool(await context.pull(self.id, "ParseNumbers"))
            
            if not csv_str:
                return []
                
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
                return parsed
            return items
        return None


@register_node("arrays/operations/get")
class GetArrayItemNode(BaseNode):
    """Retrieves an item at a specific index from an array."""
    icon = "🔍"
    display_name = "Get Item"
    description = "Retrieves an item at a specific index from an array."
    
    inputs_def = [
        DataIn("Array", type_hint=list),
        DataIn("Index", type_hint=int, default=0, widget="number")
    ]
    outputs_def = [DataOut("Item", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Item":
            arr = await context.pull(self.id, "Array")
            idx = int(await context.pull(self.id, "Index"))
            
            if not arr or not isinstance(arr, list):
                return None
                
            if 0 <= idx < len(arr):
                return arr[idx]
            elif -len(arr) <= idx < 0:
                return arr[idx]
            return None
        return None


@register_node("arrays/operations/length")
class ArrayLengthNode(BaseNode):
    """Returns the size of the array."""
    icon = "📏"
    display_name = "Array Length"
    description = "Returns the size of the array."
    
    inputs_def = [
        DataIn("Array", type_hint=list)
    ]
    outputs_def = [DataOut("Length", type_hint=int)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Length":
            arr = await context.pull(self.id, "Array")
            if not arr or not isinstance(arr, list):
                return 0
            return len(arr)
        return None


@register_node("arrays/manipulation/concat")
class ConcatArraysNode(BaseNode):
    """Concatenates two arrays."""
    icon = "🔗"
    display_name = "Concatenate Arrays"
    description = "Concatenates two arrays."
    
    inputs_def = [
        DataIn("ArrayA", type_hint=list),
        DataIn("ArrayB", type_hint=list)
    ]
    outputs_def = [DataOut("Result", type_hint=list)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = await context.pull(self.id, "ArrayA")
            b = await context.pull(self.id, "ArrayB")
            
            arr_a = a if isinstance(a, list) else ([a] if a is not None else [])
            arr_b = b if isinstance(b, list) else ([b] if b is not None else [])
            
            return arr_a + arr_b
        return None


@register_node("string/concat")
class ConcatStringsNode(BaseNode):
    """Concatenates string A and B."""
    icon = "➕"
    display_name = "Concatenate Strings"
    description = "Concatenates string A and string B."
    
    inputs_def = [
        DataIn("A", type_hint=str, default="", widget="text"),
        DataIn("B", type_hint=str, default="", widget="text"),
        DataIn("Separator", type_hint=str, default="", widget="text", optional=True)
    ]
    outputs_def = [DataOut("Result", type_hint=str)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = str(await context.pull(self.id, "A"))
            b = str(await context.pull(self.id, "B"))
            sep = str(await context.pull(self.id, "Separator"))
            return a + sep + b
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


@register_node("string/case")
class CaseStringNode(BaseNode):
    """Converts a string to UPPER or lower case."""
    icon = "🔠"
    display_name = "String Case"
    description = "Converts a string to UPPER or lower case."
    
    inputs_def = [
        DataIn("InputString", type_hint=str, default="", widget="text"),
        DataIn("ToUppercase", type_hint=bool, default=True, widget="checkbox")
    ]
    outputs_def = [DataOut("Result", type_hint=str)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            inp = str(await context.pull(self.id, "InputString"))
            upper = bool(await context.pull(self.id, "ToUppercase"))
            return inp.upper() if upper else inp.lower()
        return None


@register_node("macro/boundary/input")
class MacroInputNode(BaseNode):
    """Anchor node representing a macro input pin inside its sub-graph."""
    icon = "📥"
    display_name = "Macro Input"
    description = "Exposes a macro input boundary pin. Connect this to nodes inside the macro."

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
            if hasattr(context, "parent_context") and hasattr(context, "_macro_node_id"):
                pin_name_config = await context.pull(self.id, "Name")
                return await context.parent_context.pull(context._macro_node_id, pin_name_config)
            return None
        return None


@register_node("macro/boundary/output")
class MacroOutputNode(BaseNode):
    """Anchor node representing a macro output pin inside its sub-graph."""
    icon = "📤"
    display_name = "Macro Output"
    description = "Exposes a macro output boundary pin. Connect nodes inside the macro to this."

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
                # Record that this macro output was triggered in the macro execution context
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


@register_node("math/arithmetic/calculator")
class CalculatorNode(BaseNode):
    """Evaluates a mathematical expression with dynamic variable inputs."""
    icon = "🧮"
    display_name = "Calculator"
    description = "Evaluates a mathematical expression with variable inputs."
    default_width = 240
    ui_behavior = {"custom_widget": "calculator"}

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

            if isinstance(x, list):
                try:
                    return [float(item) * a + b for item in x]
                except (ValueError, TypeError):
                    pass
            try:
                return float(x) * a + b
            except (ValueError, TypeError):
                return None
        return None


@register_node("arrays/manipulation/ramp_generator")
class RampGeneratorNode(BaseNode):
    """Generates a linear ramp of values, equivalent to numpy.linspace."""
    icon = "📈"
    display_name = "Ramp Generator"
    description = "Generates a list of evenly spaced numbers over a specified interval."

    inputs_def = [
        DataIn("Start", type_hint=float, default=0.0, widget="number"),
        DataIn("Stop", type_hint=float, default=10.0, widget="number"),
        DataIn("Steps", type_hint=int, default=11, widget="number", min_val=1)
    ]
    outputs_def = [
        DataOut("Array", type_hint=list)
    ]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Array":
            start = float(await context.pull(self.id, "Start"))
            stop = float(await context.pull(self.id, "Stop"))
            steps = int(await context.pull(self.id, "Steps"))

            steps = max(1, steps)
            if steps == 1:
                return [start]

            import numpy as np
            return np.linspace(start, stop, steps).tolist()
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


