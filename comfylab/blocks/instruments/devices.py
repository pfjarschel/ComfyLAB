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
from typing import Any, Dict, Optional

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.blocks.visa import visa_rm_wrapper

logger = logging.getLogger("comfylab.blocks.instruments.devices")


class BaseDeviceConnectBlock(BaseBlock):
    """
    Base class for device-specific connect blocks. Opens a VISA connection to
    the configured address, calls `_device_initialize` to perform any
    device-specific setup, and on teardown calls `_device_teardown` to send
    safety commands before closing the connection.

    Subclasses override `_device_initialize` and/or `_device_teardown` to
    populate device-specific behavior.
    """
    icon = "🔗"
    display_name = "Device Connect"
    description = "Opens a VISA connection with device-specific init/teardown hooks."

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

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._device = None
        self._lock_manager = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        address = await context.pull(self.id, "Address")
        if not address:
            raise ValueError("No address specified for Device Connect block.")

        read_termination = await context.pull(self.id, "ReadTermination")
        write_termination = await context.pull(self.id, "WriteTermination")
        timeout = await context.pull(self.id, "Timeout")

        self._lock_manager = context.lock_manager

        rm = visa_rm_wrapper.get_rm()
        async with context.lock_manager.acquire(address):
            if self._device is not None:
                try:
                    await asyncio.to_thread(self._device.close)
                except Exception:
                    pass

            logger.info(f"Opening connection to VISA device at {address}")
            self._device = await asyncio.to_thread(rm.open_resource, address)

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

            await self._device_initialize(context, self._device)

        return "Out"

    async def _device_initialize(self, context: ExecutionContext, device: Any):
        pass

    async def _device_teardown(self, device: Any, lock_manager: Any):
        pass

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Device":
            return self._device
        return None

    async def teardown(self):
        if self._device is not None:
            lock_manager = self._lock_manager
            if lock_manager is None:
                from comfylab.engine.locks import ResourceLockManager
                lock_manager = ResourceLockManager()
            try:
                await self._device_teardown(self._device, lock_manager)
            except Exception as e:
                logger.error(f"Error during device teardown: {e}")

            try:
                await asyncio.to_thread(self._device.close)
                logger.info(f"Closed connection to VISA device {self.id}.")
            except Exception as e:
                logger.error(f"Error closing VISA connection on teardown: {e}")
            finally:
                self._device = None
