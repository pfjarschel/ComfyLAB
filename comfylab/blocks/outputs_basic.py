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

import logging
import numpy as np
from typing import Any, Optional, Dict
from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, ExecutionContext

logger = logging.getLogger("comfylab.blocks.outputs_basic")


def clean_cell_value(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (float, np.floating)):
        if np.isnan(val):
            return "NaN"
        if np.isinf(val):
            return "Inf" if val > 0 else "-Inf"
        return float(val)
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, (bool, np.bool_)):
        return bool(val)
    if isinstance(val, np.ndarray):
        return [clean_cell_value(x) for x in val.flat[:100]]
    return str(val)


def _build_table_structure(data: Any, max_rows: int, max_cols: int) -> Dict[str, Any]:
    if data is None:
        return {"headers": [], "rows": [], "total_rows": 0, "total_cols": 0, "truncated": False}

    # Check for pandas DataFrame
    if hasattr(data, "columns") and hasattr(data, "values") and hasattr(data, "iloc"):
        try:
            total_rows, total_cols = data.shape
            headers = [str(c) for c in list(data.columns)[:max_cols]]
            truncated = total_rows > max_rows or total_cols > max_cols
            sub_df = data.iloc[:max_rows, :max_cols]
            rows = [[clean_cell_value(val) for val in row] for row in sub_df.values]
            return {
                "headers": headers,
                "rows": rows,
                "total_rows": total_rows,
                "total_cols": total_cols,
                "truncated": truncated
            }
        except Exception:
            pass

    # Check numpy array
    if isinstance(data, np.ndarray):
        if data.ndim == 0:
            val = clean_cell_value(data.item())
            return {"headers": ["Value"], "rows": [[val]], "total_rows": 1, "total_cols": 1, "truncated": False}
        elif data.ndim == 1:
            total_rows = len(data)
            total_cols = 1
            truncated = total_rows > max_rows
            sub_arr = data[:max_rows]
            rows = [[clean_cell_value(x)] for x in sub_arr]
            return {
                "headers": ["Value"],
                "rows": rows,
                "total_rows": total_rows,
                "total_cols": total_cols,
                "truncated": truncated
            }
        else:
            if data.ndim > 2:
                shape = data.shape
                data = data.reshape(shape[0], -1)
            total_rows, total_cols = data.shape
            truncated = total_rows > max_rows or total_cols > max_cols
            sub_arr = data[:max_rows, :max_cols]
            rows = [[clean_cell_value(val) for val in row] for row in sub_arr]
            headers = [f"Col {j}" for j in range(min(total_cols, max_cols))]
            return {
                "headers": headers,
                "rows": rows,
                "total_rows": total_rows,
                "total_cols": total_cols,
                "truncated": truncated
            }

    # Handle Dict
    if isinstance(data, dict):
        values = list(data.values())
        if values and all(isinstance(v, (list, tuple, np.ndarray)) for v in values):
            total_cols = len(data)
            col_keys = list(data.keys())[:max_cols]
            col_data = [list(data[k]) for k in col_keys]
            max_len = max(len(c) for c in col_data) if col_data else 0
            total_rows = max_len
            truncated = total_rows > max_rows or total_cols > max_cols

            rows = []
            for r in range(min(total_rows, max_rows)):
                row_vals = []
                for c_idx in range(len(col_keys)):
                    lst = col_data[c_idx]
                    row_vals.append(clean_cell_value(lst[r]) if r < len(lst) else None)
                rows.append(row_vals)
            headers = [str(k) for k in col_keys]
            return {
                "headers": headers,
                "rows": rows,
                "total_rows": total_rows,
                "total_cols": total_cols,
                "truncated": truncated
            }
        else:
            items = list(data.items())
            total_rows = len(items)
            total_cols = 2
            truncated = total_rows > max_rows
            rows = [[clean_cell_value(k), clean_cell_value(v)] for k, v in items[:max_rows]]
            return {
                "headers": ["Key", "Value"],
                "rows": rows,
                "total_rows": total_rows,
                "total_cols": total_cols,
                "truncated": truncated
            }

    # Handle List or Tuple
    if isinstance(data, (list, tuple)):
        total_rows = len(data)
        if total_rows == 0:
            return {"headers": [], "rows": [], "total_rows": 0, "total_cols": 0, "truncated": False}

        first = data[0]
        if isinstance(first, dict):
            all_keys = []
            for item in data:
                if isinstance(item, dict):
                    for k in item.keys():
                        if k not in all_keys:
                            all_keys.append(k)
            total_cols = len(all_keys)
            headers = [str(k) for k in all_keys[:max_cols]]
            truncated = total_rows > max_rows or total_cols > max_cols

            rows = []
            for item in data[:max_rows]:
                if isinstance(item, dict):
                    row = [clean_cell_value(item.get(k)) for k in all_keys[:max_cols]]
                else:
                    row = [clean_cell_value(item)] + [None] * (len(headers) - 1)
                rows.append(row)

            return {
                "headers": headers,
                "rows": rows,
                "total_rows": total_rows,
                "total_cols": total_cols,
                "truncated": truncated
            }

        if isinstance(first, (list, tuple, np.ndarray)):
            sub_data = data[:max_rows]
            total_cols = max(len(row) for row in data if isinstance(row, (list, tuple, np.ndarray))) if data else 0
            truncated = total_rows > max_rows or total_cols > max_cols

            headers = [f"Col {j}" for j in range(min(total_cols, max_cols))]
            rows = []
            for row in sub_data:
                r_list = list(row)[:max_cols] if isinstance(row, (list, tuple, np.ndarray)) else [row]
                rows.append([clean_cell_value(val) for val in r_list])

            return {
                "headers": headers,
                "rows": rows,
                "total_rows": total_rows,
                "total_cols": total_cols,
                "truncated": truncated
            }

        truncated = total_rows > max_rows
        rows = [[clean_cell_value(x)] for x in data[:max_rows]]
        return {
            "headers": ["Value"],
            "rows": rows,
            "total_rows": total_rows,
            "total_cols": 1,
            "truncated": truncated
        }

    val = clean_cell_value(data)
    return {
        "headers": ["Value"],
        "rows": [[val]],
        "total_rows": 1,
        "total_cols": 1,
        "truncated": False
    }


