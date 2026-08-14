# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
from typing import Any, Dict, Optional

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.blocks.devices.base import BaseDeviceConnectBlock, locked_device
from comfylab.devices.generic.dmm import GenericDMM


@register_block("devices/generic/dmm/connect")
class GenericDMMConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a SCPI Digital Multimeter (DMM)."""
    icon = "🎛️"
    display_name = "Generic DMM Connect"
    description = "Opens a VISA session to a SCPI Digital Multimeter (DMM)."
    i18n = {
        "pt-BR": {
            "category": "Dispositivos/Genérico/Multímetro",
            "display_name": "Conexão Genérica DMM",
            "description": "Abre uma sessão VISA para um Multímetro Digital (DMM) SCPI."
        },
        "es": {
            "category": "Dispositivos/Genérico/Multímetro",
            "display_name": "Conexión Genérica DMM",
            "description": "Abre una sesión VISA para un Multímetro Digital (DMM) SCPI."
        }
    }


@register_block("devices/generic/dmm/measure")
class GenericDMMMeasureBlock(BaseBlock):
    """Configures measurement mode and triggers a reading on a SCPI Digital Multimeter (DMM)."""
    icon = "🔢"
    display_name = "Generic DMM Measure"
    description = "Configures mode (VOLT:DC, CURR:DC, RES, etc.) and triggers reading on a SCPI DMM."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Mode", type_hint=str, default="VOLT:DC", widget="dropdown", options=["VOLT:DC", "VOLT:AC", "CURR:DC", "CURR:AC", "RES", "FRES"]),
        DataIn("Range", type_hint=float, optional=True),
        DataIn("NPLC", type_hint=float, default=1.0, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Value", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]
    i18n = {
        "pt-BR": {
            "category": "Dispositivos/Genérico/Multímetro",
            "display_name": "Medição Genérica DMM",
            "description": "Configura o modo (VOLT:DC, CURR:DC, RES, etc.) e aciona a leitura em um DMM SCPI.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Mode": "Modo",
                "Range": "Faixa",
                "Out": "Saída",
                "Value": "Valor"
            }
        },
        "es": {
            "category": "Dispositivos/Genérico/Multímetro",
            "display_name": "Medición Genérica DMM",
            "description": "Configura el modo (VOLT:DC, CURR:DC, RES, etc.) y activa la lectura en un DMM SCPI.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Mode": "Modo",
                "Range": "Rango",
                "Out": "Salida",
                "Value": "Valor"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_val: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        mode = await context.pull(self.id, "Mode")
        rng = await context.pull(self.id, "Range")
        nplc = await context.pull(self.id, "NPLC")

        drv = GenericDMM(device)
        async with locked_device(context, device, "Generic DMM Measure"):
            await asyncio.to_thread(drv.configure, mode, rng, None, nplc)
            self._last_val = await asyncio.to_thread(drv.read_measurement)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return self._last_val
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
