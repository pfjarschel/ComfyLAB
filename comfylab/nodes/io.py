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

import os
import csv
from datetime import datetime
import logging
from typing import Any, Optional, Dict, List

logger = logging.getLogger("comfylab.nodes.io")

from comfylab.engine.registry import register_node
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext


@register_node("files/path_generator")
class FilePathGeneratorNode(BaseNode):
    """Generates file names dynamically using timestamps to prevent overwriting."""
    icon = "📂"
    display_name = "Path Generator"
    description = "Generates a file path using a prefix, current timestamp, and extension."

    inputs_def = [
        DataIn("Prefix", type_hint=str, default="data", widget="text"),
        DataIn("Extension", type_hint=str, default=".csv", widget="text"),
        DataIn("FormatPattern", type_hint=str, default="", widget="text", optional=True),
        DataIn("Subfolder", type_hint=str, default="", widget="text", optional=True)
    ]
    outputs_def = [
        DataOut("FilePath", type_hint=str)
    ]

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "FilePath":
            prefix = await context.pull(self.id, "Prefix")
            ext = await context.pull(self.id, "Extension")
            pattern = await context.pull(self.id, "FormatPattern")
            subfolder = await context.pull(self.id, "Subfolder")

            if not pattern:
                pattern = "%Y-%m-%d_%H%M%S"
            if ext and not ext.startswith("."):
                ext = "." + ext

            timestamp = datetime.now().strftime(pattern)
            filename = f"{prefix}_{timestamp}{ext}"

            if subfolder:
                # Ensure directory exists
                os.makedirs(subfolder, exist_ok=True)
                filepath = os.path.join(subfolder, filename)
            else:
                filepath = filename

            return filepath
        return None


@register_node("files/csv_logger")
class DataLoggerNode(BaseNode):
    """Logs experimental data (scalars, lists, or dictionaries) to a CSV file."""
    icon = "📝"
    display_name = "CSV Logger"
    description = "Logs structured data rows to a CSV file. Supports appending or overwriting."

    inputs_def = [
        ExecIn("Write"),
        DataIn("FilePath", type_hint=str, default="output.csv", widget="text"),
        DataIn("Data", type_hint=Any),
        DataIn("Headers", type_hint=list, optional=True),
        DataIn("Transpose", type_hint=bool, default=True, widget="checkbox", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        filepath = await context.pull(self.id, "FilePath")
        data = await context.pull(self.id, "Data")
        headers = await context.pull(self.id, "Headers")
        transpose = await context.pull(self.id, "Transpose")
        mode_prop = self.properties.get("mode", "append").lower()

        if isinstance(headers, str):
            # If the user passed a single string like "Time, Voltage", split it
            headers = [h.strip() for h in headers.split(',')]
        # Removed the quote stripping from list items to preserve user's typed quotes

        if not filepath:
            raise ValueError("CSV Logger: FilePath input cannot be empty.")

        # Ensure parent directory of filepath exists
        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        file_exists = os.path.exists(filepath)
        file_empty = not file_exists or os.path.getsize(filepath) == 0

        # Determine open mode
        open_mode = 'w' if (mode_prop == "overwrite" or not file_exists) else 'a'

        if isinstance(data, dict):
            # Check if values are lists (writing columns) or scalars (writing a single row)
            is_col_format = any(isinstance(v, list) for v in data.values())
            
            if is_col_format:
                keys = list(data.keys())
                lengths = [len(data[k]) for k in keys if isinstance(data[k], list)]
                max_len = max(lengths) if lengths else 0
                
                with open(filepath, open_mode, newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if open_mode == 'w' or file_empty:
                        writer.writerow(keys)
                    for idx in range(max_len):
                        row = []
                        for k in keys:
                            val = data[k]
                            if isinstance(val, list):
                                row.append(val[idx] if idx < len(val) else "")
                            else:
                                row.append(val if idx == 0 else "")
                        writer.writerow(row)
            else:
                keys = list(data.keys())
                with open(filepath, open_mode, newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    if open_mode == 'w' or file_empty:
                        writer.writeheader()
                    writer.writerow(data)
        
        elif isinstance(data, list):
            if transpose:
                if len(data) > 0 and isinstance(data[0], list):
                    # 2D array transpose
                    data = list(map(list, zip(*data)))
                else:
                    # 1D array transpose to column
                    data = [[x] for x in data]

            if len(data) > 0 and isinstance(data[0], list):
                # Multiple rows
                with open(filepath, open_mode, newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if (open_mode == 'w' or file_empty) and headers:
                        f.write(",".join(str(h) for h in headers) + "\n")
                    writer.writerows(data)
            else:
                # Single row
                with open(filepath, open_mode, newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if (open_mode == 'w' or file_empty) and headers:
                        f.write(",".join(str(h) for h in headers) + "\n")
                    writer.writerow(data)
        else:
            # Scalar
            row = [data]
            with open(filepath, open_mode, newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if (open_mode == 'w' or file_empty) and headers:
                    f.write(",".join(str(h) for h in headers) + "\n")
                writer.writerow(row)

        return "Out"
