# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Virtual Instruments Process Lifecycle Manager.
Ensures a singleton background process runs the virtual instrument servers,
prevents duplicate processes, tracks active connections, and performs clean teardown.
"""

import sys
import os
import time
import socket
import atexit
import logging
import subprocess
import threading
from typing import Optional, Set

logger = logging.getLogger("comfylab.virtual.manager")

DEFAULT_OSC_PORT = 51234
DEFAULT_SIGGEN_PORT = 51235
DEFAULT_RC_PORT = 51236


class VirtualInstrumentManager:
    """
    Singleton manager responsible for spawning, checking, and terminating
    the background virtual instruments server process.
    """

    _lock = threading.Lock()
    _process: Optional[subprocess.Popen] = None
    _clients: Set[str] = set()

    @classmethod
    def is_port_open(cls, port: int = DEFAULT_OSC_PORT, host: str = "127.0.0.1", timeout: float = 0.2) -> bool:
        """Checks whether a TCP port is open and accepting connections."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, ConnectionRefusedError):
            return False

    @classmethod
    def is_running(cls) -> bool:
        """Returns True if the server process is alive and responsive on the primary port."""
        with cls._lock:
            if cls._process is not None:
                if cls._process.poll() is None:
                    return cls.is_port_open(DEFAULT_OSC_PORT)
                else:
                    cls._process = None

            # Process handle might not be stored (e.g. spawned externally), check port
            return cls.is_port_open(DEFAULT_OSC_PORT)

    @classmethod
    def ensure_started(cls, timeout: float = 5.0) -> bool:
        """
        Ensures the virtual instruments server is running.
        Spawns a background subprocess if not already running.
        Guarantees no duplicate processes are created.
        """
        with cls._lock:
            # 1. Check if already running and responsive
            if cls._process is not None and cls._process.poll() is None:
                if cls.is_port_open(DEFAULT_OSC_PORT):
                    return True

            if cls.is_port_open(DEFAULT_OSC_PORT):
                logger.info("Virtual instruments server already active on port 51234.")
                return True

            # 2. Spawn a new subprocess
            logger.info("Spawning ComfyLAB Virtual Instruments server subprocess...")
            env = dict(os.environ)
            # Ensure python path includes project src
            src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            existing_pp = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{existing_pp}" if existing_pp else src_dir

            cmd = [sys.executable, "-m", "comfylab.virtual.server"]
            cls._process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 3. Wait for socket to become ready
            start_time = time.time()
            while time.time() - start_time < timeout:
                if cls.is_port_open(DEFAULT_OSC_PORT):
                    logger.info(f"ComfyLAB Virtual Instruments server running (PID: {cls._process.pid}).")
                    return True
                if cls._process.poll() is not None:
                    stderr = cls._process.stderr.read() if cls._process.stderr else ""
                    logger.error(f"Virtual instruments server exited prematurely: {stderr}")
                    cls._process = None
                    return False
                time.sleep(0.05)

            logger.error(f"Timed out waiting for virtual instruments server on port {DEFAULT_OSC_PORT}.")
            return False

    @classmethod
    def register_client(cls, client_id: str) -> None:
        """Registers an active connection block using the virtual instruments."""
        with cls._lock:
            cls._clients.add(client_id)
            logger.debug(f"Registered virtual instrument client '{client_id}'. Active count: {len(cls._clients)}")

    @classmethod
    def unregister_client(cls, client_id: str, auto_stop: bool = True) -> None:
        """
        Unregisters a connection block upon teardown.
        If no clients remain, terminates the background process.
        """
        with cls._lock:
            cls._clients.discard(client_id)
            logger.debug(f"Unregistered virtual instrument client '{client_id}'. Remaining: {len(cls._clients)}")
            if len(cls._clients) == 0 and auto_stop:
                cls._stop_internal()

    @classmethod
    def stop(cls) -> None:
        """Stops the virtual instruments server process."""
        with cls._lock:
            cls._clients.clear()
            cls._stop_internal()

    @classmethod
    def _stop_internal(cls) -> None:
        if cls._process is not None:
            logger.info(f"Stopping ComfyLAB Virtual Instruments server (PID: {cls._process.pid})...")
            try:
                cls._process.terminate()
                try:
                    cls._process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    cls._process.kill()
                    cls._process.wait(timeout=1.0)
            except Exception as e:
                logger.error(f"Error terminating virtual instruments server: {e}")
            finally:
                cls._process = None
                logger.info("Virtual Instruments server process stopped.")


# Register cleanup at Python process exit
atexit.register(VirtualInstrumentManager.stop)
