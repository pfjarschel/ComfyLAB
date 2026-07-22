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

import re
import json
import os
import shutil
import tempfile
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, ExecutionContext
from backend.workspace import get_temp_dir

logger = logging.getLogger("comfylab.blocks.base_script")

KV_PATTERN = re.compile(
    r'(\w+)=("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|\[.*?\]|\S+)'
)

def parse_decorators(code: str, decorator_pattern: re.Pattern) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parses decorator comments (input/output parameters) from script code."""
    inputs = []
    outputs = []
    for match in decorator_pattern.finditer(code):
        direction = match.group(1)
        kv_string = match.group(2)
        params = {}
        for kv_match in KV_PATTERN.finditer(kv_string):
            key = kv_match.group(1)
            value = kv_match.group(2).strip()
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            elif value.startswith('['):
                try:
                    value = json.loads(value.replace("'", '"'))
                except json.JSONDecodeError:
                    pass
            elif value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            else:
                try:
                    value = float(value)
                    if value == int(value) and '.' not in kv_match.group(2):
                        value = int(value)
                except ValueError:
                    pass
            params[key] = value
        if 'name' not in params:
            continue
        if direction == 'input':
            inputs.append(params)
        else:
            outputs.append(params)
    return inputs, outputs


class BaseScriptBlock(BaseBlock):
    """Abstract base class for all scripting blocks (in-process or subprocess-based)."""
    comment_pattern: Optional[re.Pattern] = None
    default_code: str = ""

    inputs_def = [ExecIn("In")]
    outputs_def = [ExecOut("Out")]

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._computed_outputs: Dict[str, Any] = {}
        code = self.properties.get("code", self.default_code)
        self._parsed_inputs: List[Dict[str, Any]] = []
        self._parsed_outputs: List[Dict[str, Any]] = []
        if self.comment_pattern:
            self._parsed_inputs, self._parsed_outputs = parse_decorators(code, self.comment_pattern)
        self._sync_dynamic_pins()

    def _sync_dynamic_pins(self):
        type_map = {
            'number': float, 'boolean': bool, 'text': str,
            'string': str, 'list': list, 'ndarray': np.ndarray, 'any': None
        }
        for inp in self._parsed_inputs:
            name = inp['name']
            type_hint = type_map.get(inp.get('type', 'any'))
            default = inp.get('default')
            widget = inp.get('widget')
            min_val = inp.get('min')
            max_val = inp.get('max')
            step = inp.get('step')
            options = inp.get('options')
            optional = inp.get('optional', False)
            pin = DataIn(name, type_hint=type_hint, default=default, widget=widget,
                         min_val=min_val, max_val=max_val, step=step,
                         options=options, optional=optional)
            self.inputs[name] = pin

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        val = self._computed_outputs.get(pin_name)
        out_info = next((o for o in self._parsed_outputs if o.get('name') == pin_name), None)
        if out_info and out_info.get('type') == 'ndarray' and isinstance(val, list):
            return np.array(val)
        return val


class BaseSubprocessScriptBlock(BaseScriptBlock):
    """Base class for scripting blocks that compile or run user code in an external subprocess."""
    file_extension: str = ""
    executable_name: str = ""

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        code = self.properties.get("code", "")
        if not code.strip():
            raise ValueError(f"{self.display_name} has no code to execute.")

        if self.comment_pattern:
            self._parsed_inputs, self._parsed_outputs = parse_decorators(code, self.comment_pattern)

        inputs = {}
        for inp in self._parsed_inputs:
            name = inp['name']
            val = await context.pull(self.id, name)
            if isinstance(val, np.ndarray):
                val = val.tolist()
            inputs[name] = val

        timeout = float(self.properties.get("timeout", 30.0))
        await self._run_subprocess(code, inputs, timeout)
        return "Out"

    def _generate_script(self, code: str, inputs: Dict[str, Any], output_file_path: str) -> str:
        """Language-specific logic to inject inputs and output JSON serialization code around the user's script."""
        raise NotImplementedError

    def _get_subprocess_args(self, script_file_path: str) -> List[str]:
        """Returns the command line arguments used to execute the script file. Overridden for complex toolchains like Cargo."""
        return [self.executable_name, script_file_path]

    def _get_subprocess_env(self) -> Optional[Dict[str, str]]:
        """Returns environment variables to set when running the subprocess."""
        return None

    async def _run_subprocess(self, code: str, inputs: Dict[str, Any], timeout: float):
        tmp_dir = get_temp_dir()
        script_file = tmp_dir / f"temp_script_{self.id}{self.file_extension}"
        output_file = tmp_dir / f"temp_out_{self.id}.json"

        full_script = self._generate_script(code, inputs, output_file.as_posix())

        try:
            script_file.write_text(full_script, encoding="utf-8")
            args = self._get_subprocess_args(str(script_file))
            env = self._get_subprocess_env()

            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError(f"{self.display_name} subprocess exceeded execution timeout of {timeout}s.")

            if process.returncode != 0:
                err_msg = stderr.decode().strip() or stdout.decode().strip()
                raise RuntimeError(f"{self.display_name} execution failed with exit code {process.returncode}: {err_msg}")

            if output_file.exists():
                outputs_data = json.loads(output_file.read_text(encoding="utf-8"))
                self._computed_outputs = outputs_data
            else:
                self._computed_outputs = {}

        finally:
            if script_file.exists():
                script_file.unlink()
            if output_file.exists():
                output_file.unlink()


async def validate_via_external_parser(executable: str, args: List[str], code: str, suffix: str) -> dict:
    """
    Shared script syntax validator for subprocess-based languages.
    Writes the code to a temp file and runs `executable` with `args`
    (any occurrence of "{temp}" in args is replaced by the temp file path).
    Returns {"valid": True} when the executable is not installed (validation skipped).
    """
    if not shutil.which(executable):
        return {"valid": True}

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode="w", encoding="utf-8") as f:
        f.write(code)
        temp_name = f.name
    try:
        cmd = [executable] + [a.replace("{temp}", temp_name) for a in args]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return {"valid": True}
        return {"valid": False, "error": stderr.decode().strip() or stdout.decode().strip()}
    except Exception as e:
        return {"valid": False, "error": str(e)}
    finally:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
