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
from comfylab.devices.caen.dt5720b import CAENDT5720B


@register_block("devices/caen/dt5720b/connect")
class CAENDT5720BConnectBlock(BaseBlock):
    """Opens a connection to a CAEN DT5720B 4-Channel 250 MS/s 12-bit Desktop Digitizer."""
    icon = "⚡"
    display_name = "CAEN DT5720B Digitizer Connect"
    description = "Opens a connection to a CAEN DT5720B digitizer via USB or Optical Link."

    inputs_def = [
        ExecIn("Open"),
        DataIn("LinkType", type_hint=int, default=0, widget="dropdown", options=[0, 1]),
        DataIn("LinkNum", type_hint=int, default=0),
        DataIn("ConetNode", type_hint=int, default=0),
        DataIn("Simulate", type_hint=bool, default=False, widget="checkbox", optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/CAEN",
            "display_name": "Conectar Digitalizador CAEN DT5720B",
            "description": "Abre conexão com o digitalizador CAEN DT5720B (4 canais, 250 MS/s, 12 bits) via USB ou Link Óptico.",
            "pins": {
                "Open": "Abrir",
                "LinkType": "Tipo de Link (0: USB, 1: Óptico)",
                "LinkNum": "Número do Link",
                "ConetNode": "Nó Conet",
                "Simulate": "Simular",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "category": "Instrumentos/CAEN",
            "display_name": "Conectar Digitalizador CAEN DT5720B",
            "description": "Abre conexión con el digitalizador CAEN DT5720B (4 canales, 250 MS/s, 12 bits) vía USB o Enlace Óptico.",
            "pins": {
                "Open": "Abrir",
                "LinkType": "Tipo de Enlace (0: USB, 1: Óptico)",
                "LinkNum": "Número de Enlace",
                "ConetNode": "Nodo Conet",
                "Simulate": "Simular",
                "Out": "Salida",
                "Device": "Dispositivo"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._device: Optional[CAENDT5720B] = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        link_type = await context.pull(self.id, "LinkType")
        link_num = await context.pull(self.id, "LinkNum")
        conet_node = await context.pull(self.id, "ConetNode")
        simulate = await context.pull(self.id, "Simulate")

        self._device = CAENDT5720B(simulate=bool(simulate))
        await asyncio.to_thread(
            self._device.open,
            link_type=int(link_type) if link_type is not None else 0,
            link_num=int(link_num) if link_num is not None else 0,
            conet_node=int(conet_node) if conet_node is not None else 0,
            simulate=bool(simulate)
        )

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


@register_block("devices/caen/dt5720b/configure")
class CAENDT5720BConfigBlock(BaseBlock):
    """Configures record length (samples), post-trigger percentage, and dynamic range on a CAEN DT5720B."""
    icon = "⚙️"
    display_name = "CAEN DT5720B Configure"
    description = "Sets record length (samples), post-trigger size (%), and acquisition parameters."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("RecordLength", type_hint=int, default=1024),
        DataIn("PostTriggerPct", type_hint=float, default=50.0),
        DataIn("DynamicRange_Vpp", type_hint=float, default=2.0, widget="dropdown", options=[2.0, 0.5])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/CAEN",
            "display_name": "Configurar CAEN DT5720B",
            "description": "Configura o tamanho do registro (amostras), pós-disparo (%) e faixa dinâmica (2.0 Vpp / 0.5 Vpp).",
            "pins": {
                "Device": "Dispositivo",
                "RecordLength": "Tamanho Registro",
                "PostTriggerPct": "Pós-Disparo (%)",
                "DynamicRange_Vpp": "Faixa Dinâmica (Vpp)"
            }
        },
        "es": {
            "category": "Instrumentos/CAEN",
            "display_name": "Configurar CAEN DT5720B",
            "description": "Configura el tamaño de registro (muestras), post-disparo (%) y rango dinámico (2.0 Vpp / 0.5 Vpp).",
            "pins": {
                "Device": "Dispositivo",
                "RecordLength": "Tamaño Registro",
                "PostTriggerPct": "Post-Disparo (%)",
                "DynamicRange_Vpp": "Rango Dinámico (Vpp)"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        rec_len = await context.pull(self.id, "RecordLength")
        post_trig = await context.pull(self.id, "PostTriggerPct")
        vpp = await context.pull(self.id, "DynamicRange_Vpp")

        if isinstance(device, CAENDT5720B):
            if rec_len is not None:
                await asyncio.to_thread(device.set_record_length, int(rec_len))
            if post_trig is not None:
                await asyncio.to_thread(device.set_post_trigger_size, float(post_trig))
            if vpp is not None:
                for ch in range(device.NUM_CHANNELS):
                    await asyncio.to_thread(device.set_channel, ch, dynamic_range_vpp=float(vpp))

        return "Out"


@register_block("devices/caen/dt5720b/channel")
class CAENDT5720BChannelBlock(BaseBlock):
    """Configures individual channel settings (enable, DC offset, trigger threshold, slope) on a CAEN DT5720B."""
    icon = "📶"
    display_name = "CAEN DT5720B Channel"
    description = "Configures channel enable, DC offset (%), trigger threshold DAC (0-4095), and slope."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=0, widget="dropdown", options=[0, 1, 2, 3]),
        DataIn("Enable", type_hint=bool, default=True, widget="checkbox"),
        DataIn("DCOffsetPct", type_hint=float, default=50.0, optional=True),
        DataIn("TriggerThresholdDAC", type_hint=int, default=2000, optional=True),
        DataIn("TriggerSlope", type_hint=str, default="FALLING", widget="dropdown", options=["FALLING", "RISING"], optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/CAEN",
            "display_name": "Canal CAEN DT5720B",
            "description": "Configura ativação do canal, offset DC (%), limiar de disparo do DAC (0-4095) e borda no CAEN DT5720B.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Enable": "Habilitar",
                "DCOffsetPct": "Offset DC (%)",
                "TriggerThresholdDAC": "Limiar Disparo (DAC)",
                "TriggerSlope": "Borda Disparo"
            }
        },
        "es": {
            "category": "Instrumentos/CAEN",
            "display_name": "Canal CAEN DT5720B",
            "description": "Configura activación del canal, offset DC (%), umbral de disparo DAC (0-4095) y flanco en CAEN DT5720B.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Enable": "Habilitar",
                "DCOffsetPct": "Offset DC (%)",
                "TriggerThresholdDAC": "Umbral Disparo (DAC)",
                "TriggerSlope": "Flanco Disparo"
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
        dc_offset = await context.pull(self.id, "DCOffsetPct")
        threshold = await context.pull(self.id, "TriggerThresholdDAC")
        slope = await context.pull(self.id, "TriggerSlope")

        if isinstance(device, CAENDT5720B):
            await asyncio.to_thread(
                device.set_channel,
                int(channel),
                enable,
                dc_offset,
                threshold,
                slope
            )

        return "Out"


@register_block("devices/caen/dt5720b/acquire")
class CAENDT5720BAcquireBlock(BaseBlock):
    """Acquires a pulse waveform event from a CAEN DT5720B digitizer channel."""
    icon = "📥"
    display_name = "CAEN DT5720B Acquire"
    description = "Triggers acquisition and reads raw pulse waveform arrays (Time & Voltage) with telemetry streaming."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Channel", type_hint=int, default=0, widget="dropdown", options=[0, 1, 2, 3])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Waveform", type_hint=np.ndarray),
        DataOut("Time", type_hint=np.ndarray),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/CAEN",
            "display_name": "Adquirir CAEN DT5720B",
            "description": "Aciona e lê as formas de onda de pulsos (Tempo e Tensão) no CAEN DT5720B com transmissão de telemetria.",
            "pins": {
                "Device": "Dispositivo",
                "Channel": "Canal",
                "Waveform": "Forma de Onda",
                "Time": "Tempo"
            }
        },
        "es": {
            "category": "Instrumentos/CAEN",
            "display_name": "Adquirir CAEN DT5720B",
            "description": "Activa y lee las formas de onda de pulsos (Tiempo y Voltaje) en CAEN DT5720B con transmisión de telemetría.",
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

        if isinstance(device, CAENDT5720B):
            t_vec, v_vec = await asyncio.to_thread(device.acquire_event, int(channel))
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


@register_block("devices/caen/dt5720b/pulse_stats")
class CAENDT5720BPulseStatsBlock(BaseBlock):
    """Calculates pulse physical properties (Peak Amplitude, Baseline, Integral Area, Rise Time, FWHM) from digitizer waveform."""
    icon = "📊"
    display_name = "CAEN DT5720B Pulse Stats"
    description = "Calculates pulse peak amplitude (V), baseline (V), charge integral (V*s), rise time (s), and FWHM (s)."

    inputs_def = [
        ExecIn("In"),
        DataIn("Time", type_hint=np.ndarray),
        DataIn("Waveform", type_hint=np.ndarray)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Amplitude", type_hint=float),
        DataOut("Baseline", type_hint=float),
        DataOut("PulseArea", type_hint=float),
        DataOut("RiseTime", type_hint=float),
        DataOut("FWHM", type_hint=float)
    ]

    i18n = {
        "pt-BR": {
            "category": "Instrumentos/CAEN",
            "display_name": "Estatísticas de Pulso CAEN DT5720B",
            "description": "Calcula amplitude de pico (V), linha de base (V), integral de carga/área (V·s), tempo de subida (s) e FWHM (s).",
            "pins": {
                "Time": "Tempo",
                "Waveform": "Forma de Onda",
                "Amplitude": "Amplitude",
                "Baseline": "Linha de Base",
                "PulseArea": "Área do Pulso",
                "RiseTime": "Tempo Subida",
                "FWHM": "FWHM"
            }
        },
        "es": {
            "category": "Instrumentos/CAEN",
            "display_name": "Estadísticas de Pulso CAEN DT5720B",
            "description": "Calcula amplitud de pico (V), línea de base (V), integral de carga/área (V·s), tiempo de subida (s) y FWHM (s).",
            "pins": {
                "Time": "Tiempo",
                "Waveform": "Forma de Onda",
                "Amplitude": "Amplitud",
                "Baseline": "Línea de Base",
                "PulseArea": "Área del Pulso",
                "RiseTime": "Tiempo Subida",
                "FWHM": "FWHM"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._amplitude: float = 0.0
        self._baseline: float = 0.0
        self._pulse_area: float = 0.0
        self._rise_time: float = 0.0
        self._fwhm: float = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        t_vec = await context.pull(self.id, "Time")
        v_vec = await context.pull(self.id, "Waveform")

        if isinstance(t_vec, np.ndarray) and isinstance(v_vec, np.ndarray) and len(v_vec) > 0:
            stats = CAENDT5720B.calculate_pulse_stats(t_vec, v_vec)
            self._amplitude = stats["peak_amplitude"]
            self._baseline = stats["baseline"]
            self._pulse_area = stats["pulse_area"]
            self._rise_time = stats["rise_time"]
            self._fwhm = stats["fwhm"]

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Amplitude":
            return self._amplitude
        elif pin_name == "Baseline":
            return self._baseline
        elif pin_name == "PulseArea":
            return self._pulse_area
        elif pin_name == "RiseTime":
            return self._rise_time
        elif pin_name == "FWHM":
            return self._fwhm
        return None
