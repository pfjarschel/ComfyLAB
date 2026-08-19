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
from comfylab.devices.keithley.k2231a import Keithley2231A


@register_block("devices/keithley/k2231a/connect")
class Keithley2231AConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a Keithley 2231A-30-3 Triple-Channel DC Power Supply."""
    icon = "⚡"
    display_name = "Keithley 2231A Connect"
    description = "Opens a VISA session to a Keithley 2231A-30-3 DC Power Supply. On teardown, turns outputs OFF."

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keithley",
            "display_name": "Conectar Keithley 2231A",
            "description": "Abre uma sessão VISA para uma Fonte DC Keithley 2231A-30-3. Ao desmontar, desliga as saídas.",
            "pins": {
                "Open": "Abrir",
                "Address": "Endereço",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "category": "Instrumentos/Keithley",
            "display_name": "Conectar Keithley 2231A",
            "description": "Abre una sesión VISA a una Fuente DC Keithley 2231A-30-3. Al desmontar, apaga las salidas.",
            "pins": {
                "Open": "Abrir",
                "Address": "Dirección",
                "Out": "Salida",
                "Device": "Dispositivo"
            }
        }
    }

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        drv = Keithley2231A(device)
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(drv.set_output, False)
        else:
            await asyncio.to_thread(drv.set_output, False)


@register_block("devices/keithley/k2231a/channel")
class Keithley2231ASetChannelBlock(BaseBlock):
    """Configures voltage, current limit, and output state for a channel on a Keithley 2231A."""
    icon = "⚙️"
    display_name = "Keithley 2231A Set Channel"
    description = "Configures voltage setpoint (V), current limit (A), and output on a Keithley 2231A channel."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3]),
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
            "category": "Instrumentos/Keithley",
            "display_name": "Keithley 2231A Configurar Canal",
            "description": "Configura a tensão (V), limite de corrente (A) e ativa a saída em um canal da Keithley 2231A.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Voltage": "Tensão",
                "CurrentLimit": "LimiteCorrente",
                "Enable": "Habilitar"
            }
        },
        "es": {
            "category": "Instrumentos/Keithley",
            "display_name": "Keithley 2231A Configurar Canal",
            "description": "Configura el voltaje (V), límite de corriente (A) y habilita la salida en un canal de la Keithley 2231A.",
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

        drv = Keithley2231A(device)
        async with locked_device(context, device, "Keithley 2231A Set Channel"):
            await asyncio.to_thread(drv.set_channel, int(channel), voltage, curr_lim)
            if enable is not None:
                await asyncio.to_thread(drv.set_output, bool(enable), int(channel))

        return "Out"


@register_block("devices/keithley/k2231a/output")
class Keithley2231AOutputBlock(BaseBlock):
    """Enables or disables outputs on a Keithley 2231A power supply."""
    icon = "🔌"
    display_name = "Keithley 2231A Output"
    description = "Toggles power supply output state ON or OFF."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("Channel", type_hint=int, default=0, widget="dropdown", options=[0, 1, 2, 3], optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keithley",
            "display_name": "Keithley 2231A Saída",
            "description": "Alterna o estado da saída da fonte entre LIGADO e DESLIGADO (Canal 0 = Global).",
            "pins": {
                "Device": "Dispositivo",
                "Enable": "Habilitar",
                "Channel": "Canal"
            }
        },
        "es": {
            "category": "Instrumentos/Keithley",
            "display_name": "Keithley 2231A Salida",
            "description": "Alterna el estado de salida de la fuente entre ENCENDIDO y APAGADO (Canal 0 = Global).",
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

        drv = Keithley2231A(device)
        ch_arg = int(channel) if channel and int(channel) in (1, 2, 3) else None
        async with locked_device(context, device, "Keithley 2231A Output"):
            await asyncio.to_thread(drv.set_output, bool(enable), ch_arg)

        return "Out"


@register_block("devices/keithley/k2231a/measure")
class Keithley2231AMeasureBlock(BaseBlock):
    """Measures actual voltage, current, and computed power on a Keithley 2231A channel."""
    icon = "📊"
    display_name = "Keithley 2231A Measure"
    description = "Queries real-time voltage (V), current (A), and power (W) on selected channel."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=1, widget="dropdown", options=[1, 2, 3])
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
            "category": "Instrumentos/Keithley",
            "display_name": "Keithley 2231A Medir",
            "description": "Consulta a tensão (V), corrente (A) e potência (W) em tempo real no canal selecionado.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Voltage": "Tensão",
                "Current": "Corrente",
                "Power": "Potência"
            }
        },
        "es": {
            "category": "Instrumentos/Keithley",
            "display_name": "Keithley 2231A Medir",
            "description": "Consulta el voltaje (V), corriente (A) y potencia (W) en tiempo real en el canal seleccionado.",
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

        drv = Keithley2231A(device)
        ch_idx = int(channel) if channel in (1, 2, 3) else 1
        async with locked_device(context, device, "Keithley 2231A Measure"):
            v = await asyncio.to_thread(drv.measure_voltage, ch_idx)
            i = await asyncio.to_thread(drv.measure_current, ch_idx)
            self._voltage = v
            self._current = i
            self._power = v * i

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


@register_block("devices/keithley/k2231a/measure_all")
class Keithley2231AMeasureAllBlock(BaseBlock):
    """Measures all 3 channels simultaneously on a Keithley 2231A power supply."""
    icon = "📈"
    display_name = "Keithley 2231A Measure All"
    description = "Queries real-time voltage and current for channels 1, 2, and 3 simultaneously."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("V1", type_hint=float),
        DataOut("I1", type_hint=float),
        DataOut("V2", type_hint=float),
        DataOut("I2", type_hint=float),
        DataOut("V3", type_hint=float),
        DataOut("I3", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Keithley",
            "display_name": "Keithley 2231A Medir Todos",
            "description": "Consulta em tempo real a tensão e corrente de todos os 3 canais simultaneamente.",
            "pins": {
                "Device": "Dispositivo",
                "V1": "V1",
                "I1": "I1",
                "V2": "V2",
                "I2": "I2",
                "V3": "V3",
                "I3": "I3"
            }
        },
        "es": {
            "category": "Instrumentos/Keithley",
            "display_name": "Keithley 2231A Medir Todos",
            "description": "Consulta en tiempo real el voltaje y la corriente de los 3 canales simultáneamente.",
            "pins": {
                "Device": "Dispositivo",
                "V1": "V1",
                "I1": "I1",
                "V2": "V2",
                "I2": "I2",
                "V3": "V3",
                "I3": "I3"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._v1: float = 0.0
        self._i1: float = 0.0
        self._v2: float = 0.0
        self._i2: float = 0.0
        self._v3: float = 0.0
        self._i3: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")

        drv = Keithley2231A(device)
        async with locked_device(context, device, "Keithley 2231A Measure All"):
            results = await asyncio.to_thread(drv.measure_all)
            self._v1, self._i1 = results.get("CH1", (0.0, 0.0))
            self._v2, self._i2 = results.get("CH2", (0.0, 0.0))
            self._v3, self._i3 = results.get("CH3", (0.0, 0.0))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "V1":
            return self._v1
        elif pin_name == "I1":
            return self._i1
        elif pin_name == "V2":
            return self._v2
        elif pin_name == "I2":
            return self._i2
        elif pin_name == "V3":
            return self._v3
        elif pin_name == "I3":
            return self._i3
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
