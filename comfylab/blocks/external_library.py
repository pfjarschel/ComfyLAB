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

"""
ComfyLAB DLL/SO Library Bridge Blocks

Provides a safe, zero-boilerplate bridge between ComfyLAB graphs and native
shared libraries (.dll on Windows, .so on Linux) via Python's ctypes module.

Blocks:
  - library/load : Loads a shared library and outputs its handle.
  - library/call : Calls a named function using a user-configured argument
                   signature, handling all ctypes mechanics transparently.

Design Guardrails:
  A) Thread isolation  — all blocking C calls run in asyncio.to_thread() so
     they never stall the main async execution loop.
  B) Buffer bounds     — allocation sizes are validated before every C call;
                         an explicit, readable error is raised if violated.
"""

import asyncio
import ctypes
import logging
import sys
from typing import Any, Dict, List, Optional

from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext

logger = logging.getLogger("comfylab.blocks.external_library")


# ---------------------------------------------------------------------------
# Type mapping tables
# ---------------------------------------------------------------------------

# Maps the user-facing type-name strings to the corresponding ctypes types.
CTYPE_MAP: Dict[str, Any] = {
    "int8":    ctypes.c_int8,
    "uint8":   ctypes.c_uint8,
    "int16":   ctypes.c_int16,
    "uint16":  ctypes.c_uint16,
    "int32":   ctypes.c_int32,
    "uint32":  ctypes.c_uint32,
    "int64":   ctypes.c_int64,
    "uint64":  ctypes.c_uint64,
    "float32": ctypes.c_float,
    "float64": ctypes.c_double,
    "bool":    ctypes.c_bool,
    "c_char_p": ctypes.c_char_p,
}

# Extended map that also covers "void" (None restype).
RETURN_TYPE_MAP: Dict[str, Any] = {
    "void": None,
    **CTYPE_MAP,
}

# All valid C-type option strings for the frontend dropdown.
C_TYPE_OPTIONS = list(CTYPE_MAP.keys())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_library(path: str) -> ctypes.CDLL:
    """
    Load a shared library transparently, auto-detecting calling convention.

    On Linux / macOS, ctypes.CDLL (cdecl) is always used.
    On Windows, tries cdecl first, then falls back to stdcall (WinDLL) if the
    initial load raises an OSError — which happens with some vendor SDKs that
    are compiled with the __stdcall convention.
    """
    try:
        lib = ctypes.CDLL(path)
        logger.debug(f"[Library] Loaded library '{path}' via CDLL (cdecl).")
        return lib
    except OSError as e:
        if sys.platform == "win32":
            try:
                lib = ctypes.WinDLL(path)
                logger.debug(f"[Library] Loaded library '{path}' via WinDLL (stdcall fallback).")
                return lib
            except OSError:
                pass
        raise ValueError(
            f"Load DLL/SO: Could not load '{path}'. "
            f"Check that the path is correct and the file is a valid shared library. "
            f"Original error: {e}"
        )


def _coerce_value(val: Any, c_type_str: str) -> Any:
    """
    Coerce a Python value to be compatible with the target C type constructor.
    Specifically, float values must be converted to int before passing to ctypes
    integer types in Python 3.13+, which raises TypeErrors for float inputs.
    """
    if c_type_str in ("int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"):
        if val is None:
            return 0
        try:
            return int(float(val))
        except (TypeError, ValueError):
            return 0
    elif c_type_str == "bool":
        return bool(val) if val is not None else False
    elif c_type_str == "c_char_p":
        if val is None:
            return None
        if isinstance(val, str):
            return val.encode("utf-8")
        return val
    else:
        # float32, float64
        if val is None:
            return 0.0
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0


# ---------------------------------------------------------------------------
# Block 1 — Library Loader
# ---------------------------------------------------------------------------

