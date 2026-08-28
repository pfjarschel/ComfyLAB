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
from typing import Any, Optional, Dict
from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext


def _format_duration(seconds: float) -> str:
    """Formats duration in seconds into human-readable MM:SS or HH:MM:SS."""
    if seconds <= 0:
        return "00:00"
    sec = int(seconds)
    if sec >= 3600:
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    elif sec >= 60:
        m = sec // 60
        s = sec % 60
        return f"{m:02d}:{s:02d}"
    else:
        return f"00:{sec:02d}"

_format_etr = _format_duration
_format_eta = _format_duration


@register_block("control_flow/basic/if_else")
class IfElseBlock(BaseBlock):
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

    i18n = {
        "pt-BR": {
            "display_name": "Se/Senão",
            "description": "Ramifica o caminho de execução com base em uma condição booleana.",
            "category": "Controle de Fluxo",
            "pins": {
                "In": "Entrada",
                "Condition": "Condição",
                "True": "Verdadeiro",
                "False": "Falso"
            }
        },
        "es": {
            "display_name": "Si/Sino",
            "description": "Ramifica la ruta de ejecución basándose en una condición booleana.",
            "category": "Control de Flujo",
            "pins": {
                "In": "Entrada",
                "Condition": "Condición",
                "True": "Verdadero",
                "False": "Falso"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        cond = await context.pull(self.id, "Condition")
        return "True" if bool(cond) else "False"


@register_block("control_flow/loops/for_loop")
class ForLoopBlock(BaseBlock):
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
        DataOut("Index", type_hint=int),
        DataOut("Percentage", type_hint=float),
        DataOut("ETR", type_hint=float)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Laço For",
            "description": "Itera um número especificado de vezes, acionando o corpo do laço.",
            "category": "Controle de Fluxo",
            "pins": {
                "Start": "Iniciar",
                "Count": "Contagem",
                "LoopBody": "CorpoDoLaço",
                "Done": "Concluído",
                "Index": "Índice",
                "Percentage": "Porcentagem",
                "ETR": "Tempo Restante (ETR)"
            }
        },
        "es": {
            "display_name": "Bucle For",
            "description": "Itera un número especificado de veces, activando el cuerpo del bucle.",
            "category": "Control de Flujo",
            "pins": {
                "Start": "Iniciar",
                "Count": "Conteo",
                "LoopBody": "CuerpoDelBucle",
                "Done": "Hecho",
                "Index": "Índice",
                "Percentage": "Porcentaje",
                "ETR": "Tiempo Restante (ETR)"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._index = 0
        self._percentage = 0.0
        self._etr = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        raw_count = await context.pull(self.id, "Count")
        try:
            count = max(0, int(raw_count))
        except (ValueError, TypeError):
            count = 0

        self._index = 0
        self._percentage = 0.0
        self._etr = 0.0

        if count == 0:
            self._percentage = 100.0
            self._etr = 0.0
            await context.send_telemetry(self.id, {"resultMessage": "Completed (0 iters)"})
            return "Done"

        start_time = time.perf_counter()
        last_telemetry_time = 0.0

        for i in range(count):
            if context.engine.state == "ABORTED":
                break
            await asyncio.sleep(0) # Yield to event loop to prevent CPU blocking (no artificial delay)
            context.clear_cache()
            self._index = i
            
            # Progress calculation (Option A: 1-indexed current step progress)
            self._percentage = round(((i + 1) / count) * 100.0, 2)

            # ETR calculation (based on average elapsed time per completed iteration)
            if i > 0:
                elapsed = time.perf_counter() - start_time
                avg_per_iter = elapsed / i
                remaining_iters = count - i
                self._etr = round(avg_per_iter * remaining_iters, 2)
                etr_str = _format_etr(self._etr)
            else:
                self._etr = 0.0
                etr_str = "--:--"

            now = time.perf_counter()
            if now - last_telemetry_time >= 0.1 or i == count - 1:
                last_telemetry_time = now
                await context.send_telemetry(self.id, {
                    "resultMessage": f"{self._percentage:.1f}% (ETR {etr_str})"
                })

            # Trigger execution of the LoopBody sub-graph
            await context.engine.trigger_exec(self.id, "LoopBody", context)

        self._percentage = 100.0
        self._etr = 0.0
        await context.send_telemetry(self.id, {"resultMessage": f"Completed ({count} iters)"})
        return "Done"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Index":
            return self._index
        elif pin_name == "Percentage":
            return self._percentage
        elif pin_name in ("ETR", "ETA"):
            return self._etr
        return None

    async def clear_data(self) -> None:
        self._index = 0
        self._percentage = 0.0
        self._etr = 0.0


@register_block("control_flow/loops/while_loop")
class WhileLoopBlock(BaseBlock):
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
        ExecOut("Done"),
        DataOut("Index", type_hint=int)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Laço While",
            "description": "Itera enquanto uma condição for Verdadeira.",
            "category": "Controle de Fluxo",
            "pins": {
                "Start": "Iniciar",
                "Condition": "Condição",
                "LoopBody": "CorpoDoLaço",
                "Done": "Concluído",
                "Index": "Índice"
            }
        },
        "es": {
            "display_name": "Bucle While",
            "description": "Itera mientras una condición sea Verdadera.",
            "category": "Control de Flujo",
            "pins": {
                "Start": "Iniciar",
                "Condition": "Condición",
                "LoopBody": "CuerpoDelBucle",
                "Done": "Hecho",
                "Index": "Índice"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._index = 0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        self._index = 0
        while True:
            if context.engine.state == "ABORTED":
                break
            await asyncio.sleep(0) # Yield to event loop to prevent CPU blocking (no artificial delay)
            context.clear_cache()
            cond = await context.pull(self.id, "Condition")
            if not bool(cond):
                break
            await context.engine.trigger_exec(self.id, "LoopBody", context)
            self._index += 1
        return "Done"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Index":
            return self._index
        return None

    async def clear_data(self) -> None:
        self._index = 0


@register_block("control_flow/loops/for_each")
class ForEachLoopBlock(BaseBlock):
    """Iterates over each item in a list or array, triggering the loop body branch for each item."""
    icon = "🔁"
    display_name = "For Each Loop"
    description = "Iterates over each item in a list or array, triggering the loop body branch for each item."

    inputs_def = [
        ExecIn("Start"),
        DataIn("Items", type_hint=Any, default=[])
    ]
    outputs_def = [
        ExecOut("LoopBody"),
        ExecOut("Done"),
        DataOut("Item", type_hint=Any),
        DataOut("Index", type_hint=int),
        DataOut("Percentage", type_hint=float),
        DataOut("ETR", type_hint=float)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Laço For Each",
            "description": "Itera sobre cada item em uma lista ou array, acionando o corpo do laço para cada item.",
            "category": "Controle de Fluxo",
            "pins": {
                "Start": "Iniciar",
                "Items": "Itens",
                "LoopBody": "CorpoDoLaço",
                "Done": "Concluído",
                "Item": "Item",
                "Index": "Índice",
                "Percentage": "Porcentagem",
                "ETR": "Tempo Restante (ETR)"
            }
        },
        "es": {
            "display_name": "Bucle Para Cada",
            "description": "Itera sobre cada elemento en una lista o matriz, activando el cuerpo del bucle para cada elemento.",
            "category": "Control de Flujo",
            "pins": {
                "Start": "Iniciar",
                "Items": "Elementos",
                "LoopBody": "CuerpoDelBucle",
                "Done": "Hecho",
                "Item": "Elemento",
                "Index": "Índice",
                "Percentage": "Porcentaje",
                "ETR": "Tiempo Restante (ETR)"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._current_item = None
        self._current_index = 0
        self._percentage = 0.0
        self._etr = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        items = await context.pull(self.id, "Items")
        if items is None:
            items = []

        if hasattr(items, "__iter__") and not isinstance(items, (str, bytes, dict)):
            iterable = list(items)
        else:
            iterable = [items]

        total = len(iterable)
        self._current_index = 0
        self._current_item = None
        self._percentage = 0.0
        self._etr = 0.0

        if total == 0:
            self._percentage = 100.0
            self._etr = 0.0
            await context.send_telemetry(self.id, {"resultMessage": "Completed (0 items)"})
            return "Done"

        start_time = time.perf_counter()
        last_telemetry_time = 0.0

        for i, item in enumerate(iterable):
            if context.engine.state == "ABORTED":
                break
            await asyncio.sleep(0) # Yield to event loop to prevent CPU blocking
            context.clear_cache()
            self._current_index = i
            self._current_item = item

            # Progress calculation (Option A: 1-indexed current step progress)
            self._percentage = round(((i + 1) / total) * 100.0, 2)

            # ETR calculation (based on average elapsed time per completed iteration)
            if i > 0:
                elapsed = time.perf_counter() - start_time
                avg_per_iter = elapsed / i
                remaining_iters = total - i
                self._etr = round(avg_per_iter * remaining_iters, 2)
                etr_str = _format_etr(self._etr)
            else:
                self._etr = 0.0
                etr_str = "--:--"

            now = time.perf_counter()
            if now - last_telemetry_time >= 0.1 or i == total - 1:
                last_telemetry_time = now
                await context.send_telemetry(self.id, {
                    "resultMessage": f"{self._percentage:.1f}% (ETR {etr_str})"
                })

            # Trigger execution of the LoopBody sub-graph
            await context.engine.trigger_exec(self.id, "LoopBody", context)

        self._percentage = 100.0
        self._etr = 0.0
        await context.send_telemetry(self.id, {"resultMessage": f"Completed ({total} items)"})
        return "Done"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Item":
            return self._current_item
        elif pin_name == "Index":
            return self._current_index
        elif pin_name == "Percentage":
            return self._percentage
        elif pin_name in ("ETR", "ETA"):
            return self._etr
        return None

    async def clear_data(self) -> None:
        self._current_item = None
        self._current_index = 0
        self._percentage = 0.0
        self._etr = 0.0

