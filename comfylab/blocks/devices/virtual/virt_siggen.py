# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
from typing import Any, Optional, Dict

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.blocks.devices.base import BaseDeviceConnectBlock, locked_device
from comfylab.virtual.manager import VirtualInstrumentManager


@register_block("devices/virtual/signal_generator/connect")
class VirtSigGenConnectBlock(BaseDeviceConnectBlock):
    """Opens a VISA connection to a VirtSigGen device with safety teardown (output off)."""
    icon = "⚡"
    display_name = "VirtSigGen Connect"
    description = "Opens a VISA connection to a VirtSigGen signal generator. On teardown, disables output."
    inputs_def = [
        ExecIn("Open"),
        DataIn("Address", type_hint=str, default="TCPIP0::127.0.0.1::51235::SOCKET", widget="text"),
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
            "category": "Dispositivos/Virtual/Gerador de Sinal",
            "display_name": "Conexão VirtSigGen",
            "description": "Abre uma conexão VISA para um gerador de sinais VirtSigGen. Na desconexão, desabilita a saída.",
            "pins": {
                "Open": "Abrir",
                "Address": "Endereço",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "category": "Dispositivos/Virtual/Generador de Señales",
            "display_name": "Conexión VirtSigGen",
            "description": "Abre una conexión VISA a un generador de señales VirtSigGen. Al desconectar, deshabilita la salida.",
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
        if address and ("51235" in str(address) or "VIRT" in str(address).upper() or "127.0.0.1" in str(address)):
            await asyncio.to_thread(VirtualInstrumentManager.ensure_started)
            VirtualInstrumentManager.register_client(self.id)

        res = await super().execute(context, trigger_pin)
        return res

    async def _device_teardown(self, device: Any, lock_manager: Any) -> None:
        address = getattr(device, "resource_name", None)
        if address and lock_manager:
            async with lock_manager.acquire(address, timeout=5.0):
                await asyncio.to_thread(device.write, ":OUTPut1:STATe OFF")
        else:
            await asyncio.to_thread(device.write, ":OUTPut1:STATe OFF")

    async def teardown(self) -> None:
        try:
            await super().teardown()
        finally:
            VirtualInstrumentManager.unregister_client(self.id)


@register_block("devices/virtual/signal_generator/config_wave")
class VirtSigGenConfigWaveBlock(BaseBlock):
    """Configures the main waveform output parameters of a VirtSigGen device."""
    icon = "🎵"
    display_name = "VirtSigGen Config Wave"
    description = "Configures wave shape, frequency, amplitude, offset, phase, and duty cycle of a VirtSigGen device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("WaveType", type_hint=str, default="sine", widget="dropdown", options=["sine", "triangle", "square", "saw", "rsaw", "pulse"]),
        DataIn("Frequency", type_hint=float, default=1000.0, optional=True),
        DataIn("Amplitude", type_hint=float, default=1.0, optional=True),
        DataIn("Offset", type_hint=float, default=0.0, optional=True),
        DataIn("Phase", type_hint=float, default=0.0, optional=True),
        DataIn("DutyCycle", type_hint=float, default=50.0, optional=True),
        DataIn("Noise", type_hint=float, default=0.0, optional=True),
        DataIn("Jitter", type_hint=float, default=0.0, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]
    i18n = {
        "pt-BR": {
            "category": "Dispositivos/Virtual/Gerador de Sinal",
            "display_name": "Configurar Onda VirtSigGen",
            "description": "Configura a forma de onda, frequência, amplitude, offset, fase e ciclo de trabalho de um dispositivo VirtSigGen.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "WaveType": "Tipo de Onda",
                "Frequency": "Frequência",
                "Amplitude": "Amplitude",
                "Offset": "Offset",
                "Phase": "Fase",
                "DutyCycle": "Ciclo de Trabalho",
                "Noise": "Ruído",
                "Jitter": "Jitter",
                "Out": "Saída"
            }
        },
        "es": {
            "category": "Dispositivos/Virtual/Generador de Señales",
            "display_name": "Configurar Onda VirtSigGen",
            "description": "Configura la forma de onda, frecuencia, amplitud, offset, fase y ciclo de trabajo de un dispositivo VirtSigGen.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "WaveType": "Tipo de Onda",
                "Frequency": "Frecuencia",
                "Amplitude": "Amplitud",
                "Offset": "Offset",
                "Phase": "Fase",
                "DutyCycle": "Ciclo de Trabajo",
                "Noise": "Ruido",
                "Jitter": "Jitter",
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
        wave_type = await context.pull(self.id, "WaveType")
        shape = await context.pull(self.id, "Shape")
        frequency = await context.pull(self.id, "Frequency")
        amplitude = await context.pull(self.id, "Amplitude")
        offset = await context.pull(self.id, "Offset")
        phase = await context.pull(self.id, "Phase")
        duty_cycle = await context.pull(self.id, "DutyCycle")
        noise = await context.pull(self.id, "Noise")
        jitter = await context.pull(self.id, "Jitter")

        target_wave = wave_type if wave_type is not None else shape

        async with locked_device(context, device, "VirtSigGen Config Wave"):
            if target_wave:
                w_str = str(target_wave).lower()
                if w_str in ("sawtooth", "ramp"):
                    func_name = "RAMP"
                elif w_str == "sine":
                    func_name = "SINUSOID"
                elif w_str == "square":
                    func_name = "SQUARE"
                elif w_str == "triangle":
                    func_name = "TRIANGLE"
                elif w_str == "pulse":
                    func_name = "PULSE"
                elif w_str == "rsaw":
                    func_name = "RSAW"
                else:
                    func_name = w_str.upper()
                await asyncio.to_thread(device.write, f":SOURce1:FUNCtion {func_name}")

            if frequency is not None:
                await asyncio.to_thread(device.write, f":SOURce1:FREQuency {frequency}")

            if amplitude is not None:
                await asyncio.to_thread(device.write, f":SOURce1:VOLTage {amplitude}")

            if offset is not None:
                await asyncio.to_thread(device.write, f":SOURce1:VOLTage:OFFSet {offset}")

            if phase is not None:
                await asyncio.to_thread(device.write, f":SOURce1:PHASe {phase}")

            if duty_cycle is not None:
                await asyncio.to_thread(device.write, f":SOURce1:PULSe:DCYCle {duty_cycle}")

            if noise is not None and noise > 0:
                await asyncio.to_thread(device.write, ":SOURce1:NOISe:STATe ON")
                await asyncio.to_thread(device.write, f":SOURce1:NOISe:LEVel {noise}")
            elif noise is not None and noise == 0:
                await asyncio.to_thread(device.write, ":SOURce1:NOISe:STATe OFF")

            if jitter is not None:
                await asyncio.to_thread(device.write, f":SOURce1:JITTer {jitter}")

        return "Out"


@register_block("devices/virtual/signal_generator/config_chirp")
class VirtSigGenConfigChirpBlock(BaseBlock):
    """Configures the frequency sweep chirp settings of a VirtSigGen device."""
    icon = "📈"
    display_name = "VirtSigGen Config Chirp"
    description = "Configures trigger chirp state, frequency sweep variation span, and period of a VirtSigGen device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Chirp", type_hint=bool, default=False, widget="checkbox"),
        DataIn("Variation", type_hint=float, default=100.0, optional=True),
        DataIn("Period", type_hint=float, default=1.0, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]
    i18n = {
        "pt-BR": {
            "category": "Dispositivos/Virtual/Gerador de Sinal",
            "display_name": "Configurar Chirp VirtSigGen",
            "description": "Configura o estado do chirp, span de variação de frequência e período de um dispositivo VirtSigGen.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Chirp": "Chirp",
                "Variation": "Variação",
                "Period": "Período",
                "Out": "Saída"
            }
        },
        "es": {
            "category": "Dispositivos/Virtual/Generador de Señales",
            "display_name": "Configurar Chirp VirtSigGen",
            "description": "Configura el estado de chirp del trigger, el span de variación de frecuencia y el período de un dispositivo VirtSigGen.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Chirp": "Chirp",
                "Variation": "Variación",
                "Period": "Período",
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
        chirp = await context.pull(self.id, "Chirp")
        variation = await context.pull(self.id, "Variation")
        period = await context.pull(self.id, "Period")

        async with locked_device(context, device, "VirtSigGen Config Chirp"):
            chirp_str = "ON" if chirp else "OFF"
            await asyncio.to_thread(device.write, f":SOURce1:FREQuency:CHIRp {chirp_str}")

            if variation is not None:
                await asyncio.to_thread(device.write, f":SOURce1:FREQuency:CVAR {variation}")

            if period is not None:
                await asyncio.to_thread(device.write, f":SOURce1:FREQuency:CPER {period}")

        return "Out"


@register_block("devices/virtual/signal_generator/output")
class VirtSigGenOutputBlock(BaseBlock):
    """Enables or disables output signal transmission of a VirtSigGen device."""
    icon = "🔘"
    display_name = "VirtSigGen Output"
    description = "Enables or disables output state (ON/OFF) of a VirtSigGen device."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]
    i18n = {
        "pt-BR": {
            "category": "Dispositivos/Virtual/Gerador de Sinal",
            "display_name": "Saída VirtSigGen",
            "description": "Habilita ou desabilita o estado de saída (ON/OFF) de um dispositivo VirtSigGen.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Enable": "Habilitar",
                "Out": "Saída"
            }
        },
        "es": {
            "category": "Dispositivos/Virtual/Generador de Señales",
            "display_name": "Salida VirtSigGen",
            "description": "Habilita o deshabilita el estado de salida (ON/OFF) de un dispositivo VirtSigGen.",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Enable": "Habilitar",
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
        enable = await context.pull(self.id, "Enable")
        output = await context.pull(self.id, "Output")

        target_out = enable if enable is not None else output
        if target_out is None:
            target_out = True

        async with locked_device(context, device, "VirtSigGen Output"):
            state_str = "ON" if target_out else "OFF"
            await asyncio.to_thread(device.write, f":OUTPut1:STATe {state_str}")

        return "Out"
