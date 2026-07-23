# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
import logging
from typing import Any, Dict, Optional
import numpy as np

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.devices.generic.camera import GenericCamera

logger = logging.getLogger("comfylab.blocks.devices.generic.camera")


@register_block("devices/generic/camera/connect")
class GenericCameraConnectBlock(BaseBlock):
    """Opens a connection to a standard USB webcam or camera via OpenCV."""
    icon = "📷"
    display_name = "Generic Camera Connect"
    description = "Opens a session to a USB webcam or UVC camera (index 0, 1, 2...)."

    inputs_def = [
        ExecIn("Open"),
        DataIn("CameraIndex", type_hint=int, default=0, widget="dropdown", options=[0, 1, 2, 3]),
        DataIn("Width", type_hint=int, default=640, optional=True),
        DataIn("Height", type_hint=int, default=480, optional=True)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Camera", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._cam: Optional[GenericCamera] = None

    async def _init_camera(self, context: ExecutionContext) -> GenericCamera:
        if self._cam is None or not self._cam.is_opened():
            idx = await context.pull(self.id, "CameraIndex")
            w = await context.pull(self.id, "Width")
            h = await context.pull(self.id, "Height")
            idx_val = int(idx) if idx is not None else 0
            self._cam = await asyncio.to_thread(GenericCamera, idx_val)
            if w and h:
                await asyncio.to_thread(self._cam.set_resolution, int(w), int(h))
        return self._cam

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        await self._init_camera(context)
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Camera":
            return await self._init_camera(context)
        return None

    async def teardown(self) -> None:
        if self._cam:
            try:
                await asyncio.to_thread(self._cam.close)
                logger.info("Closed camera capture stream.")
            except Exception as e:
                logger.error(f"Error closing camera: {e}")
            finally:
                self._cam = None


@register_block("devices/generic/camera/capture")
class GenericCameraCaptureBlock(BaseBlock):
    """Captures single image frame (H, W, 3) array from an open camera stream."""
    icon = "🖼️"
    display_name = "Generic Camera Capture"
    description = "Captures an image frame array from an open camera stream."

    inputs_def = [
        ExecIn("In"),
        DataIn("Camera", type_hint=Any)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Frame", type_hint=np.ndarray),
        DataOut("Camera", type_hint=Any)
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._last_frame: np.ndarray = np.array([])

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        cam = await context.pull(self.id, "Camera")
        if cam is None:
            raise ValueError("No camera handle connected to Capture block. Connect the 'Camera' output pin from Generic Camera Connect.")
        if not isinstance(cam, GenericCamera):
            raise ValueError(f"Invalid Camera handle supplied to Capture block: expected GenericCamera instance, got {type(cam).__name__}.")

        frame = await asyncio.to_thread(cam.read_frame)
        self._last_frame = frame
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Frame":
            return self._last_frame
        elif pin_name == "Camera":
            return await context.pull(self.id, "Camera")
        return None
