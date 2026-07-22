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
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger("backend.manager")

class TelemetryConnectionManager:
    """
    Manages active WebSocket connections grouped by execution run_id.
    Handles connection acceptance, disconnection, and message broadcasting.
    """
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, run_id: str, websocket: WebSocket):
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
        self.active_connections[run_id].append(websocket)
        logger.info(f"WebSocket client connected to run_id: {run_id}")

    def disconnect(self, run_id: str, websocket: WebSocket):
        if run_id in self.active_connections:
            if websocket in self.active_connections[run_id]:
                self.active_connections[run_id].remove(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]
        logger.info(f"WebSocket client disconnected from run_id: {run_id}")

    async def broadcast(self, run_id: str, message: Any):
        """Sends a JSON or binary message to all active WebSocket clients for a run_id."""
        if run_id in self.active_connections:
            # Iterate over a copy to prevent mutation issues if a client disconnects during send
            for websocket in list(self.active_connections[run_id]):
                try:
                    if isinstance(message, bytes):
                        await websocket.send_bytes(message)
                    else:
                        await websocket.send_json(message)
                except Exception:
                    # Clean up dead connection
                    self.disconnect(run_id, websocket)