@register_block(r"dll\/SO/load")
class LibraryLoadBlock(BaseBlock):
    """
    Loads a native shared library (.dll / .so) and outputs a handle for use
    with Library Call blocks. Calling convention (cdecl vs stdcall) is detected
    automatically — the user only needs to supply the file path.

    The library handle is cached for the duration of the graph run and
    released automatically on teardown, consistent with VISA device blocks.
    """
    icon = "🔗"
    display_name = "Load DLL/SO"
    description = (
        "Loads a native shared library (.dll on Windows, .so on Linux) and "
        "outputs the handle. Connect to a 'Call DLL/SO' block to invoke functions."
    )

    inputs_def = [
        ExecIn("Load"),
        DataIn("LibraryPath", type_hint=str, default="", widget="text"),
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Library", type_hint=Any),
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._lib: Optional[ctypes.CDLL] = None
        self._loaded_path: Optional[str] = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        path = await context.pull(self.id, "LibraryPath")
        if not path:
            raise ValueError("Load DLL/SO: 'LibraryPath' must not be empty.")

        # Reload only if path changed since last run step
        if self._lib is None or self._loaded_path != path:
            logger.info(f"[LibraryLoad '{self.id}'] Loading library: {path}")
            # Run potentially blocking OS loader in a worker thread (Guardrail A)
            self._lib = await asyncio.to_thread(_load_library, path)
            self._loaded_path = path
            logger.info(f"[LibraryLoad '{self.id}'] Library loaded successfully.")
        else:
            logger.debug(f"[LibraryLoad '{self.id}'] Reusing cached handle for: {path}")

        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Library":
            return self._lib
        return None

    async def teardown(self):
        if self._lib is not None:
            logger.info(f"[LibraryLoad '{self.id}'] Releasing library handle.")
            self._lib = None
            self._loaded_path = None


# ---------------------------------------------------------------------------
# Block 2 — Function Call
# ---------------------------------------------------------------------------

@register_block(r"dll\/SO/call")
class LibraryCallBlock(BaseBlock):
    """
    Invokes a named function from a loaded native library handle.

    The argument signature is configured via the 'library_args' property (set
    through the dedicated Library Signature Editor panel in the frontend). Each
    argument entry has:
        name      — matches the DataIn/DataOut pin name on this block
        c_type    — one of the supported ctypes type strings (e.g. "float32")
        direction — one of:
                      "in"    Input         (input pin only)
                      "out"   Output        (output pin; scalar pointer if
                                             size_arg is blank, array buffer
                                             if size_arg names an input arg)
                      "inout" Input/Output  (input pin + output pin; array
                                             buffer modified in-place)
        size_arg  — (only for "out" with a buffer) the name of the Input
                    argument that holds the element count.

    All ctypes pointer mechanics are handled transparently. The C call runs
    in a worker thread (Guardrail A). Buffer sizes are validated before the
    call (Guardrail B).
    """
    icon = "⚡"
    display_name = "Call DLL/SO"
    description = (
        "Calls a function in a loaded native library using a configurable "
        "argument signature. Click '⚙️ Edit Signature' on the block to define "
        "the function's arguments and their C types."
    )

    # Static pins always present on every Library Call block instance.
    inputs_def = [
        ExecIn("Call"),
        DataIn("Library", type_hint=Any),
        DataIn("FunctionName", type_hint=str, default="myFunction", widget="text"),
        DataIn("ReturnType", type_hint=str, default="void", widget="dropdown",
               options=["void"] + C_TYPE_OPTIONS),
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("ReturnValue", type_hint=Any),
        DataOut("Status", type_hint=int),
    ]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._outputs: Dict[str, Any] = {}

        # Build dynamic pins from the stored library_args property (or backward-compatible ffi_args).
        library_args = self.properties.get("library_args")
        if library_args is None:
            library_args = self.properties.get("ffi_args", [])
            
        for arg in library_args:
            name = arg.get("name", "").strip()
            direction = arg.get("direction", "in")
            if not name:
                continue

            if direction == "in":
                self.inputs[name] = DataIn(name, type_hint=Any)

            elif direction in ("out", "out_buffer", "out_ptr"):
                # "out" with size_arg → list; without → scalar Any
                out_hint = list if (arg.get("size_arg", "").strip() or direction == "out_buffer") else Any
                self.outputs[name] = DataOut(name, type_hint=out_hint)

            elif direction in ("inout", "inout_buffer"):
                # Both a DataIn (the initial array) and a DataOut (modified array)
                self.inputs[name] = DataIn(name, type_hint=list)
                self.outputs[name] = DataOut(name, type_hint=list)

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        # --- Pull static inputs ---
        lib = await context.pull(self.id, "Library")
        func_name = await context.pull(self.id, "FunctionName")
        return_type_str = (await context.pull(self.id, "ReturnType")) or "void"

        if lib is None:
            raise ValueError(
                "Call DLL/SO: No library handle. Connect a 'Load DLL/SO' block to the 'Library' input."
            )
        if not func_name or not func_name.strip():
            raise ValueError("Call DLL/SO: 'FunctionName' must not be empty.")

        func_name = func_name.strip()

        # --- Resolve function symbol from library ---
        try:
            lib_func = getattr(lib, func_name)
        except AttributeError:
            raise ValueError(
                f"Call DLL/SO: Function '{func_name}' was not found in the loaded library. "
                f"Check the symbol name (it is case-sensitive)."
            )

        # --- Set return type ---
        if return_type_str not in RETURN_TYPE_MAP:
            raise ValueError(
                f"Call DLL/SO: Unknown return type '{return_type_str}'. "
                f"Supported types: {list(RETURN_TYPE_MAP.keys())}"
            )
        lib_func.restype = RETURN_TYPE_MAP[return_type_str]

        # --- Process library_args: build ctypes argument list ---
        library_args = self.properties.get("library_args")
        if library_args is None:
            library_args = self.properties.get("ffi_args", [])

        # We pre-pull all "in" values we might need for size_arg lookups.
        # Map of arg name → pulled Python value for "in" direction.
        pulled_inputs: Dict[str, Any] = {}

        # First pass: pull all "in" values (needed to resolve size_arg for buffers)
        for arg in library_args:
            name = arg.get("name", "").strip()
            direction = arg.get("direction", "in")
            if not name:
                continue
            if direction == "in":
                pulled_inputs[name] = await context.pull(self.id, name)
            elif direction in ("inout", "inout_buffer"):
                pulled_inputs[name] = await context.pull(self.id, name)

        c_args: List[Any] = []
        argtypes: List[Any] = []
        # Records what needs to be unpacked after the call.
        # Entries: (direction, name, buffer_object, size)
        output_records: List[tuple] = []

        for arg in library_args:
            name = arg.get("name", "").strip()
            direction = arg.get("direction", "in")
            c_type_str = arg.get("c_type", "int32")
            size_arg = arg.get("size_arg", "").strip()

            if not name:
                continue

            if c_type_str not in CTYPE_MAP:
                raise ValueError(
                    f"Call DLL/SO: Unknown C type '{c_type_str}' for argument '{name}'. "
                    f"Supported types: {C_TYPE_OPTIONS}"
                )
            c_type = CTYPE_MAP[c_type_str]

            # ---- Input (by value) ----
            if direction == "in":
                val = pulled_inputs.get(name)
                coerced = _coerce_value(val, c_type_str)
                try:
                    if c_type_str == "c_char_p":
                        c_val = ctypes.c_char_p(coerced)
                    else:
                        c_val = c_type(coerced)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Call DLL/SO: Cannot convert input '{name}' value {val!r} "
                        f"to C type '{c_type_str}': {exc}"
                    )
                c_args.append(c_val)
                argtypes.append(c_type)

            # ---- Output — scalar pointer (no size_arg) or array buffer (size_arg given) ----
            elif direction in ("out", "out_buffer", "out_ptr"):
                is_buffer = bool(size_arg) or direction == "out_buffer"
                if is_buffer:
                    # Array buffer mode
                    if not size_arg:
                        raise ValueError(
                            f"Call DLL/SO: Argument '{name}' is an Output buffer but "
                            f"no 'Size Arg' is configured. Set the size argument name in the "
                            f"Library Signature Editor."
                        )
                    size_val = pulled_inputs.get(size_arg)
                    if size_val is None:
                        raise ValueError(
                            f"Call DLL/SO: Size argument '{size_arg}' for buffer '{name}' "
                            f"was not found or has no value. Check the argument name."
                        )
                    try:
                        size = int(size_val)
                    except (TypeError, ValueError):
                        raise ValueError(
                            f"Call DLL/SO: Size argument '{size_arg}' for buffer '{name}' "
                            f"must be an integer (got {size_val!r})."
                        )
                    # Guardrail B: explicit pre-flight bounds check
                    if size <= 0:
                        raise ValueError(
                            f"Call DLL/SO: Size argument '{size_arg}' for buffer '{name}' "
                            f"must be > 0 (got {size}). Refusing to make the C call."
                        )
                    buf = (c_type * size)()
                    output_records.append(("out_buffer", name, buf, size))
                    c_args.append(buf)
                    argtypes.append(ctypes.POINTER(c_type))
                else:
                    # Scalar pointer mode
                    buf = c_type()
                    output_records.append(("out_ptr", name, buf, 1))
                    c_args.append(ctypes.byref(buf))
                    argtypes.append(ctypes.POINTER(c_type))

            # ---- Input/Output — array passed in, modified in-place ----
            elif direction in ("inout", "inout_buffer"):
                input_list = pulled_inputs.get(name)
                if not isinstance(input_list, (list, tuple)):
                    raise ValueError(
                        f"Call DLL/SO: Input/Output argument '{name}' expects a list or array "
                        f"on the DataIn pin, but received {type(input_list).__name__!r}."
                    )
                n = len(input_list)
                if n == 0:
                    raise ValueError(
                        f"Call DLL/SO: Input/Output argument '{name}' received an empty list. "
                        f"The buffer must contain at least one element."
                    )
                try:
                    coerced_list = []
                    for v in input_list:
                        coerced_v = _coerce_value(v, c_type_str)
                        if c_type_str != "c_char_p":
                            coerced_v = c_type(coerced_v).value
                        coerced_list.append(coerced_v)
                    buf = (c_type * n)(*coerced_list)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Call DLL/SO: Cannot convert Input/Output '{name}' list values "
                        f"to C type '{c_type_str}': {exc}"
                    )
                output_records.append(("inout_buffer", name, buf, n))
                c_args.append(buf)
                argtypes.append(ctypes.POINTER(c_type))

        # Assign argtypes so ctypes can perform type checking on the call.
        lib_func.argtypes = argtypes if argtypes else None

        # --- Guardrail A: non-blocking C call in a worker thread ---
        logger.info(
            f"[LibraryCall '{self.id}'] Calling {func_name} with {len(c_args)} argument(s)."
        )

        def _invoke():
            return lib_func(*c_args)

        raw_return = await asyncio.to_thread(_invoke)

        # --- Unpack return value ---
        if return_type_str == "void":
            self._outputs["ReturnValue"] = None
        elif return_type_str == "c_char_p":
            self._outputs["ReturnValue"] = (
                raw_return.decode("utf-8", errors="replace") if raw_return else None
            )
        else:
            self._outputs["ReturnValue"] = raw_return

        self._outputs["Status"] = 0

        # --- Unpack output buffers ---
        for record in output_records:
            direction_key, name, buf, size = record

            if direction_key == "out_buffer":
                self._outputs[name] = list(buf[:size])

            elif direction_key == "out_ptr":
                # Extract the scalar value written into the single-element buffer
                self._outputs[name] = buf.value

            elif direction_key == "inout_buffer":
                self._outputs[name] = list(buf[:size])

        logger.info(
            f"[LibraryCall '{self.id}'] Call completed. "
            f"Return = {self._outputs.get('ReturnValue')!r}"
        )
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        return self._outputs.get(pin_name)

    async def clear_data(self) -> None:
        self._outputs.clear()
