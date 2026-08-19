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
from comfylab.devices.tektronix.mso24 import TektronixMSO24


@register_block("devices/tektronix/mso24/connect")
class TektronixMSO24ConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Tektronix 2 Series MSO (MSO24 200 MHz) oscilloscope."""
    icon = "📺"
    display_name = "Tektronix MSO24 Connect"
    description = "Opens a VISA session to a Tektronix 2 Series MSO oscilloscope (e.g. MSO24 200 MHz)."

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Conectar Tektronix MSO24",
            "description": "Abre uma sessão VISA para um osciloscópio Tektronix 2 Series MSO (MSO24 200 MHz).",
            "pins": {
                "Open": "Abrir",
                "Address": "Endereço",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Conectar Tektronix MSO24",
            "description": "Abre una sesión VISA con un osciloscopio Tektronix 2 Series MSO (MSO24 200 MHz).",
            "pins": {
                "Open": "Abrir",
                "Address": "Dirección",
                "Out": "Salida",
                "Device": "Dispositivo"
            }
        }
    }


@register_block("devices/tektronix/mso24/timebase")
class TektronixMSO24TimebaseBlock(BaseBlock):
    """Configures horizontal timebase scale (s/div) and position on a Tektronix MSO24."""
    icon = "⏱️"
    display_name = "Tektronix MSO24 Timebase"
    description = "Configures horizontal timebase scale and position on a Tektronix MSO24 oscilloscope."

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
            "category": "Instrumentos/Tektronix",
            "display_name": "Base de Tempo Tektronix MSO24",
            "description": "Configura a escala de tempo horizontal e posição no osciloscópio Tektronix MSO24.",
            "pins": {
                "Device": "Dispositivo",
                "Scale": "Escala",
                "Position": "Posição"
            }
        },
        "es": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Base de Tiempo Tektronix MSO24",
            "description": "Configura la escala de tiempo horizontal y posición en el osciloscopio Tektronix MSO24.",
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

        drv = TektronixMSO24(device)
        async with locked_device(context, device, "Tektronix MSO24 Timebase"):
            await asyncio.to_thread(drv.set_timebase, scale, position)

        return "Out"


@register_block("devices/tektronix/mso24/channel")
class TektronixMSO24ChannelBlock(BaseBlock):
    """Configures vertical channel scale (V/div), position, offset, and coupling on a Tektronix MSO24."""
    icon = "📶"
    display_name = "Tektronix MSO24 Channel"
    description = "Configures vertical channel parameters on a Tektronix MSO24 oscilloscope."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Scale", type_hint=float, default=1.0, optional=True),
        DataIn("Position", type_hint=float, default=0.0, optional=True),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Coupling", type_hint=str, default="DC", widget="dropdown", options=["DC", "AC", "DCREJ"], optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Canal Tektronix MSO24",
            "description": "Configura os parâmetros verticais do canal no osciloscópio Tektronix MSO24.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Enable": "Habilitar",
                "Scale": "Escala",
                "Position": "Posição",
                "Offset": "Offset",
                "Coupling": "Acoplamento"
            }
        },
        "es": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Canal Tektronix MSO24",
            "description": "Configura los parámetros verticales del canal en el osciloscopio Tektronix MSO24.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Enable": "Habilitar",
                "Scale": "Escala",
                "Position": "Posición",
                "Offset": "Offset",
                "Coupling": "Acoplamiento"
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
        position = await context.pull(self.id, "Position")
        offset = await context.pull(self.id, "Offset")
        coupling = await context.pull(self.id, "Coupling")

        drv = TektronixMSO24(device)
        async with locked_device(context, device, "Tektronix MSO24 Channel"):
            await asyncio.to_thread(drv.set_channel, int(channel), enable, scale, position, offset, coupling)

        return "Out"


@register_block("devices/tektronix/mso24/trigger")
class TektronixMSO24TriggerBlock(BaseBlock):
    """Configures edge trigger parameters on a Tektronix MSO24."""
    icon = "⚡"
    display_name = "Tektronix MSO24 Trigger"
    description = "Configures trigger source, level (V), slope, and mode on a Tektronix MSO24."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Source", type_hint=str, default="CH1", widget="dropdown", options=["CH1", "CH2", "CH3", "CH4", "EXT", "LINE"]),
        DataIn("Level", type_hint=float, default=0.0),
        DataIn("Slope", type_hint=str, default="RISE", widget="dropdown", options=["RISE", "FALL"]),
        DataIn("Mode", type_hint=str, default="AUTO", widget="dropdown", options=["AUTO", "NORMAL"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Gatilho Tektronix MSO24",
            "description": "Configura a fonte, nível de tensão, borda e modo de disparo no Tektronix MSO24.",
            "pins": {
                "Device": "Dispositivo",
                "Source": "Fonte",
                "Level": "Nível",
                "Slope": "Borda",
                "Mode": "Modo"
            }
        },
        "es": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Disparo Tektronix MSO24",
            "description": "Configura la fuente, nivel de voltaje, flanco y modo de disparo en el Tektronix MSO24.",
            "pins": {
                "Device": "Dispositivo",
                "Source": "Fuente",
                "Level": "Nivel",
                "Slope": "Flanco",
                "Mode": "Modo"
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
        mode = await context.pull(self.id, "Mode")

        drv = TektronixMSO24(device)
        async with locked_device(context, device, "Tektronix MSO24 Trigger"):
            await asyncio.to_thread(drv.set_trigger, source, level, slope, mode)

        return "Out"


@register_block("devices/tektronix/mso24/acquire")
class TektronixMSO24AcquireBlock(BaseBlock):
    """Pulls waveform arrays from a Tektronix MSO24 oscilloscope."""
    icon = "📥"
    display_name = "Tektronix MSO24 Acquire"
    description = "Triggers waveform acquisition from a Tektronix MSO24, outputs arrays, and broadcasts telemetry."

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
            "category": "Instrumentos/Tektronix",
            "display_name": "Adquirir Tektronix MSO24",
            "description": "Aciona a aquisição de forma de onda do Tektronix MSO24, gera arrays e transmite telemetria.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Waveform": "Forma de Onda",
                "Time": "Tempo"
            }
        },
        "es": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Adquirir Tektronix MSO24",
            "description": "Activa la adquisición de forma de onda del Tektronix MSO24, genera arrays y transmite telemetría.",
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

        drv = TektronixMSO24(device)
        async with locked_device(context, device, "Tektronix MSO24 Acquire"):
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


@register_block("devices/tektronix/mso24/measure")
class TektronixMSO24MeasureBlock(BaseBlock):
    """Measures scalar parameters (Vpp, Frequency, RMS, Mean, Max, Min) on a Tektronix MSO24."""
    icon = "🔢"
    display_name = "Tektronix MSO24 Measure"
    description = "Queries real-time automated measurement on a Tektronix MSO24 channel."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Measurement", type_hint=str, default="PK2PK", widget="dropdown", options=["PK2PK", "FREQ", "RMS", "CRMS", "MEAN", "MAX", "MIN", "PERIOD"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Value", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Medição Tektronix MSO24",
            "description": "Consulta medições automáticas em tempo real no canal do Tektronix MSO24.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Measurement": "Medição",
                "Value": "Valor"
            }
        },
        "es": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Medición Tektronix MSO24",
            "description": "Consulta mediciones automáticas en tiempo real en el canal del Tektronix MSO24.",
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

        drv = TektronixMSO24(device)
        async with locked_device(context, device, "Tektronix MSO24 Measure"):
            self._last_val = await asyncio.to_thread(drv.measure, int(channel), str(measurement))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return self._last_val
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
