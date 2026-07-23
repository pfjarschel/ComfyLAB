# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Generic OpenCV Camera / Webcam Driver.
Pure Python — no ComfyLAB UI or block dependencies.
Supports standard USB Webcams, UVC cameras, and frame grabbers via OpenCV.
"""

from typing import Any, Tuple, Optional
import numpy as np

try:
    import cv2
    OPENCV_AVAILABLE = True
except Exception:
    OPENCV_AVAILABLE = False


class GenericCamera:
    """
    Driver for standard USB / UVC cameras, webcams, and frame grabbers via OpenCV.
    """

    def __init__(self, camera_index: int = 0):
        if not OPENCV_AVAILABLE:
            raise RuntimeError("The 'opencv-python' (cv2) package is not installed on this system.")

        self.index = camera_index
        # Try default backend first
        self.cap = cv2.VideoCapture(camera_index)
        # On Linux, fallback to explicit V4L2 backend if default backend failed
        if not self.cap.isOpened() and hasattr(cv2, "CAP_V4L2"):
            self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera at index {camera_index}. Ensure camera hardware is connected and permissions are granted.")

    def is_opened(self) -> bool:
        """Returns True if camera capture session is open and active."""
        return self.cap is not None and self.cap.isOpened()

    def set_resolution(self, width: int = 640, height: int = 480) -> None:
        """Sets capture frame resolution."""
        if self.cap:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read_frame(self) -> np.ndarray:
        """Captures single frame image array (BGR numpy array of shape (H, W, 3))."""
        if not self.is_opened():
            raise RuntimeError("Camera capture stream is not open.")
        
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("Failed to capture image frame from camera.")
        return frame

    def close(self) -> None:
        """Releases camera capture hardware."""
        if self.cap:
            self.cap.release()
            self.cap = None

