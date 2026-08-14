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
from comfylab.devices.yokogawa.aq6370 import AQ6370


@register_block("devices/yokogawa/aq6370/connect")
class AQ6370ConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Yokogawa / Ando AQ6370 Series Optical Spectrum Analyzer (OSA)."""
    icon = "🌈"
    display_name = "Yokogawa AQ6370 Connect"
    description = "Opens a VISA session to a Yokogawa AQ6370 Optical Spectrum Analyzer."

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Yokogawa",
            "display_name": "Conectar Yokogawa AQ6370",
            "description": "Abre uma sessão VISA para um Analisador de Espectro Óptico Yokogawa AQ6370."
        },
        "es": {
            "category": "Instrumentos/Yokogawa",
            "display_name": "Conectar Yokogawa AQ6370",
            "description": "Abre una sesión VISA a un Analizador de Espectro Óptico Yokogawa AQ6370."
        }
    }


@register_block("devices/yokogawa/aq6370/sweep_config")
class AQ6370SweepConfigBlock(BaseBlock):
    """Configures wavelength/span/RBW/sensitivity and sweep mode/traces on a Yokogawa OSA."""
    icon = "🎛️"
    display_name = "Yokogawa AQ6370 Sweep Config"
    description = "Configures center wavelength, span, RBW, sensitivity, sweep mode, and active trace on a Yokogawa AQ6370 OSA."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("CenterWavelength", type_hint=float, default=1550.0, optional=True),
        DataIn("Span", type_hint=float, default=20.0, optional=True),
        DataIn("RBW", type_hint=float, default=0.02, optional=True),
        DataIn("Sensitivity", type_hint=str, default="NORM", widget="dropdown", options=["NORM", "HIGH1", "HIGH2", "HIGH3", "MID"], optional=True),
        DataIn("SweepMode", type_hint=str, default="REPEAT", widget="dropdown", options=["REPEAT", "SINGLE", "STOP"], optional=True),
        DataIn("ActiveTrace", type_hint=str, default="TRA", widget="dropdown", options=["TRA", "TRB", "TRC", "TRD", "TRE", "TRF", "TRG"], optional=True),
        DataIn("FixOtherTraces", type_hint=bool, default=True, optional=True),
        DataIn("WaitCompletion", type_hint=bool, default=False, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Yokogawa",
            "display_name": "Configuração de Varredura Yokogawa AQ6370",
            "description": "Configura comprimento de onda central, span, RBW, sensibilidade, modo de varredura e traço ativo em um OSA Yokogawa AQ6370.",
            "pins": {
                "Device": "Dispositivo",
                "CenterWavelength": "ComprimentoDeOndaCentral",
                "WaitCompletion": "AguardarConclusao",
                "FixOtherTraces": "FixarOutrosTracos"
            }
        },
        "es": {
            "category": "Instrumentos/Yokogawa",
            "display_name": "Configuración de Barrido Yokogawa AQ6370",
            "description": "Configura la longitud de onda central, span, RBW, sensibilidad, modo de barrido y traza activa en un OSA Yokogawa AQ6370.",
            "pins": {
                "Device": "Dispositivo",
                "CenterWavelength": "LongitudDeOndaCentral",
                "WaitCompletion": "EsperarFinalizacion",
                "FixOtherTraces": "FijarOtrasTrazas"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        center_nm = await context.pull(self.id, "CenterWavelength")
        span_nm = await context.pull(self.id, "Span")
        rbw_nm = await context.pull(self.id, "RBW")
        sens = await context.pull(self.id, "Sensitivity")
        mode = await context.pull(self.id, "SweepMode")
        active_trace = await context.pull(self.id, "ActiveTrace")
        fix_others = await context.pull(self.id, "FixOtherTraces")
        wait = await context.pull(self.id, "WaitCompletion")

        drv = AQ6370(device)
        async with locked_device(context, device, "Yokogawa AQ6370 Sweep Config"):
            await asyncio.to_thread(drv.set_sweep_config, center_nm, span_nm, rbw_nm, sens)
            if mode is not None or active_trace is not None:
                sweep_m = str(mode or "REPEAT")
                tr_name = str(active_trace or "TRA")
                fix_o = bool(fix_others if fix_others is not None else True)
                wait_c = bool(wait if wait is not None else False)
                await asyncio.to_thread(drv.sweep, mode=sweep_m, active_trace=tr_name, fix_other_traces=fix_o, wait=wait_c)

        return "Out"


@register_block("devices/yokogawa/aq6370/acquire")
class AQ6370AcquireBlock(BaseBlock):
    """Pulls wavelength (nm) and optical spectrum trace (dBm) directly from Yokogawa OSA memory."""
    icon = "📥"
    display_name = "Yokogawa AQ6370 Get Trace Data"
    description = "Fetches wavelength and power trace arrays directly from Yokogawa OSA memory without triggering a sweep, broadcasting plot telemetry."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Trace", type_hint=str, default="TRA", widget="dropdown", options=["TRA", "TRB", "TRC", "TRD", "TRE", "TRF", "TRG"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Power", type_hint=np.ndarray),
        DataOut("Wavelength", type_hint=np.ndarray),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Yokogawa",
            "display_name": "Yokogawa AQ6370 Obter Dados do Traço",
            "description": "Busca vetores de comprimento de onda e potência diretamente da memória do OSA Yokogawa sem acionar uma varredura.",
            "pins": {
                "Device": "Dispositivo",
                "Trace": "Traco",
                "Power": "Potencia",
                "Wavelength": "ComprimentoDeOnda"
            }
        },
        "es": {
            "category": "Instrumentos/Yokogawa",
            "display_name": "Yokogawa AQ6370 Obtener Datos de Traza",
            "description": "Obtiene arreglos de longitud de onda y potencia directamente de la memoria del OSA Yokogawa sin activar un barrido.",
            "pins": {
                "Device": "Dispositivo",
                "Trace": "Traza",
                "Power": "Potencia",
                "Wavelength": "LongitudDeOnda"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_power: np.ndarray = np.array([])
        self._last_wl: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        trace_name = await context.pull(self.id, "Trace")

        drv = AQ6370(device)
        async with locked_device(context, device, "Yokogawa AQ6370 Get Trace Data"):
            wl_vec, p_vec = await asyncio.to_thread(drv.get_trace, str(trace_name))
            self._last_wl = wl_vec
            self._last_power = p_vec

            # Broadcast plot telemetry
            floats = self._last_power.tolist()
            point_count = len(floats)
            encoded_id = self.id.encode('utf-8')[:36].ljust(36, b'\x00')
            binary_packet = struct.pack(f"<36sI{point_count}f", encoded_id, point_count, *floats)
            await context.send_telemetry(self.id, binary_packet)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Power":
            return self._last_power
        elif pin_name == "Wavelength":
            return self._last_wl
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("devices/yokogawa/aq6370/sweep_and_acquire")
class AQ6370SweepAndAcquireBlock(BaseBlock):
    """Triggers a single sweep on a Yokogawa OSA, waits for completion, and pulls trace arrays."""
    icon = "⚡"
    display_name = "Yokogawa AQ6370 Sweep & Acquire"
    description = "Triggers a single sweep, waits for completion, and fetches trace arrays from a Yokogawa OSA."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Trace", type_hint=str, default="TRA", widget="dropdown", options=["TRA", "TRB", "TRC", "TRD", "TRE", "TRF", "TRG"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Power", type_hint=np.ndarray),
        DataOut("Wavelength", type_hint=np.ndarray),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Yokogawa",
            "display_name": "Yokogawa AQ6370 Varrer e Adquirir",
            "description": "Aciona uma única varredura, aguarda a conclusão e busca os vetores do traço de um OSA Yokogawa.",
            "pins": {
                "Device": "Dispositivo",
                "Trace": "Traco",
                "Power": "Potencia",
                "Wavelength": "ComprimentoDeOnda"
            }
        },
        "es": {
            "category": "Instrumentos/Yokogawa",
            "display_name": "Yokogawa AQ6370 Barrer y Adquirir",
            "description": "Activa un solo barrido, espera la finalización y obtiene los arreglos de traza de un OSA Yokogawa.",
            "pins": {
                "Device": "Dispositivo",
                "Trace": "Traza",
                "Power": "Potencia",
                "Wavelength": "LongitudDeOnda"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_power: np.ndarray = np.array([])
        self._last_wl: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        trace_name = await context.pull(self.id, "Trace")

        drv = AQ6370(device)
        async with locked_device(context, device, "Yokogawa AQ6370 Sweep & Acquire"):
            wl_vec, p_vec = await asyncio.to_thread(drv.sweep_and_acquire, str(trace_name))
            self._last_wl = wl_vec
            self._last_power = p_vec

            # Broadcast plot telemetry
            floats = self._last_power.tolist()
            point_count = len(floats)
            encoded_id = self.id.encode('utf-8')[:36].ljust(36, b'\x00')
            binary_packet = struct.pack(f"<36sI{point_count}f", encoded_id, point_count, *floats)
            await context.send_telemetry(self.id, binary_packet)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Power":
            return self._last_power
        elif pin_name == "Wavelength":
            return self._last_wl
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None



