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
from comfylab.devices.tektronix.mdo3040 import TektronixMDO3040


@register_block("devices/tektronix/mdo3040/connect")
class TektronixMDO3040ConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Tektronix MDO3040 / MDO3000 Series Mixed Domain Oscilloscope."""
    icon = "📺"
    display_name = "Tektronix MDO3040 Connect"
    description = "Opens a VISA session to a Tektronix MDO3040 oscilloscope / RF spectrum analyzer."

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Conectar Tektronix MDO3040",
            "description": "Abre uma sessão VISA para um osciloscópio / analisador RF Tektronix MDO3040.",
            "pins": {
                "Open": "Abrir",
                "Address": "Endereço",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Conectar Tektronix MDO3040",
            "description": "Abre una sesión VISA con un osciloscopio / analizador RF Tektronix MDO3040.",
            "pins": {
                "Open": "Abrir",
                "Address": "Dirección",
                "Out": "Salida",
                "Device": "Dispositivo"
            }
        }
    }


@register_block("devices/tektronix/mdo3040/timebase")
class TektronixMDO3040TimebaseBlock(BaseBlock):
    """Configures horizontal timebase scale (s/div) and position on a Tektronix MDO3040."""
    icon = "⏱️"
    display_name = "Tektronix MDO3040 Timebase"
    description = "Configures horizontal timebase scale and position on a Tektronix MDO3040."

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
            "display_name": "Base de Tempo Tektronix MDO3040",
            "description": "Configura a escala de tempo horizontal e posição no Tektronix MDO3040.",
            "pins": {
                "Device": "Dispositivo",
                "Scale": "Escala",
                "Position": "Posição"
            }
        },
        "es": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Base de Tiempo Tektronix MDO3040",
            "description": "Configura la escala de tiempo horizontal y posición en el Tektronix MDO3040.",
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

        drv = TektronixMDO3040(device)
        async with locked_device(context, device, "Tektronix MDO3040 Timebase"):
            await asyncio.to_thread(drv.set_timebase, scale, position)

        return "Out"


@register_block("devices/tektronix/mdo3040/channel")
class TektronixMDO3040ChannelBlock(BaseBlock):
    """Configures vertical channel parameters on a Tektronix MDO3040."""
    icon = "📶"
    display_name = "Tektronix MDO3040 Channel"
    description = "Configures vertical scale (V/div), position, offset, and coupling on a Tektronix MDO3040."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Scale", type_hint=float, default=1.0, optional=True),
        DataIn("Position", type_hint=float, default=0.0, optional=True),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Coupling", type_hint=str, default="DC", widget="dropdown", options=["DC", "AC", "GND"], optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Canal Tektronix MDO3040",
            "description": "Configura parâmetros verticais do canal no osciloscópio Tektronix MDO3040.",
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
            "display_name": "Canal Tektronix MDO3040",
            "description": "Configura parámetros verticales del canal en el osciloscopio Tektronix MDO3040.",
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

        drv = TektronixMDO3040(device)
        async with locked_device(context, device, "Tektronix MDO3040 Channel"):
            await asyncio.to_thread(drv.set_channel, int(channel), enable, scale, position, offset, coupling)

        return "Out"


@register_block("devices/tektronix/mdo3040/trigger")
class TektronixMDO3040TriggerBlock(BaseBlock):
    """Configures edge trigger parameters on a Tektronix MDO3040."""
    icon = "⚡"
    display_name = "Tektronix MDO3040 Trigger"
    description = "Configures trigger source, voltage level, slope, and mode on a Tektronix MDO3040."

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
            "display_name": "Gatilho Tektronix MDO3040",
            "description": "Configura a fonte, nível de disparo, borda e modo de disparo no Tektronix MDO3040.",
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
            "display_name": "Disparo Tektronix MDO3040",
            "description": "Configura la fuente, nivel de disparo, flanco y modo de disparo en el Tektronix MDO3040.",
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

        drv = TektronixMDO3040(device)
        async with locked_device(context, device, "Tektronix MDO3040 Trigger"):
            await asyncio.to_thread(drv.set_trigger, source, level, slope, mode)

        return "Out"


@register_block("devices/tektronix/mdo3040/acquire")
class TektronixMDO3040AcquireBlock(BaseBlock):
    """Pulls waveform arrays from a Tektronix MDO3040 oscilloscope channel."""
    icon = "📥"
    display_name = "Tektronix MDO3040 Acquire"
    description = "Triggers waveform acquisition from Tektronix MDO3040, outputs arrays, and broadcasts telemetry."

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
            "display_name": "Adquirir Tektronix MDO3040",
            "description": "Aciona a aquisição de forma de onda do Tektronix MDO3040, gera arrays e transmite telemetria.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Waveform": "Forma de Onda",
                "Time": "Tempo"
            }
        },
        "es": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Adquirir Tektronix MDO3040",
            "description": "Activa la adquisición de forma de onda del Tektronix MDO3040, genera arrays y transmite telemetría.",
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

        drv = TektronixMDO3040(device)
        async with locked_device(context, device, "Tektronix MDO3040 Acquire"):
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


@register_block("devices/tektronix/mdo3040/measure")
class TektronixMDO3040MeasureBlock(BaseBlock):
    """Measures scalar parameters (Vpp, Frequency, RMS, Mean, Max, Min, Period) on a Tektronix MDO3040."""
    icon = "🔢"
    display_name = "Tektronix MDO3040 Measure"
    description = "Queries real-time automated measurement on a Tektronix MDO3040 channel."

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
            "display_name": "Medição Tektronix MDO3040",
            "description": "Consulta medições automáticas em tempo real no canal do Tektronix MDO3040.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Measurement": "Medição",
                "Value": "Valor"
            }
        },
        "es": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Medición Tektronix MDO3040",
            "description": "Consulta mediciones automáticas en tiempo real en el canal del Tektronix MDO3040.",
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

        drv = TektronixMDO3040(device)
        async with locked_device(context, device, "Tektronix MDO3040 Measure"):
            self._last_val = await asyncio.to_thread(drv.measure, int(channel), str(measurement))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Value":
            return self._last_val
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("devices/tektronix/mdo3040/rf_acquire")
class TektronixMDO3040RFAcquireBlock(BaseBlock):
    """Pulls RF spectrum analyzer trace arrays (Frequency in Hz, Power in dBm) from a Tektronix MDO3040."""
    icon = "📡"
    display_name = "Tektronix MDO3040 RF Spectrum"
    description = "Acquires RF Spectrum Analyzer trace (Frequency Hz and Power dBm) on a Tektronix MDO3040."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("CenterFreq", type_hint=float, default=1e9, optional=True),
        DataIn("Span", type_hint=float, default=1e7, optional=True),
        DataIn("RefLevel", type_hint=float, default=0.0, optional=True),
        DataIn("TraceType", type_hint=str, default="NORMAL", widget="dropdown", options=["NORMAL", "AVERAGE", "MAXHOLD", "MINHOLD"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Power_dBm", type_hint=np.ndarray),
        DataOut("Frequency", type_hint=np.ndarray),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Espectro RF Tektronix MDO3040",
            "description": "Adquire traço do Analisador de Espectro RF (Frequência Hz e Potência dBm) no Tektronix MDO3040.",
            "pins": {
                "Device": "Dispositivo",
                "CenterFreq": "Freq Central",
                "Span": "Span",
                "RefLevel": "Nível Ref",
                "TraceType": "Tipo Traço",
                "Power_dBm": "Potência (dBm)",
                "Frequency": "Frequência"
            }
        },
        "es": {
            "category": "Instrumentos/Tektronix",
            "display_name": "Espectro RF Tektronix MDO3040",
            "description": "Adquiere traza del Analizador de Espectro RF (Frecuencia Hz y Potencia dBm) en el Tektronix MDO3040.",
            "pins": {
                "Device": "Dispositivo",
                "CenterFreq": "Freq Central",
                "Span": "Span",
                "RefLevel": "Nivel Ref",
                "TraceType": "Tipo Traza",
                "Power_dBm": "Potencia (dBm)",
                "Frequency": "Frecuencia"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._power: np.ndarray = np.array([])
        self._freq: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        center_f = await context.pull(self.id, "CenterFreq")
        span_f = await context.pull(self.id, "Span")
        ref_lvl = await context.pull(self.id, "RefLevel")
        trace_type = await context.pull(self.id, "TraceType")

        drv = TektronixMDO3040(device)
        async with locked_device(context, device, "Tektronix MDO3040 RF Spectrum"):
            await asyncio.to_thread(drv.set_rf, True, center_f, span_f, ref_lvl)
            f_vec, p_vec = await asyncio.to_thread(drv.acquire_rf_trace, str(trace_type))
            self._freq = f_vec
            self._power = p_vec

            # Broadcast plot telemetry
            if len(self._power) > 0:
                floats = self._power.tolist()
                point_count = len(floats)
                encoded_id = self.id.encode('utf-8')[:36].ljust(36, b'\x00')
                binary_packet = struct.pack(f"<36sI{point_count}f", encoded_id, point_count, *floats)
                await context.send_telemetry(self.id, binary_packet)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Power_dBm":
            return self._power
        elif pin_name == "Frequency":
            return self._freq
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
