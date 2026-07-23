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

from typing import Any, Optional, Dict, List
import numpy as np
from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext, make_dynamic_item_inputs


@register_block("Lists/manipulation/accumulate")
class AccumulateListBlock(BaseBlock):
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

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
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


@register_block("Lists/manipulation/create")
class CreateListBlock(BaseBlock):
    """Creates a list from a comma-separated string."""
    icon = "📥"
    display_name = "Create List"
    description = "Creates a list from a comma-separated string of numbers or texts."
    
    ui_behavior = {"dynamic_inputs": {"prefix": "Row", "type": "str", "widget": "text", "default_count": 1}}
    
    inputs_def = [
        DataIn("ParseNumbers", type_hint=bool, default=False, widget="checkbox")
    ]
    outputs_def = [DataOut("List", type_hint=list)]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        make_dynamic_item_inputs(self, "Row", 1, type_hint=str, default="")

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


@register_block("Lists/manipulation/pack")
class PackListBlock(BaseBlock):
    """Packs multiple inputs into a single List."""
    icon = "📦"
    display_name = "Pack List"
    description = "Packs multiple evaluated inputs into a standard python list."

    ui_behavior = {"dynamic_inputs": {"prefix": "Item", "type": "any", "default_count": 2}}
    
    inputs_def = []
    outputs_def = [DataOut("List", type_hint=list)]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        make_dynamic_item_inputs(self, "Item", 2, type_hint=Any, default=None)

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "List":
            item_count = int(self.properties.get("itemCount", 2))
            result = []
            for i in range(item_count):
                val = await context.pull(self.id, f"Item {i}")
                result.append(val)
            return result
        return None


@register_block("Lists/operations/get")
class GetListItemBlock(BaseBlock):
    """Retrieves a list item at a specific index."""
    icon = "🔍"
    display_name = "Get List Item"
    description = "Retrieves a list item at a specific index."
    
    inputs_def = [
        DataIn("List", type_hint=list),
        DataIn("Index", type_hint=Any, default=0, widget="number")
    ]
    outputs_def = [DataOut("Item", type_hint=Any)]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Item":
            arr = await context.pull(self.id, "List")
            if arr is None:
                return None
            raw_idx = await context.pull(self.id, "Index")
            if raw_idx is None:
                return None

            if isinstance(arr, np.ndarray):
                arr = arr.tolist()
            elif not isinstance(arr, (list, tuple)):
                return None

            try:
                if isinstance(raw_idx, str) and "," in raw_idx:
                    indices = [int(x.strip()) for x in raw_idx.split(",") if x.strip()]
                    curr = arr
                    for i in indices:
                        curr = curr[i]
                    if isinstance(curr, np.generic):
                        return curr.item()
                    return curr
                elif isinstance(raw_idx, (list, tuple)):
                    curr = arr
                    for i in raw_idx:
                        curr = curr[int(i)]
                    if isinstance(curr, np.generic):
                        return curr.item()
                    return curr
                else:
                    idx = int(raw_idx)
                    if 0 <= idx < len(arr):
                        res = arr[idx]
                    elif -len(arr) <= idx < 0:
                        res = arr[idx]
                    else:
                        return None
                    if isinstance(res, np.generic):
                        return res.item()
                    return res
            except Exception:
                return None
        return None


@register_block("Lists/operations/length")
class ListLengthBlock(BaseBlock):
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
            if arr is None:
                return 0
            if isinstance(arr, (list, tuple, np.ndarray)):
                return len(arr)
            return 0
        return None


@register_block("Lists/manipulation/concat")
class ConcatListsBlock(BaseBlock):
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


@register_block("Lists/manipulation/transpose")
class TransposeListBlock(BaseBlock):
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


@register_block("Lists/manipulation/append")
class AppendListBlock(BaseBlock):
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


@register_block("Lists/operations/sort")
class SortListBlock(BaseBlock):
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


@register_block("Lists/operations/slice")
class SliceListBlock(BaseBlock):
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

            if lst is None:
                return []
            if isinstance(lst, np.ndarray):
                lst = lst.tolist()
            elif not isinstance(lst, (list, tuple)):
                return []

            start_val = int(start) if start is not None else 0
            stop_val = int(stop) if stop is not None else len(lst)
            step_val = int(step) if step is not None else 1

            return lst[start_val:stop_val:step_val]
        return None


@register_block("Lists/operations/take")
class TakeListBlock(BaseBlock):
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

            if lst is None or indices is None:
                return []
            if isinstance(lst, np.ndarray):
                lst = lst.tolist()
            elif not isinstance(lst, (list, tuple)):
                return []

            if isinstance(indices, np.ndarray):
                indices = indices.tolist()
            elif not isinstance(indices, (list, tuple)):
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
