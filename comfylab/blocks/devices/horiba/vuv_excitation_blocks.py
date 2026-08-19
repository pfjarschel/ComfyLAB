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
from comfylab.devices.horiba.vuv_excitation import HoribaVUVExcitation


@register_block("devices/horiba/vuv_excitation/connect")
class HoribaVUVConnectBlock(BaseBlock):
    """Initializes communication with a Horiba Jobin Yvon H20-UVL / VUV Excitation Monochromator."""
    icon = "🌈"
    display_name = "Horiba VUV Monochromator Connect"
    description = "Opens a session to a Horiba VUV Monochromator system via ActiveX/COM or simulation."

    inputs_def = [
        ExecIn("Open"),
        DataIn("MonoID", type_hint=str, default="Mono5", widget="text"),
        DataIn("Simulate", type_hint=bool, default=False, widget="checkbox", optional=True),
        DataIn("ForceInit", type_hint=bool, default=False, widget="checkbox", optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Horiba",
            "display_name": "Conectar Monocromador Horiba VUV",
            "description": "Abre uma sessão para o sistema de Monocromador Horiba VUV via ActiveX/COM ou simulação.",
            "pins": {
                "Open": "Abrir",
                "MonoID": "ID Monocromador",
                "Simulate": "Simular",
                "ForceInit": "Forçar Inicialização",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "category": "Instrumentos/Horiba",
            "display_name": "Conectar Monocromador Horiba VUV",
            "description": "Abre una sesión para el sistema de Monocromador Horiba VUV vía ActiveX/COM o simulación.",
            "pins": {
                "Open": "Abrir",
                "MonoID": "ID Monocromador",
                "Simulate": "Simular",
                "ForceInit": "Forzar Inicialización",
                "Out": "Salida",
                "Device": "Dispositivo"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._device: Optional[HoribaVUVExcitation] = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        mono_id = await context.pull(self.id, "MonoID")
        simulate = await context.pull(self.id, "Simulate")
        force_init = await context.pull(self.id, "ForceInit")

        mono_id_str = str(mono_id) if mono_id else "Mono5"
        self._device = HoribaVUVExcitation(mono_id=mono_id_str, simulate=bool(simulate))
        await asyncio.to_thread(self._device.initialize, force_init=bool(force_init), emulate=bool(simulate))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return self._device
        return None

    async def teardown(self) -> None:
        if self._device:
            try:
                await asyncio.to_thread(self._device.close)
            except Exception:
                pass
            finally:
                self._device = None


@register_block("devices/horiba/vuv_excitation/wavelength")
class HoribaVUVWavelengthBlock(BaseBlock):
    """Sets target wavelength (nm) and reads the current wavelength from a Horiba VUV Monochromator."""
    icon = "🎯"
    display_name = "Horiba VUV Wavelength"
    description = "Positions the monochromator to the target wavelength (nm) and returns current wavelength."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Wavelength", type_hint=float, default=200.0)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("CurrentWL", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Horiba",
            "display_name": "Comprimento de Onda Horiba VUV",
            "description": "Move o monocromador para o comprimento de onda desejado (nm) e retorna a posição atual.",
            "pins": {
                "Device": "Dispositivo",
                "Wavelength": "Comprimento (nm)",
                "CurrentWL": "WL Atual (nm)"
            }
        },
        "es": {
            "category": "Instrumentos/Horiba",
            "display_name": "Longitud de Onda Horiba VUV",
            "description": "Mueve el monocromador a la longitud de onda deseada (nm) y devuelve la posición actual.",
            "pins": {
                "Device": "Dispositivo",
                "Wavelength": "Longitud (nm)",
                "CurrentWL": "WL Actual (nm)"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._current_wl: float = 200.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        wl = await context.pull(self.id, "Wavelength")

        if isinstance(device, HoribaVUVExcitation):
            await asyncio.to_thread(device.set_wavelength, float(wl))
            self._current_wl = await asyncio.to_thread(device.get_current_wavelength)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "CurrentWL":
            return self._current_wl
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("devices/horiba/vuv_excitation/grating")
class HoribaVUVGratingBlock(BaseBlock):
    """Selects grating turret and reads grating properties (density, blaze, description) on Horiba Monochromator."""
    icon = "💎"
    display_name = "Horiba VUV Grating Turret"
    description = "Changes grating turret selection and returns active grating parameters."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Turret", type_hint=int, default=0, widget="dropdown", options=[0, 1, 2])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("LinesPerMM", type_hint=float),
        DataOut("Blaze", type_hint=str),
        DataOut("Description", type_hint=str),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Horiba",
            "display_name": "Torreta de Grades Horiba VUV",
            "description": "Altera a torreta de grade de difração e obtém densidade, blaze e descrição da grade.",
            "pins": {
                "Device": "Dispositivo",
                "Turret": "Torreta",
                "LinesPerMM": "Linhas/mm",
                "Blaze": "Blaze",
                "Description": "Descrição"
            }
        },
        "es": {
            "category": "Instrumentos/Horiba",
            "display_name": "Torreta de Rejillas Horiba VUV",
            "description": "Cambia la torreta de rejilla de difracción y obtiene densidad, blaze y descripción.",
            "pins": {
                "Device": "Dispositivo",
                "Turret": "Torreta",
                "LinesPerMM": "Líneas/mm",
                "Blaze": "Blaze",
                "Description": "Descripción"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._lines: float = 1200.0
        self._blaze: str = "200"
        self._desc: str = ""

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        turret = await context.pull(self.id, "Turret")

        if isinstance(device, HoribaVUVExcitation):
            await asyncio.to_thread(device.set_current_grating_turret, int(turret))
            grats = await asyncio.to_thread(device.get_gratings)
            t_idx = int(turret)
            if 0 <= t_idx < len(grats):
                g = grats[t_idx]
                self._lines = g.lines
                self._blaze = g.blaze
                self._desc = g.description

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "LinesPerMM":
            return self._lines
        elif pin_name == "Blaze":
            return self._blaze
        elif pin_name == "Description":
            return self._desc
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("devices/horiba/vuv_excitation/slit")
class HoribaVUVSlitBlock(BaseBlock):
    """Configures entrance and exit slit widths (mm) on a Horiba VUV Monochromator."""
    icon = "🚪"
    display_name = "Horiba VUV Slit Width"
    description = "Configures entrance and exit slit widths in millimeters (mm)."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Slit", type_hint=int, default=0, widget="dropdown", options=[0, 1, 2, 3, 4, 5]),
        DataIn("Width_mm", type_hint=float, default=0.5)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("CurrentWidth", type_hint=float),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Horiba",
            "display_name": "Fenda Horiba VUV",
            "description": "Configura a abertura da fenda de entrada ou saída em milímetros (0: Entr. Frontal, 1: Entr. Lateral, 2: Saída Frontal, 3: Saída Lateral).",
            "pins": {
                "Device": "Dispositivo",
                "Slit": "Fenda",
                "Width_mm": "Abertura (mm)",
                "CurrentWidth": "Abertura Atual"
            }
        },
        "es": {
            "category": "Instrumentos/Horiba",
            "display_name": "Rendija Horiba VUV",
            "description": "Configura la apertura de la rendija de entrada o salida en milímetros.",
            "pins": {
                "Device": "Dispositivo",
                "Slit": "Rendija",
                "Width_mm": "Apertura (mm)",
                "CurrentWidth": "Apertura Actual"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._current_width: float = 0.5

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        slit = await context.pull(self.id, "Slit")
        width = await context.pull(self.id, "Width_mm")

        if isinstance(device, HoribaVUVExcitation):
            await asyncio.to_thread(device.set_slit_width, int(slit), float(width))
            self._current_width = await asyncio.to_thread(device.get_slit_width, int(slit))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "CurrentWidth":
            return self._current_width
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("devices/horiba/vuv_excitation/mirror")
class HoribaVUVMirrorBlock(BaseBlock):
    """Sets mirror positions (Front vs Side) on entrance or exit ports of a Horiba VUV Monochromator."""
    icon = "🪞"
    display_name = "Horiba VUV Mirror Position"
    description = "Switches entrance (0) or exit (1) mirror position between Front (0) and Side (1)."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Mirror", type_hint=int, default=0, widget="dropdown", options=[0, 1]),
        DataIn("Position", type_hint=int, default=0, widget="dropdown", options=[0, 1])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("CurrentPos", type_hint=int),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/Horiba",
            "display_name": "Espelho Horiba VUV",
            "description": "Alterna a posição do espelho de entrada (0) ou saída (1) entre Frontal (0) e Lateral (1).",
            "pins": {
                "Device": "Dispositivo",
                "Mirror": "Espelho",
                "Position": "Posição",
                "CurrentPos": "Posição Atual"
            }
        },
        "es": {
            "category": "Instrumentos/Horiba",
            "display_name": "Espejo Horiba VUV",
            "description": "Alterna la posición del espejo de entrada (0) o salida (1) entre Frontal (0) y Lateral (1).",
            "pins": {
                "Device": "Dispositivo",
                "Mirror": "Espejo",
                "Position": "Posición",
                "CurrentPos": "Posición Actual"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._current_pos: int = 0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        mirror = await context.pull(self.id, "Mirror")
        position = await context.pull(self.id, "Position")

        if isinstance(device, HoribaVUVExcitation):
            await asyncio.to_thread(device.set_mirror_position, int(mirror), int(position))
            self._current_pos = await asyncio.to_thread(device.get_mirror_position, int(mirror))

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "CurrentPos":
            return self._current_pos
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
