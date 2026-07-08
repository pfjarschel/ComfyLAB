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

"""
ComfyLAB Example Nodes - Educational Reference Implementation

This file contains example nodes that demonstrate key concepts for creating
custom ComfyLAB nodes. Each example is thoroughly commented to help newcomers
understand the patterns and best practices.

Examples included:
- RangeCheckNode: Conditional execution outputs (multiple ExecOut pins)
- CSVWriterNode: File I/O with proper teardown
- ArrayStatsNode: Array processing with multiple data outputs
- CounterNode: Stateful processing across executions
"""

import asyncio
import csv
import os
import logging
from typing import Any, Optional, Dict, List
import numpy as np

logger = logging.getLogger("comfylab.nodes.examples")

from comfylab.engine.registry import register_node
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext


@register_node("logic/range_check")
class RangeCheckNode(BaseNode):
    """
    Checks if a value is within a specified range and branches execution accordingly.
    
    This example demonstrates:
    - Multiple execution output pins (InRange/OutOfRange)
    - How to return different ExecOut pin names to control flow
    - Using optional inputs with default values
    """
    icon = "📏"
    display_name = "Range Check"
    description = "Checks if a value is within a range and branches execution."
    
    inputs_def = [
        ExecIn("In"),
        DataIn("Value", type_hint=float, default=0.0, widget="number"),
        DataIn("Min", type_hint=float, default=0.0, widget="number", optional=True),
        DataIn("Max", type_hint=float, default=100.0, widget="number", optional=True)
    ]
    outputs_def = [
        ExecOut("InRange"),
        ExecOut("OutOfRange"),
        DataOut("IsInRange", type_hint=bool)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._is_in_range = False

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        # Pull input values (lazy evaluation)
        value = await context.pull(self.id, "Value")
        min_val = await context.pull(self.id, "Min")
        max_val = await context.pull(self.id, "Max")
        
        # Check if value is in range
        self._is_in_range = min_val <= value <= max_val
        
        # Return the name of the ExecOut pin to trigger next
        # This controls which branch of the graph executes
        return "InRange" if self._is_in_range else "OutOfRange"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        # Serve the boolean result when downstream nodes query it
        if pin_name == "IsInRange":
            return self._is_in_range
        return None

    async def clear_data(self) -> None:
        self._is_in_range = False





@register_node("Numeric Arrays/operations/stats")
class ArrayStatsNode(BaseNode):
    """
    Computes statistics (min, max, mean) from an ndarray of values.
    
    This example demonstrates:
    - Processing array/list inputs
    - Multiple data output pins
    - Storing computed results for pull_data()
    - Handling edge cases (empty arrays)
    """
    icon = "📊"
    display_name = "Array Stats"
    description = "Computes min, max, and mean from an ndarray."
    
    inputs_def = [
        ExecIn("Compute"),
        DataIn("Array", type_hint=np.ndarray)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Min", type_hint=float),
        DataOut("Max", type_hint=float),
        DataOut("Mean", type_hint=float),
        DataOut("Count", type_hint=int)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._min = 0.0
        self._max = 0.0
        self._mean = 0.0
        self._count = 0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        # Pull the input array
        array = await context.pull(self.id, "Array")
        
        # Handle edge cases
        if array is None or not isinstance(array, np.ndarray) or len(array) == 0:
            self._min = 0.0
            self._max = 0.0
            self._mean = 0.0
            self._count = 0
        else:
            try:
                self._min = float(np.min(array))
                self._max = float(np.max(array))
                self._mean = float(np.mean(array))
                self._count = int(len(array))
            except Exception:
                self._min = 0.0
                self._max = 0.0
                self._mean = 0.0
                self._count = 0
        
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        # Serve computed statistics when downstream nodes query them
        if pin_name == "Min":
            return self._min
        elif pin_name == "Max":
            return self._max
        elif pin_name == "Mean":
            return self._mean
        elif pin_name == "Count":
            return self._count
        return None

    async def clear_data(self) -> None:
        self._min = 0.0
        self._max = 0.0
        self._mean = 0.0
        self._count = 0



@register_node("utility/counter")
class CounterNode(BaseNode):
    """
    Maintains a counter that increments on each execution.
    
    This example demonstrates:
    - Stateful processing (maintaining state across executions)
    - Using __init__ to initialize instance variables
    - How state persists between node executions within a run
    """
    icon = "🔢"
    display_name = "Counter"
    description = "Maintains a counter that increments on each execution."
    
    inputs_def = [
        ExecIn("Increment"),
        DataIn("Step", type_hint=int, default=1, widget="number", optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Count", type_hint=int)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        # Initialize counter to zero
        # This state persists across multiple executions within a single run
        self._count = 0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        # Pull the step value
        step = await context.pull(self.id, "Step")
        
        # Increment the counter
        self._count += int(step)
        
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        # Serve the current count when queried
        if pin_name == "Count":
            return self._count
        return None

    async def clear_data(self) -> None:
        self._count = 0

