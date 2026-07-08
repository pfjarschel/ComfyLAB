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
import numpy as np

logger = logging.getLogger("comfylab.nodes.io")

from comfylab.engine.registry import register_node
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext


@register_node("File I\/O/path_generator")
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


@register_node("File I\/O/csv_logger")
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

        if isinstance(data, np.ndarray):
            data = data.tolist()
        if isinstance(headers, np.ndarray):
            headers = headers.tolist()

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


@register_node("File I\/O/parquet_logger")
class ParquetLoggerNode(BaseNode):
    """Logs experimental data (scalars, lists, or dictionaries) to a Parquet file."""
    icon = "📝"
    display_name = "Parquet Logger"
    description = "Logs structured data rows to a Parquet file. Highly optimized for large matrices and columnar data. Appending is supported via fastparquet."

    inputs_def = [
        ExecIn("Write"),
        DataIn("FilePath", type_hint=str, default="output.parquet", widget="text"),
        DataIn("Data", type_hint=Any),
        DataIn("Headers", type_hint=list, optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        import pandas as pd
        
        filepath = await context.pull(self.id, "FilePath")
        data = await context.pull(self.id, "Data")
        headers = await context.pull(self.id, "Headers")

        if isinstance(data, np.ndarray):
            data = data.tolist()
        if isinstance(headers, np.ndarray):
            headers = headers.tolist()

        if not filepath or data is None:
            return "Out"
            
        if isinstance(headers, str):
            headers = [h.strip() for h in headers.split(',')]
            
        file_empty = not os.path.exists(filepath) or os.path.getsize(filepath) == 0

        df = None

        if isinstance(data, dict):
            # Check if values are lists (writing columns) or scalars (writing a single row)
            is_col_format = any(isinstance(v, list) for v in data.values())
            
            if is_col_format:
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
        
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], list):
                # 2D array (list of columns)
                df = pd.DataFrame(data).T
                if headers:
                    df.columns = headers
            else:
                # 1D array (single column)
                df = pd.DataFrame(data)
                if headers:
                    df.columns = headers
        else:
            # Scalar
            df = pd.DataFrame([data])
            if headers:
                df.columns = headers

        if df is not None:
            # Parquet requires all column names to be strings
            df.columns = df.columns.astype(str)
            
            if not file_empty:
                df.to_parquet(filepath, engine='fastparquet', append=True)
            else:
                df.to_parquet(filepath, engine='fastparquet')

        return "Out"


@register_node("File I\/O/csv_loader")
class CSVLoaderNode(BaseNode):
    """Reads a CSV file into data arrays."""
    icon = "📂"
    display_name = "CSV Loader"
    description = "Reads a CSV file and outputs its contents as Columns (2D array), Headers, and a Dictionary mapping names to arrays."

    inputs_def = [
        ExecIn("Read"),
        DataIn("FilePath", type_hint=str, default="data.csv", widget="text"),
        DataIn("SkipLines", type_hint=int, default=0, widget="number")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Columns", type_hint=np.ndarray),
        DataOut("Headers", type_hint=list)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._loaded_columns: np.ndarray = np.array([])
        self._loaded_headers: List[str] = []

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Columns":
            return self._loaded_columns
        elif pin_name == "Headers":
            return self._loaded_headers
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        import pandas as pd
        
        filepath = await context.pull(self.id, "FilePath")
        skip_lines = await context.pull(self.id, "SkipLines")
        if skip_lines is None:
            skip_lines = 0

        if not filepath or not os.path.exists(filepath):
            self._loaded_columns = []
            self._loaded_headers = []
            return "Out"

        try:
            df = pd.read_csv(filepath, skiprows=int(skip_lines))
            self._loaded_columns = df.values.T
            self._loaded_headers = df.columns.astype(str).tolist()
        except Exception:
            self._loaded_columns = np.array([])
            self._loaded_headers = []

        return "Out"


@register_node("File I\/O/parquet_loader")
class ParquetLoaderNode(BaseNode):
    """Reads a Parquet file into data arrays."""
    icon = "📂"
    display_name = "Parquet Loader"
    description = "Reads a Parquet file and outputs Columns, Headers, and a Dictionary."

    inputs_def = [
        ExecIn("Read"),
        DataIn("FilePath", type_hint=str, default="data.parquet", widget="text"),
        DataIn("ColumnsToLoad", type_hint=str, default="", widget="text", optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Columns", type_hint=np.ndarray),
        DataOut("Headers", type_hint=list)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._loaded_columns: np.ndarray = np.array([])
        self._loaded_headers: List[str] = []

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Columns":
            return self._loaded_columns
        elif pin_name == "Headers":
            return self._loaded_headers
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        import pandas as pd
        
        filepath = await context.pull(self.id, "FilePath")
        columns_str = await context.pull(self.id, "ColumnsToLoad")

        if not filepath or not os.path.exists(filepath):
            self._loaded_columns = []
            self._loaded_headers = []
            return "Out"

        cols = None
        if columns_str and isinstance(columns_str, str):
            cols = [c.strip() for c in columns_str.split(',') if c.strip()]
        elif isinstance(columns_str, list) and len(columns_str) > 0:
            cols = [str(c).strip() for c in columns_str if str(c).strip()]

        try:
            df = pd.read_parquet(filepath, engine='fastparquet', columns=cols if cols else None)
            self._loaded_columns = df.values.T
            self._loaded_headers = df.columns.astype(str).tolist()
        except Exception:
            self._loaded_columns = np.array([])
            self._loaded_headers = []

        return "Out"
