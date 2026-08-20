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

import re
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import pyvisa

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext

logger = logging.getLogger("comfylab.blocks.visa")


@asynccontextmanager
async def locked_device(context: ExecutionContext, device: Any, block_name: str = "VISA"):
    """
    Validates a pulled device handle and yields it under its per-address resource lock.
    Shared by all VISA/instrument blocks to avoid repeating the
    validate -> resolve address -> acquire lock preamble.
    """
    if not device:
        raise ValueError(f"No device connection handle supplied to {block_name} block.")
    address = getattr(device, "resource_name", str(device))
    async with context.lock_manager.acquire(address):
        yield device


# Create singleton resource manager wrapper
class VISAResourceManagerWrapper:
    def __init__(self):
        self._rm = None

    def get_rm(self):
        if self._rm is None:
            try:
                # Try default NI-VISA backend
                self._rm = pyvisa.ResourceManager()
                logger.info("Initialized real PyVISA Resource Manager.")
            except Exception as e:
                # Fallback to PyVISA-py if NI-VISA is missing
                try:
                    self._rm = pyvisa.ResourceManager("@py")
                    logger.info("Initialized PyVISA-Py backend Resource Manager.")
                except Exception as py_err:
                    logger.error(f"Failed to initialize PyVISA Resource Manager: {e} (PyVISA-py fallback also failed: {py_err})")
                    raise py_err
        return self._rm

visa_rm_wrapper = VISAResourceManagerWrapper()

# --- BLOCK DEFINITIONS ---

@register_block("visa/core/resource_manager")
class VISAResourceManagerBlock(BaseBlock):
    """Lists available VISA resources on the system."""
    icon = "🔌"
    display_name = "VISA Resource Manager"
    description = "Queries the VISA library and returns a list of available device addresses."

    outputs_def = [
        DataOut("Resources", type_hint=list)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Gerenciador de Recursos VISA",
            "description": "Consulta a biblioteca VISA e retorna uma lista de endereços de dispositivos disponíveis.",
            "category": "Instrumentos/VISA",
            "pins": {
                "Resources": "Recursos"
            }
        },
        "es": {
            "display_name": "Administrador de Recursos VISA",
            "description": "Consulta la biblioteca VISA y devuelve una lista de direcciones de dispositivos disponibles.",
            "category": "Instrumentos/VISA",
            "pins": {
                "Resources": "Recursos"
            }
        }
    }


    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Resources":
            rm = visa_rm_wrapper.get_rm()
            try:
                resources = await asyncio.to_thread(rm.list_resources)
                return list(resources)
            except Exception as e:
                logger.error(f"Error listing VISA resources: {e}")
                raise e
        return None


def discover_visa_devices(interface_filter: Optional[str] = None, timeout_sec: float = 0.5) -> List[Dict[str, Any]]:
    """
    Safely probes connected VISA resources by querying *IDN? sequentially with a short timeout.
    Safely ignores non-responsive resources and guarantees session teardown.
    """
    rm = visa_rm_wrapper.get_rm()
    try:
        raw_resources = rm.list_resources()
    except Exception as e:
        logger.error(f"Error listing VISA resources during discovery: {e}")
        return []

    # Parse interface filter
    filter_clean = (interface_filter or "USB, GPIB, TCPIP").strip().lower()
    include_all = "all" in filter_clean and "serial" in filter_clean

    allowed_prefixes = set()
    if include_all:
        allowed_prefixes = {"usb", "gpib", "tcpip", "asrl", "/dev/"}
    else:
        if "usb" in filter_clean:
            allowed_prefixes.add("usb")
        if "gpib" in filter_clean:
            allowed_prefixes.add("gpib")
        if "tcpip" in filter_clean or "ethernet" in filter_clean or "lxi" in filter_clean:
            allowed_prefixes.add("tcpip")
        if "asrl" in filter_clean or "serial" in filter_clean:
            allowed_prefixes.add("asrl")
            allowed_prefixes.add("/dev/")

    candidate_addresses = []
    for r in raw_resources:
        r_str = str(r).strip()
        r_lower = r_str.lower()
        if include_all or any(r_lower.startswith(prefix) for prefix in allowed_prefixes):
            candidate_addresses.append(r_str)

    results = []
    timeout_ms = int(max(0.05, timeout_sec) * 1000)

    for address in candidate_addresses:
        dev = None
        try:
            dev = rm.open_resource(address)
            dev.timeout = timeout_ms
            idn_raw = dev.query("*IDN?").strip()
            fields = [f.strip() for f in idn_raw.split(",")]
            vendor = fields[0] if len(fields) > 0 else ""
            model = fields[1] if len(fields) > 1 else ""
            serial = fields[2] if len(fields) > 2 else ""
            firmware = fields[3] if len(fields) > 3 else ""

            results.append({
                "address": address,
                "idn": idn_raw,
                "vendor": vendor,
                "model": model,
                "serial": serial,
                "firmware": firmware
            })
        except Exception as e:
            logger.debug(f"Resource at {address} did not respond to *IDN? probe: {e}")
        finally:
            if dev is not None:
                try:
                    dev.close()
                except Exception:
                    pass

    return results


