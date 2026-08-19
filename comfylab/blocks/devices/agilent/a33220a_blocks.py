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
from comfylab.devices.agilent.a33220a import Agilent33220A


@register_block("devices/agilent/a33220a/connect")
class Agilent33220AConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to an Agilent / Keysight 33220A 20 MHz Function Generator."""
    icon = "〰️"
    display_name = "Agilent 33220A Connect"
    description = "Opens a VISA session to an Agilent 33220A Function Generator. On teardown, turns output OFF."

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Agilent",
            "display_name": "Conectar Agilent 33220A",
            "description": "Abre uma sessão VISA para um Gerador de Funções Agilent 33220A. Ao desmontar, desliga a saída.",
            "pins": {
                "Open": "Abrir",
                "Address": "Endereço",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "category": "Instrumentos/Agilent",
            "display_name": "Conectar Agilent 33220A",
            "description": "Abre una sesión VISA con un Generador de Funciones Agilent 33220A. Al desmontar, apaga la salida.",
            "pins": {
                "Open": "Abrir",
                "Address": "Dirección",
                "Out": "Salida",
                "Device": "Dispositivo"
            }
        }
    }

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        drv = Agilent33220A(device)
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(drv.set_output, False)
        else:
            await asyncio.to_thread(drv.set_output, False)


@register_block("devices/agilent/a33220a/wave")
class Agilent33220AWaveBlock(BaseBlock):
    """Configures output waveform shape, frequency, amplitude, offset, and output on an Agilent 33220A."""
    icon = "🎛️"
    display_name = "Agilent 33220A Waveform"
    description = "Sets waveform function, frequency (Hz), amplitude (Vpp), offset (V), and duty/symmetry."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Shape", type_hint=str, default="SIN", widget="dropdown", options=["SIN", "SQU", "RAMP", "PULS", "NOIS", "DC"]),
        DataIn("Frequency", type_hint=float, default=1000.0),
        DataIn("Amplitude", type_hint=float, default=1.0),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("DutyOrSym", type_hint=float, default=50.0, optional=True),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Agilent",
            "display_name": "Agilent 33220A Forma de Onda",
            "description": "Configura a função da onda, frequência (Hz), amplitude (Vpp), offset (V) e simetria/duty cycle.",
            "pins": {
                "Device": "Dispositivo",
                "Shape": "Forma",
                "Frequency": "Frequência",
                "Amplitude": "Amplitude",
                "Offset": "Offset",
                "DutyOrSym": "Duty/Simetria",
                "Enable": "Habilitar"
            }
        },
        "es": {
            "category": "Instrumentos/Agilent",
            "display_name": "Agilent 33220A Forma de Onda",
            "description": "Configura la función de onda, frecuencia (Hz), amplitud (Vpp), offset (V) y simetría/ciclo de trabajo.",
            "pins": {
                "Device": "Dispositivo",
                "Shape": "Forma",
                "Frequency": "Frecuencia",
                "Amplitude": "Amplitud",
                "Offset": "Offset",
                "DutyOrSym": "Duty/Simetría",
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
        duty_sym = await context.pull(self.id, "DutyOrSym")
        enable = await context.pull(self.id, "Enable")

        drv = Agilent33220A(device)
        async with locked_device(context, device, "Agilent 33220A Waveform"):
            await asyncio.to_thread(drv.set_wave, shape, frequency, amplitude, offset, duty_sym)
            if enable is not None:
                await asyncio.to_thread(drv.set_output, bool(enable))

        return "Out"


@register_block("devices/agilent/a33220a/output")
class Agilent33220AOutputBlock(BaseBlock):
    """Controls output state, load impedance, and inversion on an Agilent 33220A."""
    icon = "🔌"
    display_name = "Agilent 33220A Output"
    description = "Toggles output state (ON/OFF), load impedance (50 Ohm / High-Z), and polarity."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Load", type_hint=str, default="50", widget="dropdown", options=["50", "INF"]),
        DataIn("Inverted", type_hint=bool, default=False, widget="checkbox", optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Agilent",
            "display_name": "Agilent 33220A Saída",
            "description": "Alterna a saída (LIGADO/DESLIGADO), impedância de carga (50 Ohm / High-Z) e polaridade.",
            "pins": {
                "Device": "Dispositivo",
                "Enable": "Habilitar",
                "Load": "Carga",
                "Inverted": "Invertido"
            }
        },
        "es": {
            "category": "Instrumentos/Agilent",
            "display_name": "Agilent 33220A Salida",
            "description": "Alterna la salida (ENCENDIDO/APAGADO), impedancia de carga (50 Ohm / High-Z) y polaridad.",
            "pins": {
                "Device": "Dispositivo",
                "Enable": "Habilitar",
                "Load": "Carga",
                "Inverted": "Invertido"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        enable = await context.pull(self.id, "Enable")
        load = await context.pull(self.id, "Load")
        inverted = await context.pull(self.id, "Inverted")

        drv = Agilent33220A(device)
        async with locked_device(context, device, "Agilent 33220A Output"):
            await asyncio.to_thread(drv.set_output, bool(enable), str(load), bool(inverted))

        return "Out"


@register_block("devices/agilent/a33220a/pulse")
class Agilent33220APulseBlock(BaseBlock):
    """Configures high-precision pulse parameters on an Agilent 33220A."""
    icon = "⚡"
    display_name = "Agilent 33220A Pulse"
    description = "Configures pulse period (s), width (s), and transition edge time (s)."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Period", type_hint=float, default=1e-3),
        DataIn("Width", type_hint=float, default=1e-4),
        DataIn("Transition", type_hint=float, default=1e-8, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Agilent",
            "display_name": "Agilent 33220A Pulso",
            "description": "Configura período do pulso (s), largura (s) e tempo de transição de borda (s).",
            "pins": {
                "Device": "Dispositivo",
                "Period": "Período",
                "Width": "Largura",
                "Transition": "Transição"
            }
        },
        "es": {
            "category": "Instrumentos/Agilent",
            "display_name": "Agilent 33220A Pulso",
            "description": "Configura el período de pulso (s), ancho (s) y tiempo de transición de flanco (s).",
            "pins": {
                "Device": "Dispositivo",
                "Period": "Período",
                "Width": "Ancho",
                "Transition": "Transición"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        period = await context.pull(self.id, "Period")
        width = await context.pull(self.id, "Width")
        transition = await context.pull(self.id, "Transition")

        drv = Agilent33220A(device)
        async with locked_device(context, device, "Agilent 33220A Pulse"):
            await asyncio.to_thread(drv.set_pulse, period, width, transition)

        return "Out"


@register_block("devices/agilent/a33220a/sweep")
class Agilent33220ASweepBlock(BaseBlock):
    """Configures frequency sweep mode on an Agilent 33220A."""
    icon = "📈"
    display_name = "Agilent 33220A Sweep"
    description = "Sets start frequency (Hz), stop frequency (Hz), sweep time (s), spacing, and state."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("StartFreq", type_hint=float, default=100.0),
        DataIn("StopFreq", type_hint=float, default=10000.0),
        DataIn("SweepTime", type_hint=float, default=1.0),
        DataIn("Spacing", type_hint=str, default="LIN", widget="dropdown", options=["LIN", "LOG"]),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Agilent",
            "display_name": "Agilent 33220A Varredura",
            "description": "Configura frequência inicial, final, tempo de varredura (s), espaçamento e ativação.",
            "pins": {
                "Device": "Dispositivo",
                "StartFreq": "Freq Inicial",
                "StopFreq": "Freq Final",
                "SweepTime": "Tempo",
                "Spacing": "Espaçamento",
                "Enable": "Habilitar"
            }
        },
        "es": {
            "category": "Instrumentos/Agilent",
            "display_name": "Agilent 33220A Barrido",
            "description": "Configura frecuencia inicial, final, tiempo de barrido (s), espaciado y activación.",
            "pins": {
                "Device": "Dispositivo",
                "StartFreq": "Freq Inicial",
                "StopFreq": "Freq Final",
                "SweepTime": "Tiempo",
                "Spacing": "Espaciado",
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
        start_f = await context.pull(self.id, "StartFreq")
        stop_f = await context.pull(self.id, "StopFreq")
        t_sweep = await context.pull(self.id, "SweepTime")
        spacing = await context.pull(self.id, "Spacing")
        enable = await context.pull(self.id, "Enable")

        drv = Agilent33220A(device)
        async with locked_device(context, device, "Agilent 33220A Sweep"):
            await asyncio.to_thread(drv.set_sweep, start_f, stop_f, t_sweep, str(spacing), bool(enable))

        return "Out"
