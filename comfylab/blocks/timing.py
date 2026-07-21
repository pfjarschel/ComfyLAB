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
import time
import logging
from typing import Any, Optional, Dict, List

logger = logging.getLogger("comfylab.blocks.timing")

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext


@register_block("control_flow/timing/sleep")
class SleepBlock(BaseBlock):
    """Delays execution for a specified number of seconds."""
    icon = "⏳"
    display_name = "Sleep"
    description = "Delays execution for a specified number of seconds."

    inputs_def = [
        ExecIn("In"),
        DataIn("Delay", type_hint=float, default=1.0, widget="number", min_val=0.0)
    ]
    outputs_def = [ExecOut("Out")]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        delay = await context.pull(self.id, "Delay")
        d = max(0.0, float(delay))
        await asyncio.sleep(d)
        return "Out"


@register_block("control_flow/timing/measure_time")
class MeasureTimeBlock(BaseBlock):
    """Measures the execution time of connected blocks in its timed block."""
    icon = "⏱️"
    display_name = "Measure Time"
    description = "Measures the time elapsed between execution tokens on 'Start' and 'Stop', and emits the duration in seconds."
    ui_behavior = {"custom_widget": "display_area"}

    inputs_def = [
        ExecIn("In")
    ]
    outputs_def = [
        ExecOut("Body"),
        ExecOut("Out"),
        DataOut("Time", type_hint=float)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._time = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        start_time = time.perf_counter()
        
        # Trigger execution of the timed block connected to "Body"
        await context.engine.trigger_exec(self.id, "Body", context)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        self._time = duration
        
        # Format duration with appropriate units for telemetry display
        if duration < 1e-6:
            display_val = f"{duration * 1e9:.2f} ns"
        elif duration < 1e-3:
            display_val = f"{duration * 1e6:.2f} µs"
        elif duration < 1.0:
            display_val = f"{duration * 1000:.2f} ms"
        else:
            display_val = f"{duration:.4f} s"

        await context.send_telemetry(self.id, {"value": display_val})
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Time":
            return self._time
        return None

    async def clear_data(self) -> None:
        self._time = 0.0


@register_block("control_flow/timing/timer")
class TimerBlock(BaseBlock):
    """Triggers downstream execution periodically at a specified interval."""
    icon = "⏱️"
    display_name = "Timer"
    description = "Triggers execution periodically at a specified interval with stopwatch timing."

    inputs_def = [
        ExecIn("Start"),
        ExecIn("Stop"),
        DataIn("Interval", type_hint=float, default=1000.0, widget="number", min_val=0.1),
        DataIn("Count", type_hint=int, default=0, widget="number", min_val=0),
        DataIn("StopCondition", type_hint=bool, default=False, optional=True)
    ]
    outputs_def = [
        ExecOut("Tick"),
        ExecOut("Finished")
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._stopped = False

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "Stop":
            self._stopped = True
            logger.info(f"Timer block '{self.id}' stop triggered.")
            return None

        if trigger_pin == "Start":
            self._stopped = False
            interval_ms = await context.pull(self.id, "Interval")
            count = int(await context.pull(self.id, "Count"))

            interval_sec = max(0.001, float(interval_ms) / 1000.0)
            logger.info(f"Starting Timer block '{self.id}' with interval {interval_ms}ms, count limit {count}.")

            i = 0
            while not self._stopped:
                if context.engine.state == "ABORTED":
                    break

                # Manual toggle check from block properties
                enabled = bool(self.properties.get("enabled", True))
                if not enabled:
                    logger.info(f"Timer block '{self.id}' stopped via disabled property.")
                    break

                # StopCondition check (forces upstream data re-evaluation)
                context.clear_cache()
                stop_cond = bool(await context.pull(self.id, "StopCondition"))
                if stop_cond:
                    logger.info(f"Timer block '{self.id}' stopped via StopCondition data pin.")
                    break

                # Loop count limit check
                if count > 0 and i >= count:
                    logger.info(f"Timer block '{self.id}' completed target count of {count}.")
                    break

                start_time = time.perf_counter()

                # Trigger loop body (Tick path) and wait for completion
                await context.engine.trigger_exec(self.id, "Tick", context)

                elapsed = time.perf_counter() - start_time
                remaining = interval_sec - elapsed

                if remaining > 0:
                    await asyncio.sleep(remaining)
                else:
                    # Yield to event loop to keep engine responsive if loop body took too long
                    await asyncio.sleep(0.001)

                i += 1

            return "Finished"
        return None
