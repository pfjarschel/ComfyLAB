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
from comfylab.virtual.manager import VirtualInstrumentManager


@register_block("devices/virtual/oscilloscope/connect")
class VirtOscConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a VirtOsc device with safety teardown (stop acquisition)."""
    icon = "📺"
    display_name = "VirtOsc Connect"
    description = "Opens a VISA connection to a VirtOsc oscilloscope. On teardown, stops acquisition."
    inputs_def = [
        ExecIn("Open"),
        DataIn("Address", type_hint=str, default="TCPIP0::127.0.0.1::51234::SOCKET", widget="text"),
        DataIn("ReadTermination", type_hint=str, default="\n", optional=True),
        DataIn("WriteTermination", type_hint=str, default="\n", optional=True),
        DataIn("Timeout", type_hint=float, default=2.0, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]
    i18n = {
        "pt-BR": {
            "category": "Dispositivos/Virtual/Osciloscópio",
            "display_name": "Conexão VirtOsc",
            "description": "Abre uma conexão VISA para um osciloscópio VirtOsc. Na desconexão, para a aquisição.",
            "pins": {
                "Open": "Abrir",
                "Address": "Endereço",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "category": "Dispositivos/Virtual/Osciloscopio",
            "display_name": "Conexión VirtOsc",
            "description": "Abre una conexión VISA a un osciloscopio VirtOsc. Al desconectar, detiene la adquisición.",
            "pins": {
                "Open": "Abrir",
                "Address": "Dirección",
                "Out": "Salida",
                "Device": "Dispositivo"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        address = await context.pull(self.id, "Address")
        # Ensure virtual background process is started if virtual instrument address is used
        if address and ("51234" in str(address) or "VIRT" in str(address).upper() or "127.0.0.1" in str(address)):
            await asyncio.to_thread(VirtualInstrumentManager.ensure_started)
            VirtualInstrumentManager.register_client(self.id)

        res = await super().execute(context, trigger_pin)
        return res

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(device.write, ":STOP")
        else:
            await asyncio.to_thread(device.write, ":STOP")

    async def teardown(self) -> None:
        try:
            await super().teardown()
        finally:
            VirtualInstrumentManager.unregister_client(self.id)


@register_block("devices/virtual/oscilloscope/timebase")
class VirtOscTimebaseBlock(BaseBlock):
    """Configures horizontal acquisition parameters (scale, offset, length) on a VirtOsc device."""
    icon = "⏱️"
    display_name = "VirtOsc Timebase"
    description = "Configures horizontal timebase scale, offset, and points size on a VirtOsc device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Scale", type_hint=float, default=0.001),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Points", type_hint=int, default=1000, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]
    i18n = {
        "pt-BR": {
            "category": "Dispositivos/Virtual/Osciloscópio",
            "display_name": "Base de Tempo VirtOsc",
            "description": "Configura a escala da base de tempo horizontal, offset e tamanho de pontos em um dispositivo VirtOsc.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Scale": "Escala",
                "Offset": "Offset",
                "Points": "Pontos",
                "Out": "Saída"
            }
        },
        "es": {
            "category": "Dispositivos/Virtual/Osciloscopio",
            "display_name": "Base de Tiempo VirtOsc",
            "description": "Configura la escala de la base de tiempo horizontal, offset y tamaño de puntos en un dispositivo VirtOsc.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Scale": "Escala",
                "Offset": "Offset",
                "Points": "Puntos",
                "Out": "Salida"
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
        offset = await context.pull(self.id, "Offset")
        points = await context.pull(self.id, "Points")

        async with locked_device(context, device, "VirtOsc Timebase"):
            if scale is not None:
                await asyncio.to_thread(device.write, f":TIMebase:SCALe {scale}")
            if offset is not None:
                await asyncio.to_thread(device.write, f":TIMebase:POSition {offset}")
            if points is not None:
                await asyncio.to_thread(device.write, f":ACQuire:POINts {int(points)}")

        return "Out"


@register_block("devices/virtual/oscilloscope/channel")
class VirtOscChannelBlock(BaseBlock):
    """Configures input channel scale, offset, and enable state on a VirtOsc device."""
    icon = "📶"
    display_name = "VirtOsc Channel"
    description = "Configures a specific input channel vertical parameters (scale, offset, active state) on a VirtOsc device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3, 4]),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Scale", type_hint=float, default=1.0, optional=True),
        DataIn("Offset", type_hint=float, default=0.0, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]
    i18n = {
        "pt-BR": {
            "category": "Dispositivos/Virtual/Osciloscópio",
            "display_name": "Canal VirtOsc",
            "description": "Configura parâmetros verticais (escala, offset, estado ativo) de um canal de entrada específico em um dispositivo VirtOsc.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Enable": "Habilitar",
                "Scale": "Escala",
                "Offset": "Offset",
                "Out": "Saída"
            }
        },
        "es": {
            "category": "Dispositivos/Virtual/Osciloscopio",
            "display_name": "Canal VirtOsc",
            "description": "Configura parámetros verticales (escala, offset, estado activo) de un canal de entrada específico en un dispositivo VirtOsc.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Enable": "Habilitar",
                "Scale": "Escala",
                "Offset": "Offset",
                "Out": "Salida"
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

        ch_num = int(channel)
        if not (1 <= ch_num <= 4):
            raise ValueError(f"Invalid channel selection for VirtOsc: {channel}. Must be 1-4.")

        async with locked_device(context, device, "VirtOsc Channel Config"):
            disp_str = "ON" if enable else "OFF"
            await asyncio.to_thread(device.write, f":CHANnel{ch_num}:DISPlay {disp_str}")
            if scale is not None:
                await asyncio.to_thread(device.write, f":CHANnel{ch_num}:SCALe {scale}")
            if offset is not None:
                await asyncio.to_thread(device.write, f":CHANnel{ch_num}:OFFSet {offset}")

        return "Out"


@register_block("devices/virtual/oscilloscope/trigger")
class VirtOscTriggerBlock(BaseBlock):
    """Configures the capture trigger mode on a VirtOsc device."""
    icon = "🎯"
    display_name = "VirtOsc Trigger"
    description = "Sets trigger operating mode (e.g. auto, free) on a VirtOsc device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Mode", type_hint=str, default="auto", widget="dropdown", options=["auto", "free"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]
    i18n = {
        "pt-BR": {
            "category": "Dispositivos/Virtual/Osciloscópio",
            "display_name": "Trigger VirtOsc",
            "description": "Define o modo de operação do trigger (ex: auto, free) em um dispositivo VirtOsc.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Mode": "Modo",
                "Out": "Saída"
            }
        },
        "es": {
            "category": "Dispositivos/Virtual/Osciloscopio",
            "display_name": "Trigger VirtOsc",
            "description": "Establece el modo de operación del trigger (ej: auto, free) en un dispositivo VirtOsc.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Mode": "Modo",
                "Out": "Salida"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        mode = await context.pull(self.id, "Mode")

        async with locked_device(context, device, "VirtOsc Trigger"):
            mode_str = str(mode).upper()
            await asyncio.to_thread(device.write, f":TRIGger:MODE {mode_str}")

        return "Out"


@register_block("devices/virtual/oscilloscope/state")
class VirtOscStateBlock(BaseBlock):
    """Starts or stops active scanning/acquiring loops on a VirtOsc device."""
    icon = "⏯️"
    display_name = "VirtOsc State"
    description = "Puts VirtOsc device scanning state to either RUN or STOP."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("State", type_hint=str, default="run", widget="dropdown", options=["run", "stop"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]
    i18n = {
        "pt-BR": {
            "category": "Dispositivos/Virtual/Osciloscópio",
            "display_name": "Estado VirtOsc",
            "description": "Coloca o estado de varredura do dispositivo VirtOsc em RUN ou STOP.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "State": "Estado",
                "Out": "Saída"
            }
        },
        "es": {
            "category": "Dispositivos/Virtual/Osciloscopio",
            "display_name": "Estado VirtOsc",
            "description": "Establece el estado de barrido del dispositivo VirtOsc en RUN o STOP.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "State": "Estado",
                "Out": "Salida"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        state = await context.pull(self.id, "State")

        async with locked_device(context, device, "VirtOsc State"):
            state_str = str(state).lower()
            if state_str == "run":
                await asyncio.to_thread(device.write, ":RUN")
            elif state_str == "stop":
                await asyncio.to_thread(device.write, ":STOP")

        return "Out"


@register_block("devices/virtual/oscilloscope/acquire")
class VirtOscAcquireBlock(BaseBlock):
    """Pulls timebase coordinates and waveform channel values from a VirtOsc device."""
    icon = "📥"
    display_name = "VirtOsc Acquire"
    description = "Triggers acquisition retrieval, outputs waveform arrays, and broadcasts visual plot telemetry."

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
            "category": "Dispositivos/Virtual/Osciloscópio",
            "display_name": "Adquirir VirtOsc",
            "description": "Aciona a aquisição, fornece arrays de forma de onda e transmite telemetria de plotagem visual.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Out": "Saída",
                "Waveform": "Forma de Onda",
                "Time": "Tempo"
            }
        },
        "es": {
            "category": "Dispositivos/Virtual/Osciloscopio",
            "display_name": "Adquirir VirtOsc",
            "description": "Activa la recuperación de adquisición, emite arrays de forma de onda y transmite telemetría de trazado visual.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Out": "Salida",
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
        ch_num = int(channel)
        if not (1 <= ch_num <= 4):
            raise ValueError(f"Invalid channel selection for VirtOsc: {channel}. Must be 1-4.")

        async with locked_device(context, device, "VirtOsc Acquire"):
            # Request time vector and channel data
            time_str = await asyncio.to_thread(device.query, ":TIMebase:DATA?")
            data_str = await asyncio.to_thread(device.query, f":CHANnel{ch_num}:DATA?")

            time_vals = [float(v) for v in time_str.split(",") if v.strip()]
            data_vals = [float(v) for v in data_str.split(",") if v.strip()]

            self._last_time = np.array(time_vals, dtype=float)
            self._last_waveform = np.array(data_vals, dtype=float)

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
