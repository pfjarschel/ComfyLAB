# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
import struct
from typing import Any, Dict, Optional
import numpy as np

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.blocks.devices.base import BaseDeviceConnectBlock, locked_device
from comfylab.devices.keysight.dsox3024a import KeysightDSOX3024A


@register_block("devices/keysight/dsox3024a/connect")
class KeysightDSOX3024AConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Keysight InfiniiVision DSOX 3024A (3000 X-Series) oscilloscope."""
    icon = "📺"
    display_name = "Keysight DSOX 3024A Connect"
    description = "Opens a VISA session to a Keysight InfiniiVision DSOX 3024A 4-channel oscilloscope."

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Conectar Keysight DSOX 3024A",
            "description": "Abre uma sessão VISA para um osciloscópio Keysight InfiniiVision DSOX 3024A de 4 canais.",
            "pins": {
                "Open": "Abrir",
                "Address": "Endereço",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Conectar Keysight DSOX 3024A",
            "description": "Abre una sesión VISA a un osciloscopio Keysight InfiniiVision DSOX 3024A de 4 canales.",
            "pins": {
                "Open": "Abrir",
                "Address": "Dirección",
                "Out": "Salida",
                "Device": "Dispositivo"
            }
        }
    }


@register_block("devices/keysight/dsox3024a/timebase")
class KeysightDSOX3024ATimebaseBlock(BaseBlock):
    """Configures horizontal timebase scale (s/div) and position on a Keysight DSOX 3024A."""
    icon = "⏱️"
    display_name = "Keysight DSOX 3024A Timebase"
    description = "Configures horizontal timebase scale and position on a Keysight DSOX 3024A oscilloscope."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Scale", type_hint=float, default=0.001),
        DataIn("Position", type_hint=float, default=0.0, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Base de Tempo Keysight DSOX 3024A",
            "description": "Configura a escala de tempo e posição no osciloscópio Keysight DSOX 3024A.",
            "pins": {
                "Device": "Dispositivo",
                "Scale": "Escala",
                "Position": "Posição"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Base de Tiempo Keysight DSOX 3024A",
            "description": "Configura la escala de tiempo y posición en el osciloscopio Keysight DSOX 3024A.",
            "pins": {
                "Device": "Dispositivo",
                "Scale": "Escala",
                "Position": "Posición"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        scale = await context.pull(self.id, "Scale")
        position = await context.pull(self.id, "Position")

        drv = KeysightDSOX3024A(device)
        async with locked_device(context, device, "Keysight DSOX 3024A Timebase"):
            await asyncio.to_thread(drv.set_timebase, scale, position)

        return "Out"


@register_block("devices/keysight/dsox3024a/channel")
class KeysightDSOX3024AChannelBlock(BaseBlock):
    """Configures vertical channel parameters on a Keysight DSOX 3024A."""
    icon = "📶"
    display_name = "Keysight DSOX 3024A Channel"
    description = "Configures vertical channel scale (V/div), offset (V), coupling, and bandwidth limit."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Scale", type_hint=float, default=1.0, optional=True),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Coupling", type_hint=str, default="DC", widget="dropdown", options=["DC", "AC", "GND"], optional=True),
        DataIn("BWLimit", type_hint=bool, default=False, widget="checkbox", optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Canal Keysight DSOX 3024A",
            "description": "Configura os parâmetros verticais do canal no osciloscópio Keysight DSOX 3024A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Enable": "Habilitar",
                "Scale": "Escala",
                "Offset": "Offset",
                "Coupling": "Acoplamento",
                "BWLimit": "Filtro 20MHz"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Canal Keysight DSOX 3024A",
            "description": "Configura los parámetros verticales del canal en el osciloscopio Keysight DSOX 3024A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Enable": "Habilitar",
                "Scale": "Escala",
                "Offset": "Offset",
                "Coupling": "Acoplamiento",
                "BWLimit": "Filtro 20MHz"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        channel = await context.pull(self.id, "Channel")
        enable = await context.pull(self.id, "Enable")
        scale = await context.pull(self.id, "Scale")
        offset = await context.pull(self.id, "Offset")
        coupling = await context.pull(self.id, "Coupling")
        bw_limit = await context.pull(self.id, "BWLimit")

        drv = KeysightDSOX3024A(device)
        async with locked_device(context, device, "Keysight DSOX 3024A Channel"):
            await asyncio.to_thread(drv.set_channel, int(channel), enable, scale, offset, coupling, bw_limit)

        return "Out"


@register_block("devices/keysight/dsox3024a/trigger")
class KeysightDSOX3024ATriggerBlock(BaseBlock):
    """Configures edge trigger parameters on a Keysight DSOX 3024A."""
    icon = "⚡"
    display_name = "Keysight DSOX 3024A Trigger"
    description = "Configures trigger source, voltage level, slope, and sweep mode on Keysight DSOX 3024A."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Source", type_hint=str, default="CHAN1", widget="dropdown", options=["CHAN1", "CHAN2", "CHAN3", "CHAN4", "EXT", "LINE"]),
        DataIn("Level", type_hint=float, default=0.0),
        DataIn("Slope", type_hint=str, default="POS", widget="dropdown", options=["POS", "NEG"]),
        DataIn("Sweep", type_hint=str, default="AUTO", widget="dropdown", options=["AUTO", "NORMAL"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Gatilho Keysight DSOX 3024A",
            "description": "Configura a fonte, nível de disparo, borda e modo de varredura no Keysight DSOX 3024A.",
            "pins": {
                "Device": "Dispositivo",
                "Source": "Fonte",
                "Level": "Nível",
                "Slope": "Borda",
                "Sweep": "Modo"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Disparo Keysight DSOX 3024A",
            "description": "Configura la fuente, nivel de disparo, flanco y modo en el Keysight DSOX 3024A.",
            "pins": {
                "Device": "Dispositivo",
                "Source": "Fuente",
                "Level": "Nivel",
                "Slope": "Flanco",
                "Sweep": "Modo"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        source = await context.pull(self.id, "Source")
        level = await context.pull(self.id, "Level")
        slope = await context.pull(self.id, "Slope")
        sweep = await context.pull(self.id, "Sweep")

        drv = KeysightDSOX3024A(device)
        async with locked_device(context, device, "Keysight DSOX 3024A Trigger"):
            await asyncio.to_thread(drv.set_trigger, source, level, slope, sweep)

        return "Out"


@register_block("devices/keysight/dsox3024a/acquire")
class KeysightDSOX3024AAcquireBlock(BaseBlock):
    """Pulls waveform arrays from a Keysight DSOX 3024A oscilloscope."""
    icon = "📥"
    display_name = "Keysight DSOX 3024A Acquire"
    description = "Triggers waveform acquisition from Keysight DSOX 3024A, outputs arrays, and broadcasts telemetry."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Waveform", type_hint=np.ndarray),
        DataOut("Time", type_hint=np.ndarray),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Adquirir Keysight DSOX 3024A",
            "description": "Aciona a aquisição de forma de onda do Keysight DSOX 3024A, gera arrays e transmite telemetria.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Waveform": "Forma de Onda",
                "Time": "Tempo"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Adquirir Keysight DSOX 3024A",
            "description": "Activa la adquisición de forma de onda del Keysight DSOX 3024A, genera arrays y transmite telemetría.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Waveform": "Forma de Onda",
                "Time": "Tiempo"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_waveform: np.ndarray = np.array([])
        self._last_time: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        channel = await context.pull(self.id, "Channel")

        drv = KeysightDSOX3024A(device)
        async with locked_device(context, device, "Keysight DSOX 3024A Acquire"):
            t_vec, v_vec = await asyncio.to_thread(drv.acquire_waveform, int(channel))
            self._last_time = t_vec
            self._last_waveform = v_vec

            # Broadcast plot telemetry
            if len(self._last_waveform) > 0:
                floats = self._last_waveform.tolist()
                point_count = len(floats)
                encoded_id = self.id.encode('utf-8')[:36].ljust(36, b'\x00')
                binary_packet = struct.pack(f"<36sI{point_count}f", encoded_id, point_count, *floats)
                await context.send_telemetry(self.id, binary_packet)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Waveform":
            return self._last_waveform
        elif pin_name == "Time":
            return self._last_time
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("devices/keysight/dsox3024a/measure")
class KeysightDSOX3024AMeasureBlock(BaseBlock):
    """Measures scalar parameters (Vpp, Frequency, RMS, Average, Max, Min, Period, Duty) on Keysight DSOX 3024A."""
    icon = "🔢"
    display_name = "Keysight DSOX 3024A Measure"
    description = "Queries real-time automated measurement on a Keysight DSOX 3024A channel."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Measurement", type_hint=str, default="VPP", widget="dropdown", options=["VPP", "FREQ", "RMS", "AVERAGE", "MAX", "MIN", "PERIOD", "DUTY"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Value", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Medição Keysight DSOX 3024A",
            "description": "Consulta medições automáticas em tempo real no canal do Keysight DSOX 3024A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Measurement": "Medição",
                "Value": "Valor"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Medición Keysight DSOX 3024A",
            "description": "Consulta mediciones automáticas en tiempo real en el canal del Keysight DSOX 3024A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Measurement": "Medición",
                "Value": "Valor"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_val: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        channel = await context.pull(self.id, "Channel")
        measurement = await context.pull(self.id, "Measurement")

        drv = KeysightDSOX3024A(device)
        async with locked_device(context, device, "Keysight DSOX 3024A Measure"):
            self._last_val = await asyncio.to_thread(drv.measure, int(channel), str(measurement))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return self._last_val
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