def format_table_data(data: Any, custom_headers: Any = None) -> Dict[str, Any]:
    MAX_ROWS = 1000
    MAX_COLS = 1000

    res = _build_table_structure(data, MAX_ROWS, MAX_COLS)

    if custom_headers:
        if isinstance(custom_headers, str):
            override_headers = [h.strip() for h in custom_headers.split(",") if h.strip()]
        elif isinstance(custom_headers, (list, tuple, np.ndarray)):
            override_headers = [str(h) for h in custom_headers]
        else:
            override_headers = [str(custom_headers)]
        
        if override_headers:
            for idx, h in enumerate(override_headers[:MAX_COLS]):
                if idx < len(res["headers"]):
                    res["headers"][idx] = h
                else:
                    res["headers"].append(h)
    return res


@register_block("outputs/basic/table_view")
class TableViewBlock(BaseBlock):
    """Displays lists, ndarrays, or dictionaries in a scrollable table view (up to 1000 rows × 1000 columns)."""
    icon = "📋"
    display_name = "Table View"
    description = "Displays lists, ndarrays, or dictionaries in a scrollable table view (up to 1000 rows × 1000 columns)."
    default_width = 340
    default_height = 260
    ui_behavior = {"custom_widget": "table_view", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("In"),
        DataIn("Data", type_hint=Any),
        DataIn("Headers", type_hint=list, optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        data = await context.pull(self.id, "Data")
        custom_headers = await context.pull(self.id, "Headers")
        
        payload = format_table_data(data, custom_headers)
        await context.send_telemetry(self.id, payload)
        return "Out"



@register_block("outputs/basic/print")
class PrintBlock(BaseBlock):
    """Prints a pulled value to standard output and continues execution."""
    icon = " >_ "
    display_name = "Print"
    description = "Prints a pulled value to standard output and continues execution."
    
    inputs_def = [
        ExecIn("In"),
        DataIn("Value", type_hint=Any, default="", widget="text")
    ]
    outputs_def = [ExecOut("Out")]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self.last_printed: Any = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        val = await context.pull(self.id, "Value")
        self.last_printed = val
        logger.info(f"[ComfyLAB Print '{self.id}'] >>> {val}")
        print(f"[ComfyLAB Print '{self.id}'] >>> {val}")
        return "Out"

    async def clear_data(self) -> None:
        self.last_printed = None


@register_block("outputs/basic/display")
class DisplayBlock(BaseBlock):
    """Displays a pulled value on the block itself by broadcasting telemetry."""
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


@register_block("outputs/basic/led_indicator")
class LEDBlock(BaseBlock):
    """Circular passthrough block displaying state (green/red) dynamically."""
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
