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

import asyncio
import logging
from typing import Any, Dict, Optional, List

import pyvisa

from comfylab.engine.registry import register_node
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext

logger = logging.getLogger("comfylab.nodes.visa")

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

# --- NODE DEFINITIONS ---

@register_node("visa/core/resource_manager")
class VISAResourceManagerNode(BaseNode):
    """Lists available VISA resources on the system."""
    icon = "🔌"
    display_name = "VISA Resource Manager"
    description = "Queries the VISA library and returns a list of available device addresses."

    outputs_def = [
        DataOut("Resources", type_hint=list)
    ]

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


@register_node("visa/core/device")
class VISADeviceNode(BaseNode):
    """Opens a connection to a specific VISA resource address."""
    icon = "📟"
    display_name = "VISA Device"
    description = "Opens a session to a VISA address and outputs the device connection handle."

    inputs_def = [
        ExecIn("Open"),
        DataIn("Address", type_hint=str, default="GPIB0::2::INSTR", widget="text"),
        DataIn("ReadTermination", type_hint=str, default="\n", optional=True),
        DataIn("WriteTermination", type_hint=str, default="\r\n", optional=True),
        DataIn("Timeout", type_hint=float, default=2.0, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Device", type_hint=Any)
    ]

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._device = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        address = await context.pull(self.id, "Address")
        if not address:
            raise ValueError("No address specified for VISA Device node.")

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


@register_node("visa/core/write")
class VISAWriteNode(BaseNode):
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

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        command = await context.pull(self.id, "Command")

        if not device:
            raise ValueError("No device connection handle supplied to VISA Write node.")
        if not command:
            raise ValueError("No command string supplied to VISA Write node.")

        # Extract address for resource locking
        address = getattr(device, "resource_name", str(device))
        async with context.lock_manager.acquire(address):
            logger.info(f"VISA Write on {address}: {command}")
            await asyncio.to_thread(device.write, command)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_node("visa/core/read")
class VISAReadNode(BaseNode):
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

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._last_response = ""

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        if not device:
            raise ValueError("No device connection handle supplied to VISA Read node.")

        # Extract address for resource locking
        address = getattr(device, "resource_name", str(device))
        async with context.lock_manager.acquire(address):
            logger.info(f"VISA Read on {address}")
            self._last_response = await asyncio.to_thread(device.read)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Response":
            return self._last_response
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None


@register_node("visa/core/query")
class VISAQueryNode(BaseNode):
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

    def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, properties)
        self._last_response = ""

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        device = await context.pull(self.id, "Device")
        command = await context.pull(self.id, "Command")

        if not device:
            raise ValueError("No device connection handle supplied to VISA Query node.")
        if not command:
            raise ValueError("No command string supplied to VISA Query node.")

        # Extract address for resource locking
        address = getattr(device, "resource_name", str(device))
        async with context.lock_manager.acquire(address):
            logger.info(f"VISA Query on {address}: {command}")
            self._last_response = await asyncio.to_thread(device.query, command)

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Response":
            return self._last_response
        elif pin_name == "Device":
            return await context.pull(self.id, "Device")
        return None
