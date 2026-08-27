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

import logging
from typing import Optional
import time
import numpy as np
import scipy.ndimage as ndimage

logger = logging.getLogger("comfylab.blocks.plots")

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, ExecutionContext


@register_block("outputs/plots/xy_plot")
class XYPlotBlock(BaseBlock):
    """Receives X and Y array data and streams them to the UI for XY graphing."""
    icon = "📊"
    display_name = "XY Plot"
    description = "Receives X and Y data lists and streams them to the UI for XY plotting."
    default_width = 300
    default_height = 300
    ui_behavior = {"custom_widget": "xy_plot", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("X", type_hint=np.ndarray),
        DataIn("Y", type_hint=np.ndarray),
        DataIn("XLabel", type_hint=str, default="X", optional=True),
        DataIn("YLabel", type_hint=str, default="Y", optional=True),
        DataIn("Labels", type_hint=list, optional=True),
        DataIn("XMin", type_hint=float, optional=True),
        DataIn("XMax", type_hint=float, optional=True),
        DataIn("YMin", type_hint=float, optional=True),
        DataIn("YMax", type_hint=float, optional=True),
        DataIn("XLog", type_hint=bool, default=False, widget="checkbox", optional=True),
        DataIn("YLog", type_hint=bool, default=False, widget="checkbox", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Gráfico XY",
            "description": "Recebe listas de dados X e Y e os envia para a interface para plotagem XY.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Plotar",
                "XLabel": "Rótulo X",
                "YLabel": "Rótulo Y",
                "Labels": "Rótulos",
                "XMin": "X Mín",
                "XMax": "X Máx",
                "YMin": "Y Mín",
                "YMax": "Y Máx",
                "XLog": "X Log",
                "YLog": "Y Log",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Gráfico XY",
            "description": "Recibe listas de datos X e Y y los envía a la interfaz para graficar XY.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Graficar",
                "XLabel": "Etiqueta X",
                "YLabel": "Etiqueta Y",
                "Labels": "Etiquetas",
                "XMin": "X Mín",
                "XMax": "X Máx",
                "YMin": "Y Mín",
                "YMax": "Y Máx",
                "XLog": "X Log",
                "YLog": "Y Log",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        x = await context.pull(self.id, "X")
        y = await context.pull(self.id, "Y")
        x_label = await context.pull(self.id, "XLabel")
        y_label = await context.pull(self.id, "YLabel")

        # Convert to list for JSON serialization
        x_list = x.tolist() if isinstance(x, np.ndarray) else (x if isinstance(x, list) else [])
        y_list = y.tolist() if isinstance(y, np.ndarray) else (y if isinstance(y, list) else [])
        
        labels = await context.pull(self.id, "Labels")
        labels_list = labels.tolist() if isinstance(labels, np.ndarray) else (labels if isinstance(labels, list) else None)

        x_min = await context.pull(self.id, "XMin")
        x_max = await context.pull(self.id, "XMax")
        y_min = await context.pull(self.id, "YMin")
        y_max = await context.pull(self.id, "YMax")
        x_log = await context.pull(self.id, "XLog")
        y_log = await context.pull(self.id, "YLog")

        # Send telemetry payload
        payload = {
            "x": x_list,
            "y": y_list,
            "x_label": str(x_label) if x_label else "X",
            "y_label": str(y_label) if y_label else "Y",
            "x_min": float(x_min) if x_min is not None else None,
            "x_max": float(x_max) if x_max is not None else None,
            "y_min": float(y_min) if y_min is not None else None,
            "y_max": float(y_max) if y_max is not None else None,
            "x_log": bool(x_log) if x_log is not None else False,
            "y_log": bool(y_log) if y_log is not None else False,
            "labels": labels_list
        }
        await context.send_telemetry(self.id, payload)
        return "Out"


@register_block("outputs/plots/plot")
class PlotBlock(BaseBlock):
    """Receives data values and streams them to the UI for live graphing."""
    icon = "📉"
    display_name = "Time Plot"
    description = "Receives data values and streams them to the UI for live graphing."
    default_width = 210
    default_height = 220
    ui_behavior = {"accumulate_history": True, "custom_widget": "time_plot", "render_standard_inputs": True}
    
    inputs_def = [
        ExecIn("Plot"),
        DataIn("InputData"),
        DataIn("MaxHistory", type_hint=int, default=0, widget="number"),
        DataIn("Labels", type_hint=list, optional=True),
        DataIn("YLabel", type_hint=str, default="Value", optional=True),
        DataIn("UseTime", type_hint=bool, default=False, widget="checkbox"),
        DataIn("XMin", type_hint=float, optional=True),
        DataIn("XMax", type_hint=float, optional=True),
        DataIn("YMin", type_hint=float, optional=True),
        DataIn("YMax", type_hint=float, optional=True),
        DataIn("XLog", type_hint=bool, default=False, widget="checkbox", optional=True),
        DataIn("YLog", type_hint=bool, default=False, widget="checkbox", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Gráfico de Tempo",
            "description": "Recebe valores de dados e os envia para a interface para plotagem ao vivo.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Plotar",
                "InputData": "Dados de Entrada",
                "MaxHistory": "Histórico Máx",
                "Labels": "Rótulos",
                "YLabel": "Rótulo Y",
                "UseTime": "Usar Tempo",
                "XMin": "X Mín",
                "XMax": "X Máx",
                "YMin": "Y Mín",
                "YMax": "Y Máx",
                "XLog": "X Log",
                "YLog": "Y Log",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Gráfico de Tiempo",
            "description": "Recibe valores de datos y los envía a la interfaz para graficar en vivo.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Graficar",
                "InputData": "Datos de Entrada",
                "MaxHistory": "Historial Máx",
                "Labels": "Etiquetas",
                "YLabel": "Etiqueta Y",
                "UseTime": "Usar Tiempo",
                "XMin": "X Mín",
                "XMax": "X Máx",
                "YMin": "Y Mín",
                "YMax": "Y Máx",
                "XLog": "X Log",
                "YLog": "Y Log",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        val = await context.pull(self.id, "InputData")
        max_history = await context.pull(self.id, "MaxHistory")
        
        try:
            max_history = int(max_history) if max_history is not None else 0
        except Exception:
            max_history = 0

        x_min = await context.pull(self.id, "XMin")
        x_max = await context.pull(self.id, "XMax")
        y_min = await context.pull(self.id, "YMin")
        y_max = await context.pull(self.id, "YMax")
        x_log = await context.pull(self.id, "XLog")
        y_log = await context.pull(self.id, "YLog")

        # Convert np.ndarray to list for JSON telemetry serialization
        val_serialized = val.tolist() if isinstance(val, np.ndarray) else val
        
        labels = await context.pull(self.id, "Labels")
        labels_list = labels.tolist() if isinstance(labels, np.ndarray) else (labels if isinstance(labels, list) else None)
        
        y_label = await context.pull(self.id, "YLabel")
        use_time = await context.pull(self.id, "UseTime")
        timestamp = time.time() if use_time else None

        # Send numerical or array telemetry package
        await context.send_telemetry(self.id, {
            "value": val_serialized,
            "max_history": max_history,
            "x_min": float(x_min) if x_min is not None else None,
            "x_max": float(x_max) if x_max is not None else None,
            "y_min": float(y_min) if y_min is not None else None,
            "y_max": float(y_max) if y_max is not None else None,
            "x_log": bool(x_log) if x_log is not None else False,
            "y_log": bool(y_log) if y_log is not None else False,
            "labels": labels_list,
            "y_label": str(y_label) if y_label else "Value",
            "timestamp": timestamp
        })
        return "Out"


@register_block("outputs/plots/heatmap_plot")
class HeatmapPlotBlock(BaseBlock):
    """Receives a 2D array and streams it to the UI for heatmap or contour visualization."""
    icon = "🗺️"
    display_name = "Heatmap Plot"
    description = "Plots a 2D array of values with optional extents and color mapping."
    default_width = 320
    default_height = 340
    ui_behavior = {"custom_widget": "heatmap_plot", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("Z", type_hint=np.ndarray),
        DataIn("X", type_hint=np.ndarray, optional=True),
        DataIn("Y", type_hint=np.ndarray, optional=True),
        DataIn("Colormap", type_hint=str, default="Viridis", widget="dropdown", 
               options=["Plotly3", "Viridis", "Cividis", "Hot", "Inferno", "Turbo", "Agsunset", "Picnic", "Phase", "Greys", "Bluered"]),
        DataIn("XLabel", type_hint=str, default="X", optional=True),
        DataIn("YLabel", type_hint=str, default="Y", optional=True),
        DataIn("ZLabel", type_hint=str, default="Z", optional=True),
        DataIn("PlotType", type_hint=str, default="Heatmap", widget="dropdown",
               options=["Heatmap", "Contour"], optional=True),
        DataIn("Interpolation", type_hint=str, default="None", widget="dropdown",
               options=["None", "Fast (linear)", "Good (bilinear)", "Best (spline36)"], optional=True),
        DataIn("XMin", type_hint=float, optional=True),
        DataIn("XMax", type_hint=float, optional=True),
        DataIn("YMin", type_hint=float, optional=True),
        DataIn("YMax", type_hint=float, optional=True),
        DataIn("ZMin", type_hint=float, optional=True),
        DataIn("ZMax", type_hint=float, optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Mapa de Calor",
            "description": "Plota uma matriz 2D de valores com extensões e mapeamento de cores opcionais.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Plotar",
                "Colormap": "Mapa de Cores",
                "XLabel": "Rótulo X",
                "YLabel": "Rótulo Y",
                "ZLabel": "Rótulo Z",
                "PlotType": "Tipo de Gráfico",
                "Interpolation": "Interpolação",
                "XMin": "X Mín",
                "XMax": "X Máx",
                "YMin": "Y Mín",
                "YMax": "Y Máx",
                "ZMin": "Z Mín",
                "ZMax": "Z Máx",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Mapa de Calor",
            "description": "Grafica una matriz 2D de valores con extensiones y mapeo de colores opcionales.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Graficar",
                "Colormap": "Mapa de Colores",
                "XLabel": "Etiqueta X",
                "YLabel": "Etiqueta Y",
                "ZLabel": "Etiqueta Z",
                "PlotType": "Tipo de Gráfico",
                "Interpolation": "Interpolación",
                "XMin": "X Mín",
                "XMax": "X Máx",
                "YMin": "Y Mín",
                "YMax": "Y Máx",
                "ZMin": "Z Mín",
                "ZMax": "Z Máx",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        z = await context.pull(self.id, "Z")
        x = await context.pull(self.id, "X")
        y = await context.pull(self.id, "Y")
        x_label = await context.pull(self.id, "XLabel")
        y_label = await context.pull(self.id, "YLabel")
        colormap = await context.pull(self.id, "Colormap")
        interpolation = await context.pull(self.id, "Interpolation")
        plot_type = await context.pull(self.id, "PlotType")

        z_out = z.tolist() if isinstance(z, np.ndarray) else (z if isinstance(z, list) else [])
        x_out = x.tolist() if isinstance(x, np.ndarray) else (x if isinstance(x, list) else None)
        y_out = y.tolist() if isinstance(y, np.ndarray) else (y if isinstance(y, list) else None)

        interp_str = str(interpolation) if interpolation else "None"

        if interp_str != "None" and z_out:
            try:
                z_arr = np.array(z_out)
                if z_arr.ndim == 2:
                    scale = 4
                    order = 1
                    if "Good" in interp_str:
                        scale = 6
                        order = 3
                    elif "Best" in interp_str:
                        scale = 8
                        order = 5

                    z_zoomed = ndimage.zoom(z_arr, scale, order=order)
                    z_out = z_zoomed.tolist()

                    if x_out and len(x_out) == z_arr.shape[1]:
                        x_arr = np.array(x_out)
                        x_zoomed = ndimage.zoom(x_arr, scale, order=1)
                        x_out = x_zoomed.tolist()
                    
                    if y_out and len(y_out) == z_arr.shape[0]:
                        y_arr = np.array(y_out)
                        y_zoomed = ndimage.zoom(y_arr, scale, order=1)
                        y_out = y_zoomed.tolist()
            except Exception as e:
                logger.error(f"Error interpolating Heatmap Z array: {e}")

        x_min = await context.pull(self.id, "XMin")
        x_max = await context.pull(self.id, "XMax")
        y_min = await context.pull(self.id, "YMin")
        y_max = await context.pull(self.id, "YMax")
        z_min = await context.pull(self.id, "ZMin")
        z_max = await context.pull(self.id, "ZMax")
        z_label = await context.pull(self.id, "ZLabel")

        payload = {
            "z": z_out,
            "x": x_out,
            "y": y_out,
            "x_label": str(x_label) if x_label else "X",
            "y_label": str(y_label) if y_label else "Y",
            "colormap": str(colormap) if colormap else "Viridis",
            "interpolation": "False", # Tell frontend not to smooth it since we pre-smoothed it
            "plot_type": str(plot_type) if plot_type else "Heatmap",
            "x_min": float(x_min) if x_min is not None else None,
            "x_max": float(x_max) if x_max is not None else None,
            "y_min": float(y_min) if y_min is not None else None,
            "y_max": float(y_max) if y_max is not None else None,
            "z_min": float(z_min) if z_min is not None else None,
            "z_max": float(z_max) if z_max is not None else None,
            "z_label": str(z_label) if z_label else "Z"
        }
        await context.send_telemetry(self.id, payload)
        return "Out"


@register_block("outputs/plots/histogram_plot")
class HistogramPlotBlock(BaseBlock):
    """Receives 1D or 2D array data and streams it to the UI for statistical histogram plotting."""
    icon = "📶"
    display_name = "Histogram Plot"
    description = "Plots statistical frequency distributions with configurable bins, bin size, and normalization."
    default_width = 300
    default_height = 300
    ui_behavior = {"custom_widget": "histogram_plot", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("Data", type_hint=np.ndarray),
        DataIn("Bins", type_hint=int, default=0, widget="number", optional=True),
        DataIn("BinSize", type_hint=float, widget="number", optional=True),
        DataIn("BinMin", type_hint=float, optional=True),
        DataIn("BinMax", type_hint=float, optional=True),
        DataIn("Normalization", type_hint=str, default="Count", widget="dropdown",
               options=["Count", "Percent", "Probability", "Density", "Probability Density"], optional=True),
        DataIn("Cumulative", type_hint=bool, default=False, widget="checkbox", optional=True),
        DataIn("BarMode", type_hint=str, default="Overlay", widget="dropdown",
               options=["Overlay", "Group", "Stack"], optional=True),
        DataIn("Labels", type_hint=list, optional=True),
        DataIn("XLabel", type_hint=str, default="Value", optional=True),
        DataIn("YLabel", type_hint=str, default="Count", optional=True),
        DataIn("ShowStats", type_hint=bool, default=False, widget="checkbox", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Histograma",
            "description": "Plota distribuições de frequência estatística com intervalos, tamanho de intervalo e normalização configuráveis.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Plotar",
                "Data": "Dados",
                "Bins": "Intervalos (Bins)",
                "BinSize": "Tam. Intervalo",
                "BinMin": "Mín Intervalo",
                "BinMax": "Máx Intervalo",
                "Normalization": "Normalização",
                "Cumulative": "Cumulativo",
                "BarMode": "Modo de Barras",
                "Labels": "Rótulos",
                "XLabel": "Rótulo X",
                "YLabel": "Rótulo Y",
                "ShowStats": "Mostrar Estatísticas",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Histograma",
            "description": "Grafica distribuciones de frecuencia estadística con intervalos, tamaño y normalización configurables.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Graficar",
                "Data": "Datos",
                "Bins": "Intervalos (Bins)",
                "BinSize": "Tam. Intervalo",
                "BinMin": "Mín Intervalo",
                "BinMax": "Máx Intervalo",
                "Normalization": "Normalización",
                "Cumulative": "Acumulativo",
                "BarMode": "Modo de Barras",
                "Labels": "Etiquetas",
                "XLabel": "Etiqueta X",
                "YLabel": "Etiqueta Y",
                "ShowStats": "Mostrar Estadísticas",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        raw_data = await context.pull(self.id, "Data")
        bins = await context.pull(self.id, "Bins")
        bin_size = await context.pull(self.id, "BinSize")
        bin_min = await context.pull(self.id, "BinMin")
        bin_max = await context.pull(self.id, "BinMax")
        norm = await context.pull(self.id, "Normalization")
        cumulative = await context.pull(self.id, "Cumulative")
        barmode = await context.pull(self.id, "BarMode")
        labels = await context.pull(self.id, "Labels")
        x_label = await context.pull(self.id, "XLabel")
        y_label = await context.pull(self.id, "YLabel")
        show_stats = await context.pull(self.id, "ShowStats")

        data_list = raw_data.tolist() if isinstance(raw_data, np.ndarray) else (raw_data if isinstance(raw_data, list) else [])
        labels_list = labels.tolist() if isinstance(labels, np.ndarray) else (labels if isinstance(labels, list) else None)

        payload = {
            "data": data_list,
            "bins": int(bins) if bins is not None and int(bins) > 0 else None,
            "bin_size": float(bin_size) if bin_size is not None and float(bin_size) > 0 else None,
            "bin_min": float(bin_min) if bin_min is not None else None,
            "bin_max": float(bin_max) if bin_max is not None else None,
            "normalization": str(norm) if norm else "Count",
            "cumulative": bool(cumulative) if cumulative is not None else False,
            "barmode": str(barmode).lower() if barmode else "overlay",
            "labels": labels_list,
            "x_label": str(x_label) if x_label else "Value",
            "y_label": str(y_label) if y_label else "Count",
            "show_stats": bool(show_stats) if show_stats is not None else False
        }
        await context.send_telemetry(self.id, payload)
        return "Out"


@register_block("outputs/plots/dual_y_plot")
class DualYPlotBlock(BaseBlock):
    """Plots two signals with different units/scales on independent left and right Y-axes against a shared X-axis."""
    icon = "📈"
    display_name = "Dual Y-Axis Plot"
    description = "Plots two separate Y series with independent left and right Y scales over a shared X axis."
    default_width = 320
    default_height = 300
    ui_behavior = {"custom_widget": "dual_y_plot", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("X", type_hint=np.ndarray),
        DataIn("Y1", type_hint=np.ndarray),
        DataIn("Y2", type_hint=np.ndarray),
        DataIn("XLabel", type_hint=str, default="X", optional=True),
        DataIn("Y1Label", type_hint=str, default="Y1", optional=True),
        DataIn("Y2Label", type_hint=str, default="Y2", optional=True),
        DataIn("Y1TraceName", type_hint=str, default="Signal 1", optional=True),
        DataIn("Y2TraceName", type_hint=str, default="Signal 2", optional=True),
        DataIn("XMin", type_hint=float, optional=True),
        DataIn("XMax", type_hint=float, optional=True),
        DataIn("Y1Min", type_hint=float, optional=True),
        DataIn("Y1Max", type_hint=float, optional=True),
        DataIn("Y2Min", type_hint=float, optional=True),
        DataIn("Y2Max", type_hint=float, optional=True),
        DataIn("XLog", type_hint=bool, default=False, widget="checkbox", optional=True),
        DataIn("Y1Log", type_hint=bool, default=False, widget="checkbox", optional=True),
        DataIn("Y2Log", type_hint=bool, default=False, widget="checkbox", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Gráfico de Eixo Y Duplo",
            "description": "Plota duas séries Y separadas com escalas Y esquerda e direita independentes sobre um eixo X compartilhado.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Plotar",
                "X": "X",
                "Y1": "Y1",
                "Y2": "Y2",
                "XLabel": "Rótulo X",
                "Y1Label": "Rótulo Y1",
                "Y2Label": "Rótulo Y2",
                "Y1TraceName": "Nome Sinal 1",
                "Y2TraceName": "Nome Sinal 2",
                "XMin": "X Mín",
                "XMax": "X Máx",
                "Y1Min": "Y1 Mín",
                "Y1Max": "Y1 Máx",
                "Y2Min": "Y2 Mín",
                "Y2Max": "Y2 Máx",
                "XLog": "X Log",
                "Y1Log": "Y1 Log",
                "Y2Log": "Y2 Log",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Gráfico de Doble Eje Y",
            "description": "Grafica dos series Y separadas con escalas Y izquierda y derecha independientes sobre un eje X compartido.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Graficar",
                "X": "X",
                "Y1": "Y1",
                "Y2": "Y2",
                "XLabel": "Etiqueta X",
                "Y1Label": "Etiqueta Y1",
                "Y2Label": "Etiqueta Y2",
                "Y1TraceName": "Nombre Señal 1",
                "Y2TraceName": "Nombre Señal 2",
                "XMin": "X Mín",
                "XMax": "X Máx",
                "Y1Min": "Y1 Mín",
                "Y1Max": "Y1 Máx",
                "Y2Min": "Y2 Mín",
                "Y2Max": "Y2 Máx",
                "XLog": "X Log",
                "Y1Log": "Y1 Log",
                "Y2Log": "Y2 Log",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        x = await context.pull(self.id, "X")
        y1 = await context.pull(self.id, "Y1")
        y2 = await context.pull(self.id, "Y2")
        x_label = await context.pull(self.id, "XLabel")
        y1_label = await context.pull(self.id, "Y1Label")
        y2_label = await context.pull(self.id, "Y2Label")
        y1_name = await context.pull(self.id, "Y1TraceName")
        y2_name = await context.pull(self.id, "Y2TraceName")
        x_min = await context.pull(self.id, "XMin")
        x_max = await context.pull(self.id, "XMax")
        y1_min = await context.pull(self.id, "Y1Min")
        y1_max = await context.pull(self.id, "Y1Max")
        y2_min = await context.pull(self.id, "Y2Min")
        y2_max = await context.pull(self.id, "Y2Max")
        x_log = await context.pull(self.id, "XLog")
        y1_log = await context.pull(self.id, "Y1Log")
        y2_log = await context.pull(self.id, "Y2Log")

        x_list = x.tolist() if isinstance(x, np.ndarray) else (x if isinstance(x, list) else [])
        y1_list = y1.tolist() if isinstance(y1, np.ndarray) else (y1 if isinstance(y1, list) else [])
        y2_list = y2.tolist() if isinstance(y2, np.ndarray) else (y2 if isinstance(y2, list) else [])

        payload = {
            "x": x_list,
            "y1": y1_list,
            "y2": y2_list,
            "x_label": str(x_label) if x_label else "X",
            "y1_label": str(y1_label) if y1_label else "Y1",
            "y2_label": str(y2_label) if y2_label else "Y2",
            "y1_name": str(y1_name) if y1_name else "Signal 1",
            "y2_name": str(y2_name) if y2_name else "Signal 2",
            "x_min": float(x_min) if x_min is not None else None,
            "x_max": float(x_max) if x_max is not None else None,
            "y1_min": float(y1_min) if y1_min is not None else None,
            "y1_max": float(y1_max) if y1_max is not None else None,
            "y2_min": float(y2_min) if y2_min is not None else None,
            "y2_max": float(y2_max) if y2_max is not None else None,
            "x_log": bool(x_log) if x_log is not None else False,
            "y1_log": bool(y1_log) if y1_log is not None else False,
            "y2_log": bool(y2_log) if y2_log is not None else False
        }
        await context.send_telemetry(self.id, payload)
        return "Out"


@register_block("outputs/plots/polar_plot")
class PolarPlotBlock(BaseBlock):
    """Plots radial data R against angular coordinate Theta in polar coordinates."""
    icon = "🧭"
    display_name = "Polar Plot"
    description = "Plots radial data R against angular coordinate Theta in polar coordinates."
    default_width = 300
    default_height = 300
    ui_behavior = {"custom_widget": "polar_plot", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("R", type_hint=np.ndarray),
        DataIn("Theta", type_hint=np.ndarray),
        DataIn("AngleUnit", type_hint=str, default="Degrees", widget="dropdown",
               options=["Degrees", "Radians"], optional=True),
        DataIn("PlotMode", type_hint=str, default="Lines", widget="dropdown",
               options=["Lines", "Markers", "Lines+Markers"], optional=True),
        DataIn("Direction", type_hint=str, default="Counterclockwise", widget="dropdown",
               options=["Counterclockwise", "Clockwise"], optional=True),
        DataIn("Labels", type_hint=list, optional=True),
        DataIn("RLabel", type_hint=str, default="Radius", optional=True),
        DataIn("RMin", type_hint=float, optional=True),
        DataIn("RMax", type_hint=float, optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Gráfico Polar",
            "description": "Plota dados radiais R em função da coordenada angular Teta em coordenadas polares.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Plotar",
                "R": "R (Raio)",
                "Theta": "Teta (Ângulo)",
                "AngleUnit": "Unidade Angular",
                "PlotMode": "Modo de Traçado",
                "Direction": "Sentido",
                "Labels": "Rótulos",
                "RLabel": "Rótulo R",
                "RMin": "R Mín",
                "RMax": "R Máx",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Gráfico Polar",
            "description": "Grafica datos radiales R en función de la coordenada angular Theta en coordenadas polares.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Graficar",
                "R": "R (Radio)",
                "Theta": "Theta (Ángulo)",
                "AngleUnit": "Unidad Angular",
                "PlotMode": "Modo de Trazado",
                "Direction": "Sentido",
                "Labels": "Etiquetas",
                "RLabel": "Etiqueta R",
                "RMin": "R Mín",
                "RMax": "R Máx",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        r = await context.pull(self.id, "R")
        theta = await context.pull(self.id, "Theta")
        angle_unit = await context.pull(self.id, "AngleUnit")
        plot_mode = await context.pull(self.id, "PlotMode")
        direction = await context.pull(self.id, "Direction")
        labels = await context.pull(self.id, "Labels")
        r_label = await context.pull(self.id, "RLabel")
        r_min = await context.pull(self.id, "RMin")
        r_max = await context.pull(self.id, "RMax")

        r_list = r.tolist() if isinstance(r, np.ndarray) else (r if isinstance(r, list) else [])
        theta_list = theta.tolist() if isinstance(theta, np.ndarray) else (theta if isinstance(theta, list) else [])
        labels_list = labels.tolist() if isinstance(labels, np.ndarray) else (labels if isinstance(labels, list) else None)

        payload = {
            "r": r_list,
            "theta": theta_list,
            "angle_unit": str(angle_unit).lower() if angle_unit else "degrees",
            "plot_mode": str(plot_mode).lower().replace("+", "+") if plot_mode else "lines",
            "direction": str(direction).lower() if direction else "counterclockwise",
            "labels": labels_list,
            "r_label": str(r_label) if r_label else "Radius",
            "r_min": float(r_min) if r_min is not None else None,
            "r_max": float(r_max) if r_max is not None else None
        }
        await context.send_telemetry(self.id, payload)
        return "Out"


@register_block("outputs/plots/bar_plot")
class BarPlotBlock(BaseBlock):
    """Plots discrete categorical values or multi-channel comparisons as vertical or horizontal bars."""
    icon = "📊"
    display_name = "Bar Plot"
    description = "Plots discrete categorical values or multi-channel comparisons as vertical or horizontal bars."
    default_width = 300
    default_height = 300
    ui_behavior = {"custom_widget": "bar_plot", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("Values", type_hint=np.ndarray),
        DataIn("Categories", type_hint=list, optional=True),
        DataIn("Labels", type_hint=list, optional=True),
        DataIn("Orientation", type_hint=str, default="Vertical", widget="dropdown",
               options=["Vertical", "Horizontal"], optional=True),
        DataIn("BarMode", type_hint=str, default="Group", widget="dropdown",
               options=["Group", "Stack"], optional=True),
        DataIn("XLabel", type_hint=str, default="Category", optional=True),
        DataIn("YLabel", type_hint=str, default="Value", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Gráfico de Barras",
            "description": "Plota valores categóricos discretos ou comparações multicanal em barras verticais ou horizontais.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Plotar",
                "Values": "Valores",
                "Categories": "Categorias",
                "Labels": "Rótulos",
                "Orientation": "Orientação",
                "BarMode": "Modo de Barras",
                "XLabel": "Rótulo X",
                "YLabel": "Rótulo Y",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Gráfico de Barras",
            "description": "Grafica valores categóricos discretos o comparaciones multicanal en barras verticales u horizontales.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Graficar",
                "Values": "Valores",
                "Categories": "Categorías",
                "Labels": "Etiquetas",
                "Orientation": "Orientación",
                "BarMode": "Modo de Barras",
                "XLabel": "Etiqueta X",
                "YLabel": "Etiqueta Y",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        values = await context.pull(self.id, "Values")
        categories = await context.pull(self.id, "Categories")
        labels = await context.pull(self.id, "Labels")
        orientation = await context.pull(self.id, "Orientation")
        barmode = await context.pull(self.id, "BarMode")
        x_label = await context.pull(self.id, "XLabel")
        y_label = await context.pull(self.id, "YLabel")

        values_list = values.tolist() if isinstance(values, np.ndarray) else (values if isinstance(values, list) else [])
        cats_list = categories.tolist() if isinstance(categories, np.ndarray) else (categories if isinstance(categories, list) else None)
        labels_list = labels.tolist() if isinstance(labels, np.ndarray) else (labels if isinstance(labels, list) else None)

        payload = {
            "values": values_list,
            "categories": cats_list,
            "labels": labels_list,
            "orientation": "h" if str(orientation).lower().startswith("h") else "v",
            "barmode": str(barmode).lower() if barmode else "group",
            "x_label": str(x_label) if x_label else "Category",
            "y_label": str(y_label) if y_label else "Value"
        }
        await context.send_telemetry(self.id, payload)
        return "Out"


@register_block("outputs/plots/box_plot")
class BoxPlotBlock(BaseBlock):
    """Visualizes statistical distributions, medians, quartiles, and outliers via box or violin representations."""
    icon = "📦"
    display_name = "Box / Violin Plot"
    description = "Visualizes statistical distributions, medians, quartiles, and outliers via box or violin representations."
    default_width = 300
    default_height = 300
    ui_behavior = {"custom_widget": "box_plot", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("Data", type_hint=np.ndarray),
        DataIn("PlotType", type_hint=str, default="Box", widget="dropdown",
               options=["Box", "Violin"], optional=True),
        DataIn("Points", type_hint=str, default="Outliers", widget="dropdown",
               options=["Outliers", "All", "None"], optional=True),
        DataIn("Labels", type_hint=list, optional=True),
        DataIn("YLabel", type_hint=str, default="Value", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Gráfico Box / Violin",
            "description": "Visualiza distribuições estatísticas, medianas, quartis e outliers através de representações boxplot ou violino.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Plotar",
                "Data": "Dados",
                "PlotType": "Tipo de Gráfico",
                "Points": "Pontos",
                "Labels": "Rótulos",
                "YLabel": "Rótulo Y",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Gráfico Box / Violin",
            "description": "Visualiza distribuciones estadísticas, medianas, cuartiles y valores atípicos mediante representaciones boxplot o violín.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Graficar",
                "Data": "Datos",
                "PlotType": "Tipo de Gráfico",
                "Points": "Puntos",
                "Labels": "Etiquetas",
                "YLabel": "Etiqueta Y",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        raw_data = await context.pull(self.id, "Data")
        plot_type = await context.pull(self.id, "PlotType")
        points = await context.pull(self.id, "Points")
        labels = await context.pull(self.id, "Labels")
        y_label = await context.pull(self.id, "YLabel")

        data_list = raw_data.tolist() if isinstance(raw_data, np.ndarray) else (raw_data if isinstance(raw_data, list) else [])
        labels_list = labels.tolist() if isinstance(labels, np.ndarray) else (labels if isinstance(labels, list) else None)

        payload = {
            "data": data_list,
            "plot_type": str(plot_type).lower() if plot_type else "box",
            "points": str(points).lower() if points else "outliers",
            "labels": labels_list,
            "y_label": str(y_label) if y_label else "Value"
        }
        await context.send_telemetry(self.id, payload)
        return "Out"


@register_block("outputs/plots/plot_3d")
class Plot3DBlock(BaseBlock):
    """Plots 3D spatial surfaces, scatter clouds, or meshes with interactive orbital rotation."""
    icon = "🧊"
    display_name = "3D Plot"
    description = "Plots 3D spatial surfaces, scatter clouds, or meshes with interactive orbital rotation."
    default_width = 340
    default_height = 340
    ui_behavior = {"custom_widget": "plot_3d", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("Z", type_hint=np.ndarray),
        DataIn("X", type_hint=np.ndarray, optional=True),
        DataIn("Y", type_hint=np.ndarray, optional=True),
        DataIn("PlotType", type_hint=str, default="Surface", widget="dropdown",
               options=["Surface", "Scatter3D", "Mesh3D"], optional=True),
        DataIn("Colormap", type_hint=str, default="Viridis", widget="dropdown",
               options=["Plotly3", "Viridis", "Cividis", "Hot", "Inferno", "Turbo", "Agsunset", "Picnic", "Phase", "Greys", "Bluered"], optional=True),
        DataIn("XLabel", type_hint=str, default="X", optional=True),
        DataIn("YLabel", type_hint=str, default="Y", optional=True),
        DataIn("ZLabel", type_hint=str, default="Z", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Gráfico 3D",
            "description": "Plota superfícies espaciais 3D, nuvens de dispersão ou malhas com rotação orbital interativa.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Plotar",
                "Z": "Z",
                "X": "X",
                "Y": "Y",
                "PlotType": "Tipo de Gráfico",
                "Colormap": "Mapa de Cores",
                "XLabel": "Rótulo X",
                "YLabel": "Rótulo Y",
                "ZLabel": "Rótulo Z",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Gráfico 3D",
            "description": "Grafica superficies espaciales 3D, nubes de dispersión o mallas con rotación orbital interactiva.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Graficar",
                "Z": "Z",
                "X": "X",
                "Y": "Y",
                "PlotType": "Tipo de Gráfico",
                "Colormap": "Mapa de Colores",
                "XLabel": "Etiqueta X",
                "YLabel": "Etiqueta Y",
                "ZLabel": "Etiqueta Z",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        z = await context.pull(self.id, "Z")
        x = await context.pull(self.id, "X")
        y = await context.pull(self.id, "Y")
        plot_type = await context.pull(self.id, "PlotType")
        colormap = await context.pull(self.id, "Colormap")
        x_label = await context.pull(self.id, "XLabel")
        y_label = await context.pull(self.id, "YLabel")
        z_label = await context.pull(self.id, "ZLabel")

        z_out = z.tolist() if isinstance(z, np.ndarray) else (z if isinstance(z, list) else [])
        x_out = x.tolist() if isinstance(x, np.ndarray) else (x if isinstance(x, list) else None)
        y_out = y.tolist() if isinstance(y, np.ndarray) else (y if isinstance(y, list) else None)

        payload = {
            "z": z_out,
            "x": x_out,
            "y": y_out,
            "plot_type": str(plot_type).lower() if plot_type else "surface",
            "colormap": str(colormap) if colormap else "Viridis",
            "x_label": str(x_label) if x_label else "X",
            "y_label": str(y_label) if y_label else "Y",
            "z_label": str(z_label) if z_label else "Z"
        }
        await context.send_telemetry(self.id, payload)
        return "Out"


@register_block("outputs/plots/waterfall_plot")
class WaterfallPlotBlock(BaseBlock):
    """Accumulates sequential 1D spectral sweeps into a cascading 2D time/frequency waterfall display."""
    icon = "🌊"
    display_name = "Waterfall Spectrogram"
    description = "Accumulates sequential 1D spectral sweeps into a cascading 2D time/frequency waterfall display."
    default_width = 340
    default_height = 340
    ui_behavior = {"accumulate_history": True, "custom_widget": "waterfall_plot", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Plot"),
        DataIn("Spectrum", type_hint=np.ndarray),
        DataIn("XCoords", type_hint=np.ndarray, optional=True),
        DataIn("MaxHistory", type_hint=int, default=50, widget="number", optional=True),
        DataIn("Colormap", type_hint=str, default="Viridis", widget="dropdown",
               options=["Plotly3", "Viridis", "Cividis", "Hot", "Inferno", "Turbo", "Agsunset", "Picnic", "Phase", "Greys", "Bluered"], optional=True),
        DataIn("XLabel", type_hint=str, default="Frequency / Wavelength", optional=True),
        DataIn("YLabel", type_hint=str, default="Sweep / Time", optional=True),
        DataIn("ZLabel", type_hint=str, default="Intensity", optional=True),
        DataIn("ZMin", type_hint=float, optional=True),
        DataIn("ZMax", type_hint=float, optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Espectrograma Cascata",
            "description": "Acumula varreduras espectrais 1D sequenciais em um display de cascata 2D de tempo/frequência.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Plotar",
                "Spectrum": "Espectro",
                "XCoords": "Coordenadas X",
                "MaxHistory": "Histórico Máx",
                "Colormap": "Mapa de Cores",
                "XLabel": "Rótulo X",
                "YLabel": "Rótulo Y",
                "ZLabel": "Rótulo Z",
                "ZMin": "Z Mín",
                "ZMax": "Z Máx",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Espectrograma Cascada",
            "description": "Acumula barridos espectrales 1D secuenciales en una visualización en cascada 2D de tiempo/frecuencia.",
            "category": "Gráficos",
            "pins": {
                "Plot": "Graficar",
                "Spectrum": "Espectro",
                "XCoords": "Coordenadas X",
                "MaxHistory": "Historial Máx",
                "Colormap": "Mapa de Colores",
                "XLabel": "Etiqueta X",
                "YLabel": "Etiqueta Y",
                "ZLabel": "Etiqueta Z",
                "ZMin": "Z Mín",
                "ZMax": "Z Máx",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        spectrum = await context.pull(self.id, "Spectrum")
        x_coords = await context.pull(self.id, "XCoords")
        max_history = await context.pull(self.id, "MaxHistory")
        colormap = await context.pull(self.id, "Colormap")
        x_label = await context.pull(self.id, "XLabel")
        y_label = await context.pull(self.id, "YLabel")
        z_label = await context.pull(self.id, "ZLabel")
        z_min = await context.pull(self.id, "ZMin")
        z_max = await context.pull(self.id, "ZMax")

        try:
            max_hist = int(max_history) if max_history is not None else 50
        except Exception:
            max_hist = 50

        spec_list = spectrum.tolist() if isinstance(spectrum, np.ndarray) else (spectrum if isinstance(spectrum, list) else [])
        x_list = x_coords.tolist() if isinstance(x_coords, np.ndarray) else (x_coords if isinstance(x_coords, list) else None)

        payload = {
            "spectrum": spec_list,
            "x_coords": x_list,
            "max_history": max_hist,
            "colormap": str(colormap) if colormap else "Viridis",
            "x_label": str(x_label) if x_label else "Frequency / Wavelength",
            "y_label": str(y_label) if y_label else "Sweep / Time",
            "z_label": str(z_label) if z_label else "Intensity",
            "z_min": float(z_min) if z_min is not None else None,
            "z_max": float(z_max) if z_max is not None else None,
            "timestamp": time.time()
        }
        await context.send_telemetry(self.id, payload)
        return "Out"

