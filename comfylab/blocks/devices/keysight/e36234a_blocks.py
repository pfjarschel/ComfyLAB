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
from comfylab.devices.keysight.e36234a import KeysightE36234A


@register_block("devices/keysight/e36234a/connect")
class KeysightE36234AConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Keysight E36234A Dual-Output Autoranging DC Power Supply."""
    icon = "⚡"
    display_name = "Keysight E36234A Connect"
    description = "Opens a VISA session to a Keysight E36234A DC Power Supply. On teardown, turns outputs OFF."

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Conectar Keysight E36234A",
            "description": "Abre uma sessão VISA para uma Fonte DC Keysight E36234A (2 canais autorange). Ao desmontar, desliga as saídas.",
            "pins": {
                "Open": "Abrir",
                "Address": "Endereço",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Conectar Keysight E36234A",
            "description": "Abre una sesión VISA a una Fuente DC Keysight E36234A (2 canales autorange). Al desmontar, apaga las salidas.",
            "pins": {
                "Open": "Abrir",
                "Address": "Dirección",
                "Out": "Salida",
                "Device": "Dispositivo"
            }
        }
    }

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        drv = KeysightE36234A(device)
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(drv.set_output, False)
        else:
            await asyncio.to_thread(drv.set_output, False)


@register_block("devices/keysight/e36234a/channel")
class KeysightE36234ASetChannelBlock(BaseBlock):
    """Configures voltage setpoint (V), current limit (A), and output state on a Keysight E36234A channel."""
    icon = "⚙️"
    display_name = "Keysight E36234A Set Channel"
    description = "Sets voltage (0-60V), current limit (0-10A), and output on a Keysight E36234A channel."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2]),
        DataIn("Voltage", type_hint=float, default=5.0),
        DataIn("CurrentLimit", type_hint=float, default=1.0),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight E36234A Configurar Canal",
            "description": "Configura a tensão (0-60V), limite de corrente (0-10A) e saída no canal selecionado da Keysight E36234A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Voltage": "Tensão",
                "CurrentLimit": "LimiteCorrente",
                "Enable": "Habilitar"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight E36234A Configurar Canal",
            "description": "Configura el voltaje (0-60V), límite de corriente (0-10A) y salida en el canal de la Keysight E36234A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Voltage": "Voltaje",
                "CurrentLimit": "LímiteCorriente",
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
        channel = await context.pull(self.id, "Channel")
        voltage = await context.pull(self.id, "Voltage")
        curr_lim = await context.pull(self.id, "CurrentLimit")
        enable = await context.pull(self.id, "Enable")

        drv = KeysightE36234A(device)
        async with locked_device(context, device, "Keysight E36234A Set Channel"):
            await asyncio.to_thread(drv.set_channel, int(channel), voltage, curr_lim)
            if enable is not None:
                await asyncio.to_thread(drv.set_output, bool(enable), int(channel))

        return "Out"


@register_block("devices/keysight/e36234a/output")
class KeysightE36234AOutputBlock(BaseBlock):
    """Controls output state ON/OFF on a Keysight E36234A power supply."""
    icon = "🔌"
    display_name = "Keysight E36234A Output"
    description = "Toggles power supply output state ON or OFF (Channel 0 = All outputs)."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Channel", type_hint=int, default=0, widget="dropdown", options=[0, 1, 2], optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight E36234A Saída",
            "description": "Alterna o estado da saída da fonte entre LIGADO e DESLIGADO (Canal 0 = Ambos os canais).",
            "pins": {
                "Device": "Dispositivo",
                "Enable": "Habilitar",
                "Channel": "Canal"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight E36234A Salida",
            "description": "Alterna el estado de salida de la fuente entre ENCENDIDO y APAGADO (Canal 0 = Ambos canales).",
            "pins": {
                "Device": "Dispositivo",
                "Enable": "Habilitar",
                "Channel": "Canal"
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
        channel = await context.pull(self.id, "Channel")

        drv = KeysightE36234A(device)
        ch_arg = int(channel) if channel and int(channel) in (1, 2) else None
        async with locked_device(context, device, "Keysight E36234A Output"):
            await asyncio.to_thread(drv.set_output, bool(enable), ch_arg)

        return "Out"


@register_block("devices/keysight/e36234a/measure")
class KeysightE36234AMeasureBlock(BaseBlock):
    """Measures voltage (V), current (A), and power (W) on a Keysight E36234A channel."""
    icon = "📊"
    display_name = "Keysight E36234A Measure"
    description = "Queries real-time voltage (V), current (A), and power (W) on selected channel."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Voltage", type_hint=float),
        DataOut("Current", type_hint=float),
        DataOut("Power", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight E36234A Medir",
            "description": "Consulta a tensão (V), corrente (A) e potência (W) em tempo real no canal da Keysight E36234A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Voltage": "Tensão",
                "Current": "Corrente",
                "Power": "Potência"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight E36234A Medir",
            "description": "Consulta el voltaje (V), corriente (A) y potencia (W) en tiempo real en el canal de la Keysight E36234A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Voltage": "Voltaje",
                "Current": "Corriente",
                "Power": "Potencia"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._voltage: float = 0.0
        self._current: float = 0.0
        self._power: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        channel = await context.pull(self.id, "Channel")

        drv = KeysightE36234A(device)
        ch_idx = int(channel) if channel in (1, 2) else 1
        async with locked_device(context, device, "Keysight E36234A Measure"):
            v = await asyncio.to_thread(drv.measure_voltage, ch_idx)
            i = await asyncio.to_thread(drv.measure_current, ch_idx)
            p = await asyncio.to_thread(drv.measure_power, ch_idx)
            self._voltage = v
            self._current = i
            self._power = p

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Voltage":
            return self._voltage
        elif pin_name == "Current":
            return self._current
        elif pin_name == "Power":
            return self._power
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("devices/keysight/e36234a/measure_all")
class KeysightE36234AMeasureAllBlock(BaseBlock):
    """Measures both channels simultaneously on a Keysight E36234A power supply."""
    icon = "📈"
    display_name = "Keysight E36234A Measure All"
    description = "Queries real-time voltage, current, and power for Channels 1 & 2 simultaneously."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("V1", type_hint=float),
        DataOut("I1", type_hint=float),
        DataOut("P1", type_hint=float),
        DataOut("V2", type_hint=float),
        DataOut("I2", type_hint=float),
        DataOut("P2", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight E36234A Medir Todos",
            "description": "Consulta em tempo real a tensão, corrente e potência de ambos os canais simultaneamente.",
            "pins": {
                "Device": "Dispositivo",
                "V1": "V1",
                "I1": "I1",
                "P1": "P1",
                "V2": "V2",
                "I2": "I2",
                "P2": "P2"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight E36234A Medir Todos",
            "description": "Consulta en tiempo real el voltaje, corriente y potencia de ambos canales simultáneamente.",
            "pins": {
                "Device": "Dispositivo",
                "V1": "V1",
                "I1": "I1",
                "P1": "P1",
                "V2": "V2",
                "I2": "I2",
                "P2": "P2"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._v1: float = 0.0
        self._i1: float = 0.0
        self._p1: float = 0.0
        self._v2: float = 0.0
        self._i2: float = 0.0
        self._p2: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")

        drv = KeysightE36234A(device)
        async with locked_device(context, device, "Keysight E36234A Measure All"):
            results = await asyncio.to_thread(drv.measure_all)
            self._v1, self._i1, self._p1 = results.get("CH1", (0.0, 0.0, 0.0))
            self._v2, self._i2, self._p2 = results.get("CH2", (0.0, 0.0, 0.0))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "V1":
            return self._v1
        elif pin_name == "I1":
            return self._i1
        elif pin_name == "P1":
            return self._p1
        elif pin_name == "V2":
            return self._v2
        elif pin_name == "I2":
            return self._i2
        elif pin_name == "P2":
            return self._p2
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("devices/keysight/e36234a/pairing")
class KeysightE36234APairingBlock(BaseBlock):
    """Configures output pairing mode (Independent, Auto-Series up to 120V, Auto-Parallel up to 20A) on a Keysight E36234A."""
    icon = "🔗"
    display_name = "Keysight E36234A Output Pairing"
    description = "Configures auto-series (120V / 10A) or auto-parallel (60V / 20A) output pairing mode."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Mode", type_hint=str, default="OFF", widget="dropdown", options=["OFF", "SERIES", "PARALLEL"])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight E36234A Pareamento de Saídas",
            "description": "Configura modo de pareamento automático em série (120V / 10A) ou paralelo (60V / 20A).",
            "pins": {
                "Device": "Dispositivo",
                "Mode": "Modo"
            }
        },
        "es": {
            "category": "Instrumentos/Keysight",
            "display_name": "Keysight E36234A Emparejamiento de Salidas",
            "description": "Configura modo de emparejamiento automático en serie (120V / 10A) o paralelo (60V / 20A).",
            "pins": {
                "Device": "Dispositivo",
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
        mode = await context.pull(self.id, "Mode")

        drv = KeysightE36234A(device)
        async with locked_device(context, device, "Keysight E36234A Output Pairing"):
            await asyncio.to_thread(drv.set_pairing_mode, str(mode))

        return "Out"
