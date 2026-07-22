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

import time
import logging
from collections import defaultdict

logger = logging.getLogger("backend.ratelimit")

MAX_FAILURES = 6
WINDOW_SECONDS = 30
BLOCK_BASE_SECONDS = 120
BLOCK_EXTRA_PER_ATTEMPT = 30
MAX_TRACKED_IPS = 10000

_failures = defaultdict(list)
_blocks = {}
_extra_blocks = {}


def _prune(now):
    """Drops stale entries so spoofed/rotating IPs can't grow the dicts unboundedly."""
    if len(_failures) + len(_blocks) <= MAX_TRACKED_IPS:
        return
    for ip in list(_failures.keys()):
        _failures[ip] = [t for t in _failures[ip] if now - t < WINDOW_SECONDS]
        if not _failures[ip]:
            del _failures[ip]
    for ip in list(_blocks.keys()):
        if now >= _blocks[ip]:
            del _blocks[ip]
            _extra_blocks.pop(ip, None)
    # Still over capacity: drop the oldest tracked failures outright
    if len(_failures) > MAX_TRACKED_IPS:
        for ip in list(_failures.keys())[: len(_failures) - MAX_TRACKED_IPS]:
            del _failures[ip]

def is_blocked(ip):
    now = time.time()
    if ip in _blocks:
        if now < _blocks[ip]:
            return True
        del _blocks[ip]
        _failures.pop(ip, None)
        _extra_blocks.pop(ip, None)
    return False

def block_remaining(ip):
    if ip in _blocks:
        rem = _blocks[ip] - time.time()
        if rem > 0:
            return int(rem)
    return 0

def is_first_attempt(ip):
    return ip not in _blocks and len(_failures.get(ip, [])) == 0

def remaining_attempts(ip):
    if ip in _blocks:
        return 0
    now = time.time()
    recent = [t for t in _failures.get(ip, []) if now - t < WINDOW_SECONDS]
    return max(0, MAX_FAILURES - len(recent))

def record_failure(ip):
    now = time.time()
    _prune(now)

    if ip in _blocks:
        # Already blocked — reset timer and increase penalty
        _extra_blocks[ip] = _extra_blocks.get(ip, 0) + 1
        extra = _extra_blocks[ip] * BLOCK_EXTRA_PER_ATTEMPT
        total = BLOCK_BASE_SECONDS + extra
        _blocks[ip] = now + total
        logger.warning(f"Rate-limit block extended for IP {ip}: {total}s (retry #{_extra_blocks[ip]} while blocked)")
        return

    _failures[ip].append(now)
    _failures[ip] = [t for t in _failures[ip] if now - t < WINDOW_SECONDS]
    count = len(_failures[ip])
    if count >= MAX_FAILURES:
        _blocks[ip] = now + BLOCK_BASE_SECONDS
        _extra_blocks.pop(ip, None)
        del _failures[ip]
        logger.warning(f"Rate-limit block activated for IP {ip} ({BLOCK_BASE_SECONDS}s after {MAX_FAILURES} failed attempts)")
    else:
        attempts_left = MAX_FAILURES - count
        logger.info(f"Auth failure from IP {ip}: {attempts_left} attempt(s) remaining before block")

def record_success(ip):
    _failures.pop(ip, None)
    _blocks.pop(ip, None)
    _extra_blocks.pop(ip, None)
