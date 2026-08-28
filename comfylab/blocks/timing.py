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
from typing import Any, Optional, Dict

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

    i18n = {
        "pt-BR": {
            "display_name": "Aguardar",
            "description": "Atrasa a execução por um número especificado de segundos.",
            "category": "Temporização",
            "pins": {
                "In": "Entrada",
                "Delay": "Atraso",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Esperar",
            "description": "Retrasa la ejecución por un número especificado de segundos.",
            "category": "Temporización",
            "pins": {
                "In": "Entrada",
                "Delay": "Retraso",
                "Out": "Salida"
            }
        }
    }

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

    i18n = {
        "pt-BR": {
            "display_name": "Medir Tempo",
            "description": "Mede o tempo decorrido entre tokens de execução no bloco, e emite a duração em segundos.",
            "category": "Temporização",
            "pins": {
                "In": "Entrada",
                "Body": "Corpo",
                "Out": "Saída",
                "Time": "Tempo"
            }
        },
        "es": {
            "display_name": "Medir Tiempo",
            "description": "Mide el tiempo transcurrido entre tokens de ejecución en el bloque, y emite la duración en segundos.",
            "category": "Temporización",
            "pins": {
                "In": "Entrada",
                "Body": "Cuerpo",
                "Out": "Salida",
                "Time": "Tiempo"
            }
        }
    }

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
        ExecOut("Finished"),
        DataOut("Index", type_hint=int)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Temporizador",
            "description": "Aciona a execução periodicamente em um intervalo especificado.",
            "category": "Temporização",
            "pins": {
                "Start": "Iniciar",
                "Stop": "Parar",
                "Interval": "Intervalo",
                "Count": "Contagem",
                "StopCondition": "Condição de Parada",
                "Tick": "Tique",
                "Finished": "Concluído",
                "Index": "Índice"
            }
        },
        "es": {
            "display_name": "Temporizador",
            "description": "Desencadena la ejecución periódicamente en un intervalo especificado.",
            "category": "Temporización",
            "pins": {
                "Start": "Iniciar",
                "Stop": "Detener",
                "Interval": "Intervalo",
                "Count": "Conteo",
                "StopCondition": "Condición de Parada",
                "Tick": "Tic",
                "Finished": "Terminado",
                "Index": "Índice"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._stopped = False
        self._index = 0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "Stop":
            self._stopped = True
            logger.info(f"Timer block '{self.id}' stop triggered.")
            return None

        if trigger_pin == "Start":
            self._stopped = False
            self._index = 0
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

                self._index = i
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

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Index":
            return self._index
        return None

    async def clear_data(self) -> None:
        self._index = 0
        self._stopped = False


@register_block("control_flow/timing/countdown_wait")
class CountdownWaitBlock(BaseBlock):
    """Delays execution for a specified duration while providing a live visual countdown, draining progress bar, and skip control."""
    icon = "⏱️"
    display_name = "Countdown Wait"
    description = "Delays execution for a specified duration with live countdown ticking, draining progress, and skip button."
    ui_behavior = {"custom_widget": "countdown_wait"}

    inputs_def = [
        ExecIn("In"),
        DataIn("Duration", type_hint=float, default=10.0, widget="number", min_val=0.05),
        ExecIn("Skip")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Remaining", type_hint=float),
        DataOut("Elapsed", type_hint=float),
        DataOut("Percentage", type_hint=float)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Espera com Contagem",
            "description": "Atrasa a execução por uma duração com contagem regressiva ao vivo, progresso e botão de pular.",
            "category": "Temporização",
            "pins": {
                "In": "Entrada",
                "Duration": "Duração",
                "Skip": "Pular",
                "Out": "Saída",
                "Remaining": "Restante",
                "Elapsed": "Decorrido",
                "Percentage": "Porcentagem"
            }
        },
        "es": {
            "display_name": "Espera con Cuenta Regresiva",
            "description": "Retrasa la ejecución por una duración con cuenta regresiva en vivo, progreso y botón de saltar.",
            "category": "Temporización",
            "pins": {
                "In": "Entrada",
                "Duration": "Duración",
                "Skip": "Saltar",
                "Out": "Salida",
                "Remaining": "Restante",
                "Elapsed": "Transcurrido",
                "Percentage": "Porcentaje"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._duration = 10.0
        self._remaining = 0.0
        self._elapsed = 0.0
        self._percentage = 0.0
        self._skipped = False

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "Skip":
            self._skipped = True
            return "Out"

        dur_raw = await context.pull(self.id, "Duration")
        try:
            total_duration = max(0.05, float(dur_raw))
        except (ValueError, TypeError):
            total_duration = 10.0

        self._duration = total_duration
        self._remaining = total_duration
        self._elapsed = 0.0
        self._percentage = 0.0
        self._skipped = False

        start_time = time.perf_counter()
        from comfylab.blocks.control_flow import _format_duration

        while not self._skipped:
            if context.engine.state == "ABORTED":
                break

            # Check if user clicked skip button from UI (stored in block properties)
            if self.properties.get("skip", False):
                self._skipped = True
                self.properties["skip"] = False
                break

            now = time.perf_counter()
            elapsed = now - start_time
            remaining = max(0.0, total_duration - elapsed)
            pct = min(100.0, (elapsed / total_duration) * 100.0)

            self._elapsed = round(elapsed, 2)
            self._remaining = round(remaining, 2)
            self._percentage = round(pct, 2)

            remaining_str = _format_duration(remaining)
            tenth = int((remaining - int(remaining)) * 10)
            detailed_str = f"{remaining_str}.{tenth}"

            # Broadcast live countdown telemetry
            await context.send_telemetry(self.id, {
                "duration": total_duration,
                "remaining": self._remaining,
                "elapsed": self._elapsed,
                "percentage": self._percentage,
                "remaining_str": remaining_str,
                "detailed_str": detailed_str,
                "resultMessage": f"⏱️ {detailed_str} ({pct:.0f}%)"
            })

            if remaining <= 0.0:
                break

            # Sleep in small slices (up to 100ms) for responsive UI and abort/skip checks
            sleep_slice = min(0.1, remaining)
            await asyncio.sleep(sleep_slice)

        self._remaining = 0.0
        self._elapsed = total_duration
        self._percentage = 100.0
        await context.send_telemetry(self.id, {
            "duration": total_duration,
            "remaining": 0.0,
            "elapsed": total_duration,
            "percentage": 100.0,
            "remaining_str": "00:00",
            "detailed_str": "00:00.0",
            "resultMessage": "Completed"
        })
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Remaining":
            return self._remaining
        elif pin_name == "Elapsed":
            return self._elapsed
        elif pin_name == "Percentage":
            return self._percentage
        return None

    async def clear_data(self) -> None:
        self._remaining = 0.0
        self._elapsed = 0.0
        self._percentage = 0.0
        self._skipped = False
