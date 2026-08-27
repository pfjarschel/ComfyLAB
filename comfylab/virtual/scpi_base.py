# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Base class for pure-Python, headless virtual SCPI socket instruments.
Handles TCP server lifecycle, client thread management, command parsing,
and IEEE 488.2 / SCPI dispatch.
"""

import socket
import threading
import logging
import re
from typing import Dict, Callable, Any, Optional, List, Union

logger = logging.getLogger("comfylab.virtual.scpi_base")


class VirtualSCPIInstrument:
    """
    Threaded TCP Socket server implementing standard SCPI command dispatch.
    Zero GUI / Qt dependencies.
    """

    def __init__(self, port: int, name: str = "Virtual Instrument", verbose: bool = False):
        self.port = port
        self.name = name
        self.verbose = verbose
        self.listen_ip = "127.0.0.1"
        self._server_running = False
        self._server_socket: Optional[socket.socket] = None
        self._server_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # Command lookup tables:
        # Exact match or normalized SCPI commands: { normalized_command: handler_callable }
        self._scpi_commands: Dict[str, Callable[[List[str]], Any]] = {}
        self._scpi_queries: Dict[str, Callable[[List[str]], Any]] = {}

        # Register standard IEEE 488.2 commands
        self.register_query("*IDN?", self._handle_idn)
        self.register_command("*RST", self._handle_rst)
        self.register_command("*CLS", self._handle_cls)
        self.register_query("*OPC?", lambda args: "1")
        self.register_command("*OPC", lambda args: None)
        self.register_query("*ESR?", lambda args: "0")
        self.register_query("*STB?", lambda args: "0")
        self.register_command("*WAI", lambda args: None)

    def register_command(self, pattern: str, handler: Callable[[List[str]], Any]) -> None:
        """Registers a write/set command handler."""
        key = self._normalize_pattern(pattern)
        self._scpi_commands[key] = handler

    def register_query(self, pattern: str, handler: Callable[[List[str]], Any]) -> None:
        """Registers a query (? ending) handler."""
        key = self._normalize_pattern(pattern)
        if not key.endswith("?"):
            key += "?"
        self._scpi_queries[key] = handler

    @staticmethod
    def _normalize_pattern(pattern: str) -> str:
        """Normalizes command string by stripping leading colons, whitespace and lowercasing."""
        p = pattern.strip().lower()
        if p.startswith(":"):
            p = p[1:]
        return p

    def get_idn(self) -> str:
        """Subclasses should override to return their standard 4-field IEEE 488.2 IDN string."""
        return f"ComfyLAB,Virtual {self.name},V1,1.0.0"

    def reset(self) -> None:
        """Subclasses should override to reset their internal state."""
        pass

    def _handle_idn(self, args: List[str]) -> str:
        return self.get_idn()

    def _handle_rst(self, args: List[str]) -> None:
        with self._lock:
            self.reset()

    def _handle_cls(self, args: List[str]) -> None:
        pass

    def start(self, listen_ip: str = "127.0.0.1") -> None:
        """Starts the TCP socket listener in a background thread."""
        with self._lock:
            if self._server_running:
                return
            self.listen_ip = listen_ip
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((self.listen_ip, self.port))
            self._server_socket.listen(16)
            self._server_running = True

            self._server_thread = threading.Thread(
                target=self._accept_loop,
                name=f"SCPI-{self.name}-{self.port}",
                daemon=True
            )
            self._server_thread.start()
            logger.info(f"[{self.name}] Listening on {self.listen_ip}:{self.port}")

    def close(self) -> None:
        """Stops the TCP server and closes all active sockets."""
        with self._lock:
            if not self._server_running:
                return
            self._server_running = False
            if self._server_socket:
                try:
                    self._server_socket.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    self._server_socket.close()
                except Exception:
                    pass
                self._server_socket = None
            logger.info(f"[{self.name}] Server on port {self.port} closed.")

    def _accept_loop(self) -> None:
        while self._server_running and self._server_socket:
            try:
                conn, addr = self._server_socket.accept()
                t = threading.Thread(
                    target=self._client_loop,
                    args=(conn, addr),
                    name=f"SCPIClient-{addr[0]}:{addr[1]}",
                    daemon=True
                )
                t.start()
            except Exception:
                if not self._server_running:
                    break

    def _client_loop(self, conn: socket.socket, addr: Any) -> None:
        if self.verbose:
            logger.debug(f"[{self.name}] Client connected from {addr}")
        conn.settimeout(None)
        buffer = b""

        try:
            while self._server_running:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                buffer += chunk

                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line_str = line.decode("latin1", errors="replace").strip()
                    if not line_str:
                        continue

                    # SCPI commands can be separated by semicolons
                    sub_commands = self._split_scpi_commands(line_str)
                    for cmd in sub_commands:
                        resp = self._process_command(cmd)
                        if resp is not None:
                            if isinstance(resp, bytes):
                                conn.sendall(resp)
                            else:
                                out_str = f"{resp}\n".encode("latin1")
                                conn.sendall(out_str)
        except Exception as e:
            if self._server_running and self.verbose:
                logger.debug(f"[{self.name}] Client connection {addr} ended: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def _split_scpi_commands(raw_line: str) -> List[str]:
        """Splits multi-command lines by semicolons, taking quotes into account."""
        commands = []
        current = []
        in_quotes = False
        quote_char = ""

        for char in raw_line:
            if char in ('"', "'"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                current.append(char)
            elif char == ";" and not in_quotes:
                cmd_str = "".join(current).strip()
                if cmd_str:
                    commands.append(cmd_str)
                current = []
            else:
                current.append(char)

        last_cmd = "".join(current).strip()
        if last_cmd:
            commands.append(last_cmd)
        return commands

    def _process_command(self, full_cmd: str) -> Optional[Union[str, bytes]]:
        """Parses and executes a single SCPI command or query string."""
        with self._lock:
            # Separate command header and arguments (separated by space)
            full_cmd = full_cmd.strip()
            if not full_cmd:
                return None

            parts = full_cmd.split(None, 1)
            header = parts[0].strip()
            args_str = parts[1].strip() if len(parts) > 1 else ""

            # Extract arguments (comma-separated or single)
            args = []
            if args_str:
                # Comma separated arguments
                args = [a.strip().strip('"\'') for a in args_str.split(",") if a.strip()]

            is_query = header.endswith("?")
            norm_header = self._normalize_pattern(header)

            if is_query:
                handler = self._find_handler(norm_header, self._scpi_queries)
                if handler:
                    try:
                        return handler(args)
                    except Exception as e:
                        logger.error(f"[{self.name}] Error executing query '{full_cmd}': {e}")
                        return "0"
                else:
                    logger.warning(f"[{self.name}] Unrecognized query: '{full_cmd}' (norm: '{norm_header}')")
                    return "0"
            else:
                handler = self._find_handler(norm_header, self._scpi_commands)
                if handler:
                    try:
                        handler(args)
                    except Exception as e:
                        logger.error(f"[{self.name}] Error executing command '{full_cmd}': {e}")
                else:
                    logger.warning(f"[{self.name}] Unrecognized command: '{full_cmd}' (norm: '{norm_header}')")
                return None

    def _find_handler(
        self, norm_header: str, lookup: Dict[str, Callable[[List[str]], Any]]
    ) -> Optional[Callable[[List[str]], Any]]:
        """
        Attempts exact match, then flexible SCPI matching (e.g. chan1 matching channel1,
        sour1 matching source1, timebase matching tim).
        """
        if norm_header in lookup:
            return lookup[norm_header]

        # Try mapping common standard abbreviations
        canonical = self._canonicalize_scpi(norm_header)
        if canonical in lookup:
            return lookup[canonical]

        # Prefix matching for flexible short/long SCPI keywords
        for pattern, handler in lookup.items():
            if self._scpi_matches(norm_header, pattern):
                return handler

        return None

    @classmethod
    def _canonicalize_scpi(cls, header: str) -> str:
        """Normalizes common standard SCPI abbreviations."""
        h = header
        # Subsystem normalizations (single-pass regex to avoid re-substituting prefixes)
        h = re.sub(r"^(?:channel|chan|c)([1-4])(?=:|$)", r"channel\1", h)
        h = re.sub(r"^(?:source|sour)([1-4]?)", r"source\1", h)
        h = re.sub(r"^(?:output|outp|out)([1-4]?)", r"output\1", h)
        h = re.sub(r"^(?:timebase|tim)(?=:|$)", r"timebase", h)
        h = re.sub(r"^(?:acquire|acq)(?=:|$)", r"acquire", h)
        h = re.sub(r"^(?:waveform|wav)(?=:|$)", r"waveform", h)
        h = re.sub(r"^(?:trigger|trig)(?=:|$)", r"trigger", h)

        # Parameter normalizations
        h = h.replace(":scal", ":scale")
        h = h.replace(":pos", ":position")
        h = h.replace(":offs", ":offset")
        h = h.replace(":disp", ":display")
        h = h.replace(":enab", ":enable")
        h = h.replace(":coup", ":coupling")
        h = h.replace(":freq", ":frequency")
        h = h.replace(":volt", ":voltage")
        h = h.replace(":func", ":function")
        h = h.replace(":stat", ":state")
        h = h.replace(":sour", ":source")
        h = h.replace(":form", ":format")
        h = h.replace(":poin", ":points")
        return h

    @classmethod
    def _scpi_matches(cls, incoming: str, registered: str) -> bool:
        """Checks whether an incoming SCPI path matches a registered pattern."""
        in_nodes = incoming.split(":")
        reg_nodes = registered.split(":")
        if len(in_nodes) != len(reg_nodes):
            return False

        for in_node, reg_node in zip(in_nodes, reg_nodes):
            in_q = in_node.endswith("?")
            reg_q = reg_node.endswith("?")
            if in_q != reg_q:
                return False
            in_clean = in_node.rstrip("?")
            reg_clean = reg_node.rstrip("?")

            # Match channel numbers like c1 -> channel1
            m_in = re.match(r"^(?:c|chan|channel)(\d+)$", in_clean)
            m_reg = re.match(r"^channel(\d+)$", reg_clean)
            if m_in and m_reg:
                if m_in.group(1) != m_reg.group(1):
                    return False
                continue

            # Match source numbers like sour1 -> source1
            m_in_s = re.match(r"^(?:sour|source)(\d*)$", in_clean)
            m_reg_s = re.match(r"^source(\d*)$", reg_clean)
            if m_in_s and m_reg_s:
                s1 = m_in_s.group(1) or "1"
                s2 = m_reg_s.group(1) or "1"
                if s1 != s2:
                    return False
                continue

            # Prefix abbreviation (e.g. freq matches frequency, amp matches amplitude)
            if not (reg_clean.startswith(in_clean) or in_clean.startswith(reg_clean)):
                return False

        return True