def match_visa_device(device_info: Dict[str, Any], query: str) -> bool:
    """
    Checks if a discovered device dictionary matches a query string.
    Supports empty query (matches all), comma-separated tokens (all must match),
    and regex/substring pattern matching against address and IDN string.
    """
    if not query or not str(query).strip():
        return True

    address = str(device_info.get("address", ""))
    idn = str(device_info.get("idn", ""))
    target = f"{address} {idn}".strip()
    target_lower = target.lower()
    q_str = str(query).strip()

    # Comma-separated token keywords (e.g. "Keysight, 3024")
    if "," in q_str:
        tokens = [t.strip().lower() for t in q_str.split(",") if t.strip()]
        return all(tok in target_lower for tok in tokens)

    # Try regex matching first
    try:
        if re.search(q_str, target, re.IGNORECASE):
            return True
    except re.error:
        pass

    # Fallback to simple case-insensitive substring
    return q_str.lower() in target_lower


@register_block("visa/core/find_device")
class VISAFindDeviceBlock(BaseBlock):
    """Discovers and matches connected VISA instruments by *IDN? response or address."""
    icon = "🔍"
    display_name = "VISA Find Device"
    description = "Probes connected VISA instruments with *IDN? and outputs the matched device address."

    inputs_def = [
        ExecIn("In"),
        DataIn("Query", type_hint=str, default="", widget="text", optional=True),
        DataIn("Interface", type_hint=str, default="USB, GPIB, TCPIP", widget="select",
               options=["USB, GPIB, TCPIP", "All (incl. Serial)", "USB", "GPIB", "TCPIP", "Serial (ASRL)"],
               optional=True),
        DataIn("Timeout", type_hint=float, default=0.5, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Address", type_hint=str),
        DataOut("IDN", type_hint=str),
        DataOut("Found", type_hint=bool),
        DataOut("AllDevices", type_hint=list)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Buscar Dispositivo VISA",
            "description": "Busca instrumentos VISA conectados via *IDN? e retorna o endereço do dispositivo correspondente.",
            "category": "Instrumentos/VISA",
            "pins": {
                "In": "Entrada",
                "Query": "Busca",
                "Interface": "Interface",
                "Timeout": "Tempo Limite",
                "Out": "Saída",
                "Address": "Endereço",
                "IDN": "Identificação",
                "Found": "Encontrado",
                "AllDevices": "Todos os Dispositivos"
            }
        },
        "es": {
            "display_name": "Buscar Dispositivo VISA",
            "description": "Busca instrumentos VISA conectados mediante *IDN? y emite la dirección del dispositivo coincidente.",
            "category": "Instrumentos/VISA",
            "pins": {
                "In": "Entrada",
                "Query": "Búsqueda",
                "Interface": "Interfaz",
                "Timeout": "Tiempo de Espera",
                "Out": "Salida",
                "Address": "Dirección",
                "IDN": "Identificación",
                "Found": "Encontrado",
                "AllDevices": "Todos los Dispositivos"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._matched_address: str = ""
        self._matched_idn: str = ""
        self._found: bool = False
        self._all_devices: List[Dict[str, Any]] = []

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        query = await context.pull(self.id, "Query")
        if query is None:
            query = ""
        interface = await context.pull(self.id, "Interface")
        timeout_sec = await context.pull(self.id, "Timeout")
        if timeout_sec is None:
            timeout_sec = 0.5

        # Execute safe sequential discovery in worker thread
        devices = await asyncio.to_thread(discover_visa_devices, interface, float(timeout_sec))
        self._all_devices = devices

        # Find first matching device
        matched = None
        for dev in devices:
            if match_visa_device(dev, str(query)):
                matched = dev
                break

        if matched:
            self._matched_address = matched.get("address", "")
            self._matched_idn = matched.get("idn", "")
            self._found = True
            logger.info(f"VISA Find Device matched: {self._matched_address} ({self._matched_idn})")
        else:
            self._matched_address = ""
            self._matched_idn = ""
            self._found = False
            logger.info(f"VISA Find Device found no match for query: '{query}'")

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Address":
            return self._matched_address
        elif pin_name == "IDN":
            return self._matched_idn
        elif pin_name == "Found":
            return self._found
        elif pin_name == "AllDevices":
            return self._all_devices
        return None

    async def clear_data(self) -> None:
        self._matched_address = ""
        self._matched_idn = ""
        self._found = False
        self._all_devices = []


@register_block("visa/core/device")
class VISADeviceBlock(BaseBlock):
    """Opens a connection to a specific VISA resource address."""
    icon = "📟"
    display_name = "VISA Device"
    description = "Opens a session to a VISA address and outputs the device connection handle."

    inputs_def = [
        ExecIn("Open"),
        DataIn("Address", type_hint=str, default="GPIB0::2::INSTR", widget="text"),
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
            "display_name": "Dispositivo VISA",
            "description": "Abre uma sessão para um endereço VISA e gera o handle de conexão do dispositivo.",
            "category": "Instrumentos/VISA",
            "pins": {
                "Open": "Abrir",
                "Address": "Endereço",
                "ReadTermination": "Terminação de Leitura",
                "WriteTermination": "Terminação de Escrita",
                "Timeout": "Tempo Limite",
                "Out": "Saída",
                "Device": "Dispositivo"
            }
        },
        "es": {
            "display_name": "Dispositivo VISA",
            "description": "Abre una sesión a una dirección VISA y emite el identificador de conexión del dispositivo.",
            "category": "Instrumentos/VISA",
            "pins": {
                "Open": "Abrir",
                "Address": "Dirección",
                "ReadTermination": "Terminación de Lectura",
                "WriteTermination": "Terminación de Escritura",
                "Timeout": "Tiempo de Espera",
                "Out": "Salida",
                "Device": "Dispositivo"
            }
        }
    }


    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._device = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        address = await context.pull(self.id, "Address")
        if not address:
            raise ValueError("No address specified for VISA Device block.")

        read_termination = await context.pull(self.id, "ReadTermination")
        write_termination = await context.pull(self.id, "WriteTermination")
        timeout = await context.pull(self.id, "Timeout")

        rm = visa_rm_wrapper.get_rm()
        # Ensure we lock the address resource while opening it
        async with context.lock_manager.acquire(address):
            # Close previous connection if any
            if self._device is not None:
                try:
                    await asyncio.to_thread(self._device.close)
                except Exception:
                    pass
            
            logger.info(f"Opening connection to VISA device at {address}")
            self._device = await asyncio.to_thread(rm.open_resource, address)

            # Configure communication parameters
            if read_termination is not None:
                if isinstance(read_termination, str):
                    read_termination = read_termination.replace("\\r", "\r").replace("\\n", "\n")
                self._device.read_termination = read_termination
            if write_termination is not None:
                if isinstance(write_termination, str):
                    write_termination = write_termination.replace("\\r", "\r").replace("\\n", "\n")
                self._device.write_termination = write_termination
            if timeout is not None:
                self._device.timeout = int(timeout * 1000)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return self._device
        return None

    async def teardown(self):
        if self._device is not None:
            try:
                await asyncio.to_thread(self._device.close)
                logger.info("Closed connection to VISA device.")
            except Exception as e:
                logger.error(f"Error closing VISA connection on teardown: {e}")
            finally:
                self._device = None


@register_block("visa/core/write")
class VISAWriteBlock(BaseBlock):
    """Sends an SCPI/VISA command to a device."""
    icon = "✍️"
    display_name = "VISA Write"
    description = "Writes an SCPI command string to the given VISA device handle."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Command", type_hint=str, default="*IDN?", widget="text")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Escrita VISA",
            "description": "Escreve uma string de comando SCPI no handle do dispositivo VISA fornecido.",
            "category": "Instrumentos/VISA",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Command": "Comando",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Escritura VISA",
            "description": "Escribe una cadena de comando SCPI en el identificador de dispositivo VISA dado.",
            "category": "Instrumentos/VISA",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Command": "Comando",
                "Out": "Salida"
            }
        }
    }


    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        command = await context.pull(self.id, "Command")

        if not command:
            raise ValueError("No command string supplied to VISA Write block.")

        async with locked_device(context, device, "VISA Write") as dev:
            logger.info(f"VISA Write on {getattr(dev, 'resource_name', dev)}: {command}")
            await asyncio.to_thread(dev.write, command)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("visa/core/read")
