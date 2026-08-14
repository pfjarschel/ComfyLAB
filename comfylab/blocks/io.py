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

import base64
import io
import os
import csv
import json
from datetime import datetime
import logging
from typing import Any, Optional, Dict, List
import numpy as np

logger = logging.getLogger("comfylab.blocks.io")

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from backend.workspace import get_workspace_path


@register_block(r"File I\/O/path_generator")
class FilePathGeneratorBlock(BaseBlock):
    """Generates file names dynamically using timestamps to prevent overwriting."""
    icon = "📂"
    display_name = "Path Generator"
    description = "Generates a file path using a prefix, current timestamp, and extension."

    inputs_def = [
        DataIn("Prefix", type_hint=str, default="data", widget="text"),
        DataIn("Extension", type_hint=str, default=".csv", widget="text"),
        DataIn("FormatPattern", type_hint=str, default="", widget="text", optional=True),
        DataIn("Subfolder", type_hint=str, default="", widget="text", optional=True)
    ]
    outputs_def = [
        DataOut("FilePath", type_hint=str)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Gerador de Caminho",
            "description": "Gera um caminho de arquivo usando um prefixo, carimbo de tempo atual e extensão.",
            "pins": {
                "Prefix": "Prefixo",
                "Extension": "Extensão",
                "FormatPattern": "Padrão de Formato",
                "Subfolder": "Subpasta",
                "FilePath": "Caminho do Arquivo"
            }
        },
        "es": {
            "display_name": "Generador de Ruta",
            "description": "Genera una ruta de archivo utilizando un prefijo, marca de tiempo actual y extensión.",
            "pins": {
                "Prefix": "Prefijo",
                "Extension": "Extensión",
                "FormatPattern": "Patrón de Formato",
                "Subfolder": "Subcarpeta",
                "FilePath": "Ruta de Archivo"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "FilePath":
            prefix = await context.pull(self.id, "Prefix")
            ext = await context.pull(self.id, "Extension")
            pattern = await context.pull(self.id, "FormatPattern")
            subfolder = await context.pull(self.id, "Subfolder")

            if not pattern:
                pattern = "%Y-%m-%d_%H%M%S"
            if ext and not ext.startswith("."):
                ext = "." + ext

            timestamp = datetime.now().strftime(pattern)
            filename = f"{prefix}_{timestamp}{ext}"

            if subfolder:
                # Ensure directory exists
                os.makedirs(subfolder, exist_ok=True)
                filepath = os.path.join(subfolder, filename)
            else:
                filepath = filename

            return filepath
        return None


@register_block("outputs/basic/image_display")
class ImageDisplayBlock(BaseBlock):
    """Loads an image from the workspace and displays it in the UI."""
    icon = "🖼️"
    display_name = "Image Display"
    description = "Loads an image from the workspace (relative path) and displays it."
    default_width = 300
    default_height = 300
    ui_behavior = {"custom_widget": "image_display", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Display"),
        DataIn("FilePath", type_hint=str, default="uploads/image.png", widget="text"),
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Exibição de Imagem",
            "description": "Carrega uma imagem da área de trabalho (caminho relativo) e a exibe.",
            "pins": {
                "Display": "Exibir",
                "FilePath": "Caminho do Arquivo",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Visualización de Imagen",
            "description": "Carga una imagen del espacio de trabajo (ruta relativa) y la muestra.",
            "pins": {
                "Display": "Mostrar",
                "FilePath": "Ruta de Archivo",
                "Out": "Salida"
            }
        }
    }


    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        filepath = await context.pull(self.id, "FilePath")
        
        # Send telemetry payload with the filepath
        payload = {
            "filepath": str(filepath) if filepath else ""
        }
        await context.send_telemetry(self.id, payload)
        return "Out"


@register_block("outputs/basic/array_display")
class ArrayDisplayBlock(BaseBlock):
    """Displays a numeric array (2D grayscale or 3D color) directly as an image in the UI without saving to disk."""
    icon = "🖼️"
    display_name = "Array Display"
    description = "Displays a numeric array (2D grayscale or 3D BGR/RGB) directly as an image in the UI."
    default_width = 320
    default_height = 300
    ui_behavior = {"custom_widget": "array_display", "render_standard_inputs": True}

    inputs_def = [
        ExecIn("Display"),
        DataIn("Data", type_hint=np.ndarray),
        DataIn("Quality", type_hint=int, default=80, optional=True, widget="slider", options={"min": 10, "max": 100, "step": 5}),
        DataIn("ColorFormat", type_hint=str, default="BGR", widget="dropdown", options=["BGR", "RGB", "Grayscale"], optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Data", type_hint=np.ndarray)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Exibição de Array",
            "description": "Exibe um array numérico (2D tons de cinza ou 3D BGR/RGB) diretamente como uma imagem na interface.",
            "pins": {
                "Display": "Exibir",
                "Data": "Dados",
                "Quality": "Qualidade",
                "ColorFormat": "Formato de Cor",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Visualización de Matriz",
            "description": "Muestra un arreglo numérico (2D escala de grises o 3D BGR/RGB) directamente como una imagen en la interfaz.",
            "pins": {
                "Display": "Mostrar",
                "Data": "Datos",
                "Quality": "Calidad",
                "ColorFormat": "Formato de Color",
                "Out": "Salida"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_data: Optional[np.ndarray] = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        data = await context.pull(self.id, "Data")
        quality = await context.pull(self.id, "Quality")
        color_fmt = await context.pull(self.id, "ColorFormat")

        if data is None:
            return "Out"

        self._last_data = data
        quality_val = int(quality) if quality is not None else 80
        quality_val = max(10, min(100, quality_val))

        try:
            from PIL import Image
            arr = np.asarray(data)
            if np.issubdtype(arr.dtype, np.floating):
                if np.min(arr) >= 0.0 and np.max(arr) <= 1.0:
                    arr = arr * 255.0
            arr = np.clip(arr, 0, 255).astype(np.uint8)

            img = None
            if arr.ndim == 2:
                img = Image.fromarray(arr, mode='L')
            elif arr.ndim == 3:
                channels = arr.shape[2]
                if channels == 1:
                    img = Image.fromarray(arr.squeeze(axis=2), mode='L')
                elif channels == 3:
                    if color_fmt == "BGR":
                        arr_rgb = arr[:, :, ::-1]
                        img = Image.fromarray(arr_rgb, mode='RGB')
                    else:
                        img = Image.fromarray(arr, mode='RGB')
                elif channels == 4:
                    img = Image.fromarray(arr, mode='RGBA')

            if img is not None:
                buf = io.BytesIO()
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(buf, format="JPEG", quality=quality_val)
                b64_str = base64.b64encode(buf.getvalue()).decode('ascii')
                img.close()
                buf.close()

                payload = {
                    "image_data": f"data:image/jpeg;base64,{b64_str}"
                }
                await context.send_telemetry(self.id, payload)
        except Exception as e:
            logger.error(f"ArrayDisplayBlock error: {e}")

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Data":
            if self._last_data is not None:
                return self._last_data
            return await context.pull(self.id, "Data")
        return None


@register_block(r"File I\/O/image_to_array")
class ImageToArrayBlock(BaseBlock):
    """Loads an image from the workspace and converts it to a numeric array."""
    icon = "🖼️"
    display_name = "Image to Array"
    description = "Loads an image from the workspace (relative path) and outputs it as a NumPy array."

    inputs_def = [
        DataIn("FilePath", type_hint=str, default="uploads/image.png", widget="text"),
        DataIn("Grayscale", type_hint=bool, default=False, widget="checkbox"),
    ]
    outputs_def = [DataOut("Array", type_hint=np.ndarray)]

    i18n = {
        "pt-BR": {
            "display_name": "Imagem para Array",
            "description": "Carrega uma imagem da área de trabalho (caminho relativo) e a converte em um array NumPy.",
            "pins": {
                "FilePath": "Caminho do Arquivo",
                "Grayscale": "Tons de Cinza",
                "Array": "Array"
            }
        },
        "es": {
            "display_name": "Imagen a Matriz",
            "description": "Carga una imagen del espacio de trabajo (ruta relativa) y la emite como un arreglo NumPy.",
            "pins": {
                "FilePath": "Ruta de Archivo",
                "Grayscale": "Escala de Grises",
                "Array": "Matriz"
            }
        }
    }


    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Array":
            filepath = await context.pull(self.id, "FilePath")
            grayscale = bool(await context.pull(self.id, "Grayscale"))
            
            if not filepath:
                return None
                
            try:
                from PIL import Image, ImageFile

                ImageFile.LOAD_TRUNCATED_IMAGES = True
                
                ws_path = get_workspace_path()
                full_path = os.path.join(ws_path, filepath) if ws_path else filepath
                
                if not os.path.exists(full_path):
                    logger.error(f"ImageToArray: File not found {full_path}")
                    return None
                    
                img = Image.open(full_path)
                if grayscale:
                    img = img.convert("L")
                
                return np.array(img)
            except ImportError:
                logger.error("Pillow (PIL) is required to load images. Please install it.")
                return None
            except Exception as e:
                logger.error(f"Error loading image: {e}")
                return None
        return None


@register_block(r"File I\/O/save_csv")
class SaveDataBlock(BaseBlock):
    """Saves experimental data (scalars, lists, or dictionaries) to a CSV file."""
    icon = "📝"
    display_name = "Save CSV"
    description = "Saves structured data rows to a CSV file. Supports appending or overwriting."

    inputs_def = [
        ExecIn("Write"),
        DataIn("FilePath", type_hint=str, default="output.csv", widget="text"),
        DataIn("Data", type_hint=Any),
        DataIn("Headers", type_hint=list, optional=True),
        DataIn("Transpose", type_hint=bool, default=True, widget="checkbox", optional=True),
        DataIn("Append", type_hint=bool, default=False, widget="checkbox", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Salvar CSV",
            "description": "Salva linhas de dados estruturados em um arquivo CSV. Suporta anexar ou sobrescrever.",
            "pins": {
                "Write": "Escrever",
                "FilePath": "Caminho do Arquivo",
                "Data": "Dados",
                "Headers": "Cabeçalhos",
                "Transpose": "Transpor",
                "Append": "Anexar",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Guardar CSV",
            "description": "Guarda filas de datos estructurados en un archivo CSV. Soporta anexar o sobrescribir.",
            "pins": {
                "Write": "Escribir",
                "FilePath": "Ruta de Archivo",
                "Data": "Datos",
                "Headers": "Encabezados",
                "Transpose": "Transponer",
                "Append": "Anexar",
                "Out": "Salida"
            }
        }
    }


    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        filepath = await context.pull(self.id, "FilePath")
        data = await context.pull(self.id, "Data")
        headers = await context.pull(self.id, "Headers")
        transpose = await context.pull(self.id, "Transpose")
        append_mode = await context.pull(self.id, "Append")

        if isinstance(data, np.ndarray):
            data = data.tolist()
        if isinstance(headers, np.ndarray):
            headers = headers.tolist()

        if isinstance(headers, str):
            # If the user passed a single string like "Time, Voltage", split it
            headers = [h.strip() for h in headers.split(',')]
        # Removed the quote stripping from list items to preserve user's typed quotes

        if not filepath:
            raise ValueError("CSV Logger: FilePath input cannot be empty.")

        # Ensure parent directory of filepath exists
        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        file_exists = os.path.exists(filepath)
        file_empty = not file_exists or os.path.getsize(filepath) == 0

        # Determine open mode
        append_mode = False if append_mode is None else bool(append_mode)
        open_mode = 'a' if (append_mode and not file_empty) else 'w'

        if isinstance(data, dict):
            # Check if values are lists (writing columns) or scalars (writing a single row)
            is_col_format = any(isinstance(v, list) for v in data.values())
            
            if is_col_format:
                keys = list(data.keys())
                lengths = [len(data[k]) for k in keys if isinstance(data[k], list)]
                max_len = max(lengths) if lengths else 0
                
                with open(filepath, open_mode, newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if open_mode == 'w' or file_empty:
                        writer.writerow(keys)
                    for idx in range(max_len):
                        row = []
                        for k in keys:
                            val = data[k]
                            if isinstance(val, list):
                                row.append(val[idx] if idx < len(val) else "")
                            else:
                                row.append(val if idx == 0 else "")
                        writer.writerow(row)
            else:
                keys = list(data.keys())
                with open(filepath, open_mode, newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    if open_mode == 'w' or file_empty:
                        writer.writeheader()
                    writer.writerow(data)
        
        elif isinstance(data, list):
            if transpose:
                if len(data) > 0 and isinstance(data[0], list):
                    # 2D array transpose
                    data = list(map(list, zip(*data)))
                else:
                    # 1D array transpose to column
                    data = [[x] for x in data]

            if len(data) > 0 and isinstance(data[0], list):
                # Multiple rows
                with open(filepath, open_mode, newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if (open_mode == 'w' or file_empty) and headers:
                        f.write(",".join(str(h) for h in headers) + "\n")
                    writer.writerows(data)
            else:
                # Single row
                with open(filepath, open_mode, newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if (open_mode == 'w' or file_empty) and headers:
                        f.write(",".join(str(h) for h in headers) + "\n")
                    writer.writerow(data)
        else:
            # Scalar
            row = [data]
            with open(filepath, open_mode, newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if (open_mode == 'w' or file_empty) and headers:
                    f.write(",".join(str(h) for h in headers) + "\n")
                writer.writerow(row)

        return "Out"


@register_block(r"File I\/O/save_parquet")
class SaveParquetBlock(BaseBlock):
    """Saves experimental data (scalars, lists, or dictionaries) to a Parquet file."""
    icon = "📝"
    display_name = "Save Parquet"
    description = "Saves structured data rows to a Parquet file. Highly optimized for large matrices and columnar data. Appending is supported via fastparquet."

    inputs_def = [
        ExecIn("Write"),
        DataIn("FilePath", type_hint=str, default="output.parquet", widget="text"),
        DataIn("Data", type_hint=Any),
        DataIn("Headers", type_hint=list, optional=True),
        DataIn("Append", type_hint=bool, default=False, widget="checkbox", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Salvar Parquet",
            "description": "Salva linhas de dados estruturados em um arquivo Parquet. Otimizado para grandes matrizes e dados colunares. Anexação é suportada via fastparquet.",
            "pins": {
                "Write": "Escrever",
                "FilePath": "Caminho do Arquivo",
                "Data": "Dados",
                "Headers": "Cabeçalhos",
                "Append": "Anexar",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Guardar Parquet",
            "description": "Guarda filas de datos estructurados en un archivo Parquet. Optimizado para grandes matrices y datos columnares. Se admite anexar mediante fastparquet.",
            "pins": {
                "Write": "Escribir",
                "FilePath": "Ruta de Archivo",
                "Data": "Datos",
                "Headers": "Encabezados",
                "Append": "Anexar",
                "Out": "Salida"
            }
        }
    }


    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        import pandas as pd
        
        filepath = await context.pull(self.id, "FilePath")
        data = await context.pull(self.id, "Data")
        headers = await context.pull(self.id, "Headers")
        append_mode = await context.pull(self.id, "Append")

        if isinstance(data, np.ndarray):
            data = data.tolist()
        if isinstance(headers, np.ndarray):
            headers = headers.tolist()

        if not filepath or data is None:
            return "Out"
            
        if isinstance(headers, str):
            headers = [h.strip() for h in headers.split(',')]
            
        file_empty = not os.path.exists(filepath) or os.path.getsize(filepath) == 0

        df = None

        if isinstance(data, dict):
            # Check if values are lists (writing columns) or scalars (writing a single row)
            is_col_format = any(isinstance(v, list) for v in data.values())
            
            if is_col_format:
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
        
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], list):
                # 2D array (list of columns)
                df = pd.DataFrame(data).T
                if headers:
                    df.columns = headers
            else:
                # 1D array (single column)
                df = pd.DataFrame(data)
                if headers:
                    df.columns = headers
        else:
            # Scalar
            df = pd.DataFrame([data])
            if headers:
                df.columns = headers

        if df is not None:
            # Parquet requires all column names to be strings
            df.columns = df.columns.astype(str)
            
            append_mode = False if append_mode is None else bool(append_mode)
            if append_mode and not file_empty:
                df.to_parquet(filepath, engine='fastparquet', append=True)
            else:
                df.to_parquet(filepath, engine='fastparquet')

        return "Out"


@register_block(r"File I\/O/load_csv")
class LoadCSVBlock(BaseBlock):
    """Reads a CSV file into data arrays."""
    icon = "📂"
    display_name = "Load CSV"
    description = "Reads a CSV file and outputs its contents as Columns (2D array), Headers, and a Dictionary mapping names to arrays."

    inputs_def = [
        ExecIn("Read"),
        DataIn("FilePath", type_hint=str, default="data.csv", widget="text"),
        DataIn("SkipLines", type_hint=int, default=0, widget="number")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Columns", type_hint=np.ndarray),
        DataOut("Headers", type_hint=list)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._loaded_columns: np.ndarray = np.array([])
        self._loaded_headers: List[str] = []

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Columns":
            return self._loaded_columns
        elif pin_name == "Headers":
            return self._loaded_headers
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        import pandas as pd
        
        filepath = await context.pull(self.id, "FilePath")
        skip_lines = await context.pull(self.id, "SkipLines")
        if skip_lines is None:
            skip_lines = 0

        if not filepath or not os.path.exists(filepath):
            self._loaded_columns = []
            self._loaded_headers = []
            return "Out"

        try:
            df = pd.read_csv(filepath, skiprows=int(skip_lines))
            self._loaded_columns = df.values.T
            self._loaded_headers = df.columns.astype(str).tolist()
        except Exception:
            self._loaded_columns = np.array([])
            self._loaded_headers = []

        return "Out"


@register_block(r"File I\/O/load_parquet")
class LoadParquetBlock(BaseBlock):
    """Reads a Parquet file into data arrays."""
    icon = "📂"
    display_name = "Load Parquet"
    description = "Reads a Parquet file and outputs Columns, Headers, and a Dictionary."

    inputs_def = [
        ExecIn("Read"),
        DataIn("FilePath", type_hint=str, default="data.parquet", widget="text"),
        DataIn("ColumnsToLoad", type_hint=str, default="", widget="text", optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Columns", type_hint=np.ndarray),
        DataOut("Headers", type_hint=list)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._loaded_columns: np.ndarray = np.array([])
        self._loaded_headers: List[str] = []

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Columns":
            return self._loaded_columns
        elif pin_name == "Headers":
            return self._loaded_headers
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        import pandas as pd
        
        filepath = await context.pull(self.id, "FilePath")
        columns_str = await context.pull(self.id, "ColumnsToLoad")

        if not filepath or not os.path.exists(filepath):
            self._loaded_columns = []
            self._loaded_headers = []
            return "Out"

        cols = None
        if columns_str and isinstance(columns_str, str):
            cols = [c.strip() for c in columns_str.split(',') if c.strip()]
        elif isinstance(columns_str, list) and len(columns_str) > 0:
            cols = [str(c).strip() for c in columns_str if str(c).strip()]

        try:
            df = pd.read_parquet(filepath, engine='fastparquet', columns=cols if cols else None)
            self._loaded_columns = df.values.T
            self._loaded_headers = df.columns.astype(str).tolist()
        except Exception:
            self._loaded_columns = np.array([])
            self._loaded_headers = []

        return "Out"


def _make_serializable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return [_make_serializable(v) for v in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.generic):
        return obj.item()
    return obj


@register_block(r"File I\/O/save_json")
class SaveJSONBlock(BaseBlock):
    """Saves structured data (dictionaries, lists) to a JSON file."""
    icon = "📝"
    display_name = "Save JSON"
    description = "Saves data as a JSON file. Automatically converts NumPy arrays to lists."

    inputs_def = [
        ExecIn("Write"),
        DataIn("FilePath", type_hint=str, default="data.json", widget="text"),
        DataIn("Data", type_hint=Any)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Salvar JSON",
            "description": "Salva dados como um arquivo JSON. Converte arrays NumPy para listas automaticamente.",
            "pins": {
                "Write": "Escrever",
                "FilePath": "Caminho do Arquivo",
                "Data": "Dados",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Guardar JSON",
            "description": "Guarda datos como un archivo JSON. Convierte automáticamente matrices NumPy a listas.",
            "pins": {
                "Write": "Escribir",
                "FilePath": "Ruta de Archivo",
                "Data": "Datos",
                "Out": "Salida"
            }
        }
    }


    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        filepath = await context.pull(self.id, "FilePath")
        data = await context.pull(self.id, "Data")
        
        if not filepath:
            logger.error("SaveJSONBlock: FilePath cannot be empty.")
            return None

        ws_path = get_workspace_path()
        full_path = os.path.join(ws_path, filepath) if ws_path else filepath
        
        dir_name = os.path.dirname(full_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        try:
            serializable_data = _make_serializable(data)
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving JSON {full_path}: {e}")
            
        return "Out"


@register_block(r"File I\/O/load_json")
class LoadJSONBlock(BaseBlock):
    """Reads a JSON file into structured data."""
    icon = "📂"
    display_name = "Load JSON"
    description = "Reads a JSON file and outputs its contents as data (usually a dictionary or list)."

    inputs_def = [
        ExecIn("Read"),
        DataIn("FilePath", type_hint=str, default="data.json", widget="text")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Data", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Carregar JSON",
            "description": "Lê um arquivo JSON e gera seu conteúdo como dados (geralmente um dicionário ou lista).",
            "pins": {
                "Read": "Ler",
                "FilePath": "Caminho do Arquivo",
                "Out": "Saída",
                "Data": "Dados"
            }
        },
        "es": {
            "display_name": "Cargar JSON",
            "description": "Lee un archivo JSON y emite su contenido como datos (generalmente un diccionario o lista).",
            "pins": {
                "Read": "Leer",
                "FilePath": "Ruta de Archivo",
                "Out": "Salida",
                "Data": "Datos"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._loaded_data: Any = None

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Data":
            return self._loaded_data
        return None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        filepath = await context.pull(self.id, "FilePath")
        
        if not filepath:
            logger.error("LoadJSONBlock: FilePath cannot be empty.")
            return None

        ws_path = get_workspace_path()
        full_path = os.path.join(ws_path, filepath) if ws_path else filepath
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                self._loaded_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON {full_path}: {e}")
            self._loaded_data = None
            
        return "Out"


@register_block(r"File I\/O/array_to_image")
class ArrayToImageBlock(BaseBlock):
    """Saves a numeric array to an image file."""
    icon = "🖼️"
    display_name = "Array to Image"
    description = "Saves an array (2D grayscale, or MxNx3/4 color) as an image file."

    inputs_def = [
        ExecIn("Save"),
        DataIn("Data", type_hint=np.ndarray),
        DataIn("FileName", type_hint=str, default="image.png", widget="text"),
        DataIn("SubDir", type_hint=str, default="", widget="text", optional=True)
    ]
    outputs_def = [ExecOut("Out")]

    i18n = {
        "pt-BR": {
            "display_name": "Array para Imagem",
            "description": "Salva um array (2D tons de cinza ou MxNx3/4 cor) como um arquivo de imagem.",
            "pins": {
                "Save": "Salvar",
                "Data": "Dados",
                "FileName": "Nome do Arquivo",
                "SubDir": "Subdiretório",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Matriz a Imagen",
            "description": "Guarda una matriz (2D escala de grises o MxNx3/4 color) como un archivo de imagen.",
            "pins": {
                "Save": "Guardar",
                "Data": "Datos",
                "FileName": "Nombre de Archivo",
                "SubDir": "Subdirectorio",
                "Out": "Salida"
            }
        }
    }


    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        data = await context.pull(self.id, "Data")
        filename = await context.pull(self.id, "FileName")
        subdir = await context.pull(self.id, "SubDir")

        if data is None or not filename:
            logger.error("ArrayToImageBlock: Data and FileName cannot be empty.")
            return None

        from PIL import Image

        # Determine extension and append .png if needed
        valid_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
        _, ext = os.path.splitext(filename)
        if ext.lower() not in valid_extensions:
            filename += ".png"

        filepath = os.path.join(subdir, filename) if subdir else filename
        
        ws_path = get_workspace_path()
        full_path = os.path.join(ws_path, filepath) if ws_path else filepath

        dir_name = os.path.dirname(full_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        try:
            arr = np.asarray(data)
            
            if np.issubdtype(arr.dtype, np.floating):
                if np.min(arr) >= 0.0 and np.max(arr) <= 1.0:
                    arr = arr * 255.0
            
            arr = np.clip(arr, 0, 255).astype(np.uint8)
            
            # Handling 2D, 3D
            if arr.ndim == 2:
                img = Image.fromarray(arr, mode='L')
            elif arr.ndim == 3 and arr.shape[2] == 3:
                img = Image.fromarray(arr, mode='RGB')
            elif arr.ndim == 3 and arr.shape[2] == 4:
                img = Image.fromarray(arr, mode='RGBA')
            else:
                logger.error(f"ArrayToImageBlock: Unsupported array shape {arr.shape}.")
                return None
                
            img.save(full_path)
        except Exception as e:
            logger.error(f"Error saving image {full_path}: {e}")
            
        return "Out"
