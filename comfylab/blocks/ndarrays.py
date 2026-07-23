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

import collections
from typing import Any, Optional, Dict, List
import numpy as np
from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext, make_dynamic_item_inputs, parse_shape


@register_block("Numeric Arrays/manipulation/create_filled")
class CreateFilledNdarrayBlock(BaseBlock):
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

            shape = parse_shape(shape_raw)

            return np.full(shape, val, dtype=float)
        return None


@register_block("Numeric Arrays/manipulation/create")
class CreateNdarrayBlock(BaseBlock):
    """Creates a NumPy array from a comma-separated string."""
    icon = "📥"
    display_name = "Create NDArray"
    description = "Creates a NumPy numeric array from a comma-separated string of numbers."
    
    ui_behavior = {"dynamic_inputs": {"prefix": "Row", "type": "str", "widget": "text", "default_count": 1}}
    
    inputs_def = []
    outputs_def = [DataOut("Array", type_hint=np.ndarray)]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        make_dynamic_item_inputs(self, "Row", 1, type_hint=str, default="")

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


@register_block("Numeric Arrays/manipulation/pack")
class PackNdarrayBlock(BaseBlock):
    """Packs multiple inputs into a NumPy Array."""
    icon = "📦"
    display_name = "Pack NDArray"
    description = "Packs multiple evaluated inputs into a NumPy ndarray. Raises an error if dimensions are inconsistent."

    ui_behavior = {"dynamic_inputs": {"prefix": "Item", "type": "any", "default_count": 2}}
    
    inputs_def = []
    outputs_def = [DataOut("Array", type_hint=np.ndarray)]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        make_dynamic_item_inputs(self, "Item", 2, type_hint=Any, default=None)

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


@register_block("Numeric Arrays/manipulation/accumulate")
class AccumulateNdarrayBlock(BaseBlock):
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

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
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


@register_block("Numeric Arrays/manipulation/concat")
class ConcatNdarraysBlock(BaseBlock):
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


@register_block("Numeric Arrays/manipulation/transpose")
class TransposeNdarrayBlock(BaseBlock):
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


@register_block("Numeric Arrays/manipulation/append")
class AppendNdarrayBlock(BaseBlock):
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


@register_block("Numeric Arrays/operations/get")
class GetNdarrayItemBlock(BaseBlock):
    """Retrieves a NumPy array item at a specific index."""
    icon = "🔍"
    display_name = "Get NDArray Item"
    description = "Retrieves an item at a specific index from a NumPy array."
    
    inputs_def = [
        DataIn("Array", type_hint=np.ndarray),
        DataIn("Index", type_hint=Any, default=0, widget="number")
    ]
    outputs_def = [DataOut("Item", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Item":
            arr = await context.pull(self.id, "Array")
            if arr is None:
                return None
            raw_idx = await context.pull(self.id, "Index")
            if raw_idx is None:
                return None
            
            if not isinstance(arr, np.ndarray):
                try:
                    arr = np.asarray(arr)
                except Exception:
                    return None

            try:
                if isinstance(raw_idx, str) and "," in raw_idx:
                    idx = tuple(int(x.strip()) for x in raw_idx.split(",") if x.strip())
                elif isinstance(raw_idx, (list, tuple)):
                    idx = tuple(int(x) for x in raw_idx)
                else:
                    idx = int(raw_idx)

                val = arr[idx]
                if isinstance(val, np.generic):
                    return val.item()
                if isinstance(val, np.ndarray) and val.ndim == 0:
                    return val.item()
                return val
            except Exception:
                return None
        return None


@register_block("Numeric Arrays/operations/length")
class NdarrayLengthBlock(BaseBlock):
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
            if arr is None:
                return 0
            if isinstance(arr, (list, tuple, np.ndarray)):
                return len(arr)
            return 0
        return None


@register_block("Numeric Arrays/operations/sort")
class SortNdarrayBlock(BaseBlock):
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
            if arr is None:
                return np.array([])
            if not isinstance(arr, np.ndarray):
                try:
                    arr = np.asarray(arr)
                except Exception:
                    return np.array([])
            return np.sort(arr)
        return None


@register_block("Numeric Arrays/operations/slice")
class SliceNdarrayBlock(BaseBlock):
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

            if arr is None:
                return np.array([])
            if not isinstance(arr, np.ndarray):
                try:
                    arr = np.asarray(arr)
                except Exception:
                    return np.array([])

            start_val = int(start) if start is not None else 0
            stop_val = int(stop) if stop is not None else len(arr)
            step_val = int(step) if step is not None else 1

            return arr[start_val:stop_val:step_val]
        return None


@register_block("Numeric Arrays/operations/take")
class TakeNdarrayBlock(BaseBlock):
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

            if arr is None:
                return np.array([])
            if not isinstance(arr, np.ndarray):
                try:
                    arr = np.asarray(arr)
                except Exception:
                    return np.array([])

            try:
                # Support list of ints or np.ndarray of ints
                idx_arr = np.array(indices, dtype=int)
                return arr[idx_arr]
            except Exception:
                return arr
        return None


@register_block("Numeric Arrays/operations/add_subtract")
class AddSubtractNdarrayBlock(BaseBlock):
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


@register_block("Numeric Arrays/operations/multiply_divide")
class MultiplyDivideNdarrayBlock(BaseBlock):
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


@register_block("Numeric Arrays/operations/inner_product")
class InnerProductNdarrayBlock(BaseBlock):
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


@register_block("Numeric Arrays/operations/outer_product")
class OuterProductNdarrayBlock(BaseBlock):
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


@register_block("Numeric Arrays/operations/shape")
class ShapeNdarrayBlock(BaseBlock):
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


@register_block("Numeric Arrays/manipulation/linspace")
class LinspaceBlock(BaseBlock):
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

            return np.linspace(start, stop, steps)
        return None


@register_block("Numeric Arrays/operations/moving_average")
class MovingAverageBlock(BaseBlock):
    """Calculates a moving average over a sliding window."""
    icon = "📈"
    display_name = "Moving Average"
    description = "Maintains a sliding window of recent values and outputs their average."
    
    inputs_def = [
        ExecIn("Update"),
        DataIn("Data", type_hint=float),
        DataIn("Window Size", type_hint=int, default=10, widget="number")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Average", type_hint=float),
        DataOut("Buffer", type_hint=list)
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._buffer = collections.deque()
        self._buffer_sum = 0.0
        self._current_avg = 0.0

    async def execute(self, context: ExecutionContext, pin_name: str):
        if pin_name == "Update":
            val = await context.pull(self.id, "Data")
            window_size = await context.pull(self.id, "Window Size")

            try:
                window_size = int(window_size) if window_size is not None else 10
            except ValueError:
                window_size = 10

            if val is not None:
                try:
                    fval = float(val)
                    self._buffer.append(fval)
                    self._buffer_sum += fval
                    while len(self._buffer) > window_size:
                        self._buffer_sum -= self._buffer.popleft()

                    if len(self._buffer) > 0:
                        self._current_avg = self._buffer_sum / len(self._buffer)
                except (ValueError, TypeError):
                    pass

            return "Out"
        return None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Average":
            return self._current_avg
        elif pin_name == "Buffer":
            return list(self._buffer)
        return None