class VISAReadBlock(BaseBlock):
    """Reads response data from a device."""
    icon = "📖"
    display_name = "VISA Read"
    description = "Reads raw or text response data from the given VISA device handle."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Response", type_hint=str),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Leitura VISA",
            "description": "Lê os dados de resposta do handle do dispositivo VISA fornecido.",
            "category": "Instrumentos/VISA",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Response": "Resposta",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Lectura VISA",
            "description": "Lee los datos de respuesta del identificador de dispositivo VISA dado.",
            "category": "Instrumentos/VISA",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Response": "Respuesta",
                "Out": "Salida"
            }
        }
    }


    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_response = ""

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")

        async with locked_device(context, device, "VISA Read") as dev:
            logger.info(f"VISA Read on {getattr(dev, 'resource_name', dev)}")
            self._last_response = await asyncio.to_thread(dev.read)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Response":
            return self._last_response
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_block("visa/core/query")
class VISAQueryBlock(BaseBlock):
    """Performs a write and immediately reads the response."""
    icon = "❓"
    display_name = "VISA Query"
    description = "Sends an SCPI query string and reads the response from the given VISA device handle."

    inputs_def = [
        ExecIn("In"),
        DataIn("Device", type_hint=Any),
        DataIn("Command", type_hint=str, default="*IDN?", widget="text")
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Response", type_hint=str),
        DataOut("Device", type_hint=Any)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Consulta VISA",
            "description": "Envia uma string de consulta SCPI e lê a resposta do handle do dispositivo VISA fornecido.",
            "category": "Instrumentos/VISA",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Command": "Comando",
                "Response": "Resposta",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Consulta VISA",
            "description": "Envía una cadena de consulta SCPI y lee la respuesta del identificador de dispositivo VISA dado.",
            "category": "Instrumentos/VISA",
            "pins": {
                "In": "Entrada",
                "Device": "Dispositivo",
                "Command": "Comando",
                "Response": "Respuesta",
                "Out": "Salida"
            }
        }
    }


    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_response = ""

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        command = await context.pull(self.id, "Command")

        if not command:
            raise ValueError("No command string supplied to VISA Query block.")

        async with locked_device(context, device, "VISA Query") as dev:
            logger.info(f"VISA Query on {getattr(dev, 'resource_name', dev)}: {command}")
            self._last_response = await asyncio.to_thread(dev.query, command)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Response":
            return self._last_response
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
