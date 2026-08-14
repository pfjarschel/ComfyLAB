# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import ast
import time
import logging
from typing import Any, Optional
from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext

logger = logging.getLogger("comfylab.blocks.utility")


@register_block("utility/passthrough")
class PassthroughBlock(BaseBlock):
    """Passes input data directly to output. Useful for organizing wires."""
    icon = "➔"
    display_name = "Passthrough"
    description = "Passes input data directly to output. Useful for organizing wires."
    default_width = 14
    default_height = 14
    is_passthrough = True

    inputs_def = [
        DataIn("In", type_hint=Any)
    ]
    outputs_def = [
        DataOut("Out", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Passagem Direta",
            "description": "Passa os dados de entrada diretamente para a saída. Útil para organizar fios.",
            "category": "Utilidade",
            "pins": {
                "In": "Entrada",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Paso Directo",
            "description": "Pasa los datos de entrada directamente a la salida. Útil para organizar cables.",
            "category": "Utilidad",
            "pins": {
                "In": "Entrada",
                "Out": "Salida"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Out":
            return await context.pull(self.id, "In")
        return None


@register_block("utility/exec_passthrough")
class ExecPassthroughBlock(BaseBlock):
    """Passes execution trigger directly to output. Useful for organizing exec wires."""
    icon = "➜"
    display_name = "Exec Passthrough"
    description = "Passes execution trigger directly to output. Useful for organizing exec wires."
    default_width = 14
    default_height = 14
    is_passthrough = True

    inputs_def = [
        ExecIn("In")
    ]
    outputs_def = [
        ExecOut("Out")
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Passagem de Execução",
            "description": "Passa o gatilho de execução diretamente para a saída. Útil para organizar fios de execução.",
            "category": "Utilidade",
            "pins": {
                "In": "Entrada",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Paso de Ejecución",
            "description": "Pasa el gatillo de ejecución directamente a la salida. Útil para organizar cables de ejecución.",
            "category": "Utilidad",
            "pins": {
                "In": "Entrada",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if trigger_pin == "In":
            return "Out"
        return None


@register_block("utility/sample_and_hold")
class SampleAndHoldBlock(BaseBlock):
    """Latches and holds a value when triggered."""
    icon = "📥"
    display_name = "Sample & Hold"
    description = "Latches onto a data value when triggered and holds that value steady until triggered again."
    
    inputs_def = [
        ExecIn("Sample"),
        DataIn("Data", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Held Value", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Amostra e Retém",
            "description": "Trava um valor de dados quando ativado e o mantém constante até ser ativado novamente.",
            "category": "Utilidade",
            "pins": {
                "Sample": "Amostra",
                "Data": "Dados",
                "Out": "Saída",
                "Held Value": "Valor Retido"
            }
        },
        "es": {
            "display_name": "Muestra y Retiene",
            "description": "Bloquea un valor de datos cuando se activa y lo mantiene constante hasta que se activa nuevamente.",
            "category": "Utilidad",
            "pins": {
                "Sample": "Muestra",
                "Data": "Datos",
                "Out": "Salida",
                "Held Value": "Valor Retenido"
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._held_value = None

    async def execute(self, context: ExecutionContext, pin_name: str):
        if pin_name == "Sample":
            self._held_value = await context.pull(self.id, "Data")
            await context.send_telemetry(self.id, {"held_value": self._held_value})
            return "Out"
        return None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Held Value":
            return self._held_value
        return None


@register_block("utility/sequencer")
class SequencerBlock(BaseBlock):
    """Steps through a list sequence on each trigger."""
    icon = "🪜"
    display_name = "Sequencer"
    description = "Steps through a sequence array on each trigger, outputting the current element. Wraps around when it reaches the end."
    
    inputs_def = [
        ExecIn("Step"),
        DataIn("Sequence", type_hint=list, default=[])
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Current", type_hint=Any),
        DataOut("Index", type_hint=int)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Sequenciador",
            "description": "Avança em uma matriz de sequência a cada gatilho, emitindo o elemento atual. Recomeça quando chega ao fim.",
            "category": "Utilidade",
            "pins": {
                "Step": "Avançar",
                "Sequence": "Sequência",
                "Out": "Saída",
                "Current": "Atual",
                "Index": "Índice"
            }
        },
        "es": {
            "display_name": "Secuenciador",
            "description": "Avanza en una matriz de secuencia en cada gatillo, emitiendo el elemento actual. Vuelve al inicio al llegar al final.",
            "category": "Utilidad",
            "pins": {
                "Step": "Avanzar",
                "Sequence": "Secuencia",
                "Out": "Salida",
                "Current": "Actual",
                "Index": "Índice"
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._index = -1
        self._current_value = None
        self._seq_len = 0

    async def execute(self, context: ExecutionContext, pin_name: str):
        if pin_name == "Step":
            seq = await context.pull(self.id, "Sequence")
            
            if isinstance(seq, str):
                try:
                    parsed = ast.literal_eval(seq)
                    if isinstance(parsed, (list, tuple)):
                        seq = parsed
                    else:
                        seq = [s.strip() for s in seq.split(",") if s.strip()]
                except Exception:
                    seq = [s.strip() for s in seq.split(",") if s.strip()]

            if seq is not None and hasattr(seq, '__iter__') and not isinstance(seq, (str, bytes)):
                try:
                    seq = list(seq)
                    self._seq_len = len(seq)
                    if self._seq_len > 0:
                        self._index = (self._index + 1) % self._seq_len
                        self._current_value = seq[self._index]

                        await context.send_telemetry(self.id, {"index": self._index, "value": self._current_value})
                except Exception as e:
                    logger.error(f"Sequencer iteration failed: {e}")
            else:
                logger.warning(f"Sequencer received invalid sequence: {type(seq)} - {seq}")
            
            return "Out"
        return None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Current":
            return self._current_value
        elif pin_name == "Index":
            return self._index
        return None


@register_block("utility/beep")
class BeepBlock(BaseBlock):
    """Plays an audio beep in the UI."""
    icon = "🔊"
    display_name = "Beep / Alarm"
    description = "Triggers a synthesized audio tone in the browser UI when executed."
    ui_behavior = {"custom_widget": "beep_widget", "render_standard_inputs": True}
    
    inputs_def = [
        ExecIn("Play"),
        DataIn("Sound Type", type_hint=str, default="sine", options=["sine", "square", "sawtooth", "triangle"], widget="dropdown"),
        DataIn("Frequency", type_hint=float, default=440.0, widget="number"),
        DataIn("Duration (ms)", type_hint=float, default=200.0, widget="number"),
        DataIn("Volume", type_hint=float, default=1.0, widget="number")
    ]
    outputs_def = [
        ExecOut("Out")
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Bipe / Alarme",
            "description": "Aciona um tom de áudio sintetizado na interface do navegador quando executado.",
            "category": "Utilidade",
            "pins": {
                "Play": "Tocar",
                "Sound Type": "Tipo de Som",
                "Frequency": "Frequência",
                "Duration (ms)": "Duração (ms)",
                "Volume": "Volume",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Bip / Alarma",
            "description": "Activa un tono de audio sintetizado en la interfaz del navegador cuando se ejecuta.",
            "category": "Utilidad",
            "pins": {
                "Play": "Tocar",
                "Sound Type": "Tipo de Sonido",
                "Frequency": "Frecuencia",
                "Duration (ms)": "Duración (ms)",
                "Volume": "Volumen",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, pin_name: str):
        if pin_name == "Play":
            sound_type = await context.pull(self.id, "Sound Type")
            freq = await context.pull(self.id, "Frequency")
            dur = await context.pull(self.id, "Duration (ms)")
            vol = await context.pull(self.id, "Volume")
            
            payload = {
                "action": "play_beep",
                "type": sound_type or "sine",
                "frequency": float(freq) if freq is not None else 440.0,
                "duration": float(dur) if dur is not None else 200.0,
                "volume": float(vol) if vol is not None else 1.0,
                "timestamp": time.time()
            }
            await context.send_telemetry(self.id, payload)
            return "Out"
        return None
