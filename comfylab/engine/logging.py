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

import os
import sys
import json
import logging
import logging.handlers
from pathlib import Path
import contextvars
import inspect

# Context variables for storing execution context dynamically
run_id_var = contextvars.ContextVar("run_id", default="")
node_id_var = contextvars.ContextVar("node_id", default="")
node_name_var = contextvars.ContextVar("node_name", default="")
node_file_var = contextvars.ContextVar("node_file", default="")

class StructuredLoggingFilter(logging.Filter):
    """
    Filter to inject run_id, node_id, node_name, and node_file from contextvars into each LogRecord.
    """
    def filter(self, record):
        record.run_id = run_id_var.get() or "N/A"
        node_id = node_id_var.get()
        node_name = node_name_var.get()
        node_file = node_file_var.get()
        
        record.node_id = node_id or "N/A"
        record.node_name = node_name or "N/A"
        record.node_file = node_file or "N/A"
        
        if node_id:
            record.node_info = f"{node_id} ({node_name} in {node_file})"
        else:
            record.node_info = "N/A"
        return True

class JsonFormatter(logging.Formatter):
    """
    Formatter that converts LogRecords into a structured JSON string.
    """
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", "N/A"),
            "node_id": getattr(record, "node_id", "N/A"),
            "node_name": getattr(record, "node_name", "N/A"),
            "node_file": getattr(record, "node_file", "N/A")
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    """
    Initializes root-level logging for ComfyLAB.
    Sets up human-readable console logging and rolling JSON file logging under ~/.comfylab/logs/comfylab.log.
    Levels are configured dynamically from environment variables:
      - COMFYLAB_LOG_LEVEL (default: INFO) -> sets base logging level
      - COMFYLAB_CONSOLE_LEVEL (default: WARNING) -> sets terminal verbosity
      - COMFYLAB_FILE_LEVEL (default: INFO) -> sets log file verbosity
    Fallback check for uvicorn's '--log-level' CLI argument is also supported.
    """
    base_dir = Path.home() / ".comfylab"
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = logs_dir / "comfylab.log"

    # 1. Determine base and handler log levels
    # Check uvicorn cli override first
    uvicorn_level_name = None
    for i, arg in enumerate(sys.argv):
        if arg == "--log-level" and i + 1 < len(sys.argv):
            uvicorn_level_name = sys.argv[i + 1].upper()

    default_base_level = uvicorn_level_name or os.environ.get("COMFYLAB_LOG_LEVEL", "INFO").upper()
    default_console_level = uvicorn_level_name or os.environ.get("COMFYLAB_CONSOLE_LEVEL", "WARNING").upper()
    default_file_level = os.environ.get("COMFYLAB_FILE_LEVEL", "INFO").upper()

    valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    
    base_level = getattr(logging, default_base_level) if default_base_level in valid_levels else logging.INFO
    console_level = getattr(logging, default_console_level) if default_console_level in valid_levels else logging.WARNING
    file_level = getattr(logging, default_file_level) if default_file_level in valid_levels else logging.INFO

    root_logger = logging.getLogger()
    # Force base level to lowest of requested levels to allow proper filtering at handlers
    root_logger.setLevel(min(base_level, console_level, file_level))

    # Clean existing handlers on root logger
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    structured_filter = StructuredLoggingFilter()

    # 2. Console Stream Handler (Human-readable text with detailed node info)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | [Run: %(run_id)s] [Node: %(node_info)s] | %(name)s | %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(structured_filter)
    root_logger.addHandler(console_handler)

    # 3. Rotating File Handler (Structured JSON format)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(file_level)
    file_formatter = JsonFormatter()
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(structured_filter)
    root_logger.addHandler(file_handler)

    # Prevent spam from default library loggers
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Enable our package loggers to propagate cleanly
    logging.getLogger("comfylab").setLevel(base_level)
    logging.getLogger("backend").setLevel(base_level)

    logging.getLogger("comfylab.engine.logging").info(
        f"Structured logging system initialized. File path: {log_file_path} "
        f"(Console level: {logging.getLevelName(console_level)}, File level: {logging.getLevelName(file_level)})"
    )

def set_node_context(node):
    """
    Sets node context variables for logging from the given node instance.
    Returns a tuple of context tokens to be used with reset_node_context.
    """
    if not node:
        return (
            node_id_var.set(""),
            node_name_var.set(""),
            node_file_var.set("")
        )
    
    node_id = getattr(node, "id", "")
    node_name = getattr(node, "display_name", "") or node.__class__.__name__
    
    # Resolve node python file path
    file_path = "Unknown"
    if hasattr(node, "_macro_file_path") and node._macro_file_path:
        file_path = node._macro_file_path
    else:
        try:
            file_path = inspect.getfile(node.__class__)
        except Exception:
            pass
            
    # Normalize path relative to project root
    if file_path and file_path != "Unknown":
        try:
            rel_path = os.path.relpath(file_path)
            if not rel_path.startswith(".."):
                file_path = rel_path
        except Exception:
            pass
            
    return (
        node_id_var.set(node_id),
        node_name_var.set(node_name),
        node_file_var.set(file_path)
    )

def reset_node_context(tokens):
    """
    Resets the contextvars to their values before set_node_context was called.
    """
    if tokens:
        node_id_var.reset(tokens[0])
        node_name_var.reset(tokens[1])
        node_file_var.reset(tokens[2])
