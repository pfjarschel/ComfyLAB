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
from comfylab.devices.keysight.dsox1204a import KeysightDSOX1204A


@register_block("devices/keysight/dsox1204a/connect")
class KeysightDSOX1204AConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Keysight InfiniiVision DSOX 1204A (1000 X-Series) oscilloscope."""
    icon = "📺"
    display_name = "Keysight DSOX 1204A Connect"
    description = "Opens a VISA session to a Keysight InfiniiVision DSOX 1204A 4-channel oscilloscope."

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Conectar Keysight DSOX 1204A",
            "description": "Abre uma sessão VISA para um osciloscópio Keysight InfiniiVision DSOX 1204A de 4 canais.",
            "pins": {
                "Open": "Abrir",
                "Address": "Endereço",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Conectar Keysight DSOX 1204A",
            "description": "Abre una sesión VISA a un osciloscopio Keysight InfiniiVision DSOX 1204A de 4 canales.",
            "pins": {
                "Open": "Abrir",
                "Address": "Dirección",
                "Out": "Salida",
                "Device": "Dispositivo"
            }
        }
    }


@register_block("devices/keysight/dsox1204a/timebase")
class KeysightDSOX1204ATimebaseBlock(BaseBlock):
    """Configures horizontal timebase scale (s/div) and position on a Keysight DSOX 1204A."""
    icon = "⏱️"
    display_name = "Keysight DSOX 1204A Timebase"
    description = "Configures horizontal timebase scale and position on a Keysight DSOX 1204A oscilloscope."

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
            "display_name": "Base de Tempo Keysight DSOX 1204A",
            "description": "Configura a escala de tempo e posição no osciloscópio Keysight DSOX 1204A.",
            "pins": {
                "Device": "Dispositivo",
                "Scale": "Escala",
                "Position": "Posição"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Base de Tiempo Keysight DSOX 1204A",
            "description": "Configura la escala de tiempo y posición en el osciloscopio Keysight DSOX 1204A.",
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

        drv = KeysightDSOX1204A(device)
        async with locked_device(context, device, "Keysight DSOX 1204A Timebase"):
            await asyncio.to_thread(drv.set_timebase, scale, position)

        return "Out"


@register_block("devices/keysight/dsox1204a/channel")
class KeysightDSOX1204AChannelBlock(BaseBlock):
    """Configures vertical channel parameters on a Keysight DSOX 1204A."""
    icon = "📶"
    display_name = "Keysight DSOX 1204A Channel"
    description = "Configures vertical channel scale (V/div), offset (V), coupling, and probe ratio."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Scale", type_hint=float, default=1.0, optional=True),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Coupling", type_hint=str, default="DC", widget="dropdown", options=["DC", "AC", "GND"], optional=True),
        DataIn("Probe", type_hint=float, default=10.0, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Canal Keysight DSOX 1204A",
            "description": "Configura os parâmetros verticais do canal no osciloscópio Keysight DSOX 1204A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Enable": "Habilitar",
                "Scale": "Escala",
                "Offset": "Offset",
                "Coupling": "Acoplamento",
                "Probe": "Ponta"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Canal Keysight DSOX 1204A",
            "description": "Configura los parámetros verticales del canal en el osciloscopio Keysight DSOX 1204A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Enable": "Habilitar",
                "Scale": "Escala",
                "Offset": "Offset",
                "Coupling": "Acoplamiento",
                "Probe": "Sonda"
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
        probe = await context.pull(self.id, "Probe")

        drv = KeysightDSOX1204A(device)
        async with locked_device(context, device, "Keysight DSOX 1204A Channel"):
            await asyncio.to_thread(drv.set_channel, int(channel), enable, scale, offset, coupling, probe)

        return "Out"


@register_block("devices/keysight/dsox1204a/trigger")
class KeysightDSOX1204ATriggerBlock(BaseBlock):
    """Configures edge trigger parameters on a Keysight DSOX 1204A."""
    icon = "⚡"
    display_name = "Keysight DSOX 1204A Trigger"
    description = "Configures trigger source, voltage level, slope, and sweep mode on Keysight DSOX 1204A."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Source", type_hint=str, default="CHAN1", widget="dropdown", options=["CHAN1", "CHAN2", "CHAN3", "CHAN4", "EXT", "LINE", "WGEN"]),
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
            "display_name": "Gatilho Keysight DSOX 1204A",
            "description": "Configura a fonte, nível de disparo, borda e modo de varredura no Keysight DSOX 1204A.",
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
            "display_name": "Disparo Keysight DSOX 1204A",
            "description": "Configura la fuente, nivel de disparo, flanco y modo en el Keysight DSOX 1204A.",
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

        drv = KeysightDSOX1204A(device)
        async with locked_device(context, device, "Keysight DSOX 1204A Trigger"):
            await asyncio.to_thread(drv.set_trigger, source, level, slope, sweep)

        return "Out"


@register_block("devices/keysight/dsox1204a/acquire")
class KeysightDSOX1204AAcquireBlock(BaseBlock):
    """Pulls waveform arrays from a Keysight DSOX 1204A oscilloscope."""
    icon = "📥"
    display_name = "Keysight DSOX 1204A Acquire"
    description = "Triggers waveform acquisition from Keysight DSOX 1204A, outputs arrays, and broadcasts telemetry."

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
            "display_name": "Adquirir Keysight DSOX 1204A",
            "description": "Aciona a aquisição de forma de onda do Keysight DSOX 1204A, gera arrays e transmite telemetria.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Waveform": "Forma de Onda",
                "Time": "Tempo"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Adquirir Keysight DSOX 1204A",
            "description": "Activa la adquisición de forma de onda del Keysight DSOX 1204A, genera arrays y transmite telemetría.",
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

        drv = KeysightDSOX1204A(device)
        async with locked_device(context, device, "Keysight DSOX 1204A Acquire"):
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


@register_block("devices/keysight/dsox1204a/measure")
class KeysightDSOX1204AMeasureBlock(BaseBlock):
    """Measures scalar parameters on a Keysight DSOX 1204A."""
    icon = "🔢"
    display_name = "Keysight DSOX 1204A Measure"
    description = "Queries real-time automated measurement on a Keysight DSOX 1204A channel."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Measurement", type_hint=str, default="VPP", widget="dropdown", options=["VPP", "FREQ", "RMS", "AVERAGE", "MAX", "MIN", "PERIOD"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Value", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Medição Keysight DSOX 1204A",
            "description": "Consulta medições automáticas em tempo real no canal do Keysight DSOX 1204A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Measurement": "Medição",
                "Value": "Valor"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Medición Keysight DSOX 1204A",
            "description": "Consulta mediciones automáticas en tiempo real en el canal del Keysight DSOX 1204A.",
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

        drv = KeysightDSOX1204A(device)
        async with locked_device(context, device, "Keysight DSOX 1204A Measure"):
            self._last_val = await asyncio.to_thread(drv.measure, int(channel), str(measurement))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return self._last_val
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("devices/keysight/dsox1204a/wavegen")
class KeysightDSOX1204AWaveGenBlock(BaseBlock):
    """Controls the built-in 20 MHz WaveGen Function Generator on a Keysight DSOX 1204A."""
    icon = "〰️"
    display_name = "Keysight DSOX 1204A WaveGen"
    description = "Configures built-in WaveGen function generator (Sine, Square, Ramp, Pulse, Noise, DC)."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Shape", type_hint=str, default="SIN", widget="dropdown", options=["SIN", "SQU", "RAMP", "PULS", "NOIS", "DC"]),
        DataIn("Frequency", type_hint=float, default=1000.0),
        DataIn("Amplitude", type_hint=float, default=1.0),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight DSOX 1204A WaveGen",
            "description": "Configura o gerador de funções WaveGen integrado no Keysight DSOX 1204A.",
            "pins": {
                "Device": "Dispositivo",
                "Shape": "Forma",
                "Frequency": "Frequência",
                "Amplitude": "Amplitude",
                "Offset": "Offset",
                "Enable": "Habilitar"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight DSOX 1204A WaveGen",
            "description": "Configura el generador de funciones WaveGen integrado en el Keysight DSOX 1204A.",
            "pins": {
                "Device": "Dispositivo",
                "Shape": "Forma",
                "Frequency": "Frecuencia",
                "Amplitude": "Amplitud",
                "Offset": "Offset",
                "Enable": "Habilitar"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        shape = await context.pull(self.id, "Shape")
        frequency = await context.pull(self.id, "Frequency")
        amplitude = await context.pull(self.id, "Amplitude")
        offset = await context.pull(self.id, "Offset")
        enable = await context.pull(self.id, "Enable")

        drv = KeysightDSOX1204A(device)
        async with locked_device(context, device, "Keysight DSOX 1204A WaveGen"):
            await asyncio.to_thread(drv.set_wavegen, shape, frequency, amplitude, offset, bool(enable))

        return "Out"
