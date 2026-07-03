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
import time
import logging
from typing import Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger("comfylab.engine.locks")

class ResourceLockManager:
    """
    Manages mutually exclusive access to VISA resource addresses.
    Keeps track of lock contentions, wait times, and active locks.
    """
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock_stats: Dict[str, Dict[str, Any]] = {}
        self._global_stats = {
            "contentions": 0,
            "total_wait_time": 0.0,
            "total_acquires": 0
        }

    def _get_lock(self, address: str) -> asyncio.Lock:
        if address not in self._locks:
            self._locks[address] = asyncio.Lock()
            self._lock_stats[address] = {
                "contentions": 0,
                "total_wait_time": 0.0,
                "acquires": 0
            }
        return self._locks[address]

    @asynccontextmanager
    async def acquire(self, address: str, timeout: float = 30.0):
        """
        Asynchronously acquires a lock for a specific VISA address with a timeout.
        Updates statistics on contentions and waiting times.
        """
        lock = self._get_lock(address)
        stats = self._lock_stats[address]
        
        start_time = time.monotonic()
        locked = False
        
        if lock.locked():
            stats["contentions"] += 1
            self._global_stats["contentions"] += 1
            logger.info(f"Lock contention detected for VISA resource address '{address}'")
            
        try:
            await asyncio.wait_for(lock.acquire(), timeout=timeout)
            locked = True
            
            wait_time = time.monotonic() - start_time
            stats["total_wait_time"] += wait_time
            stats["acquires"] += 1
            self._global_stats["total_wait_time"] += wait_time
            self._global_stats["total_acquires"] += 1
            
            if wait_time > 5.0:
                logger.warning(
                    f"VISA resource lock acquisition for '{address}' took {wait_time:.2f}s "
                    "(exceeded 5s diagnostic threshold)."
                )
            
            yield
        finally:
            if locked:
                lock.release()

    def get_stats(self) -> Dict[str, Any]:
        """Returns lock acquisition and contention statistics."""
        return {
            "global": self._global_stats.copy(),
            "resources": {addr: stats.copy() for addr, stats in self._lock_stats.items()}
        }
