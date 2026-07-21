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
from typing import Any, Dict, List, Optional, Tuple

from comfylab.engine.registry import register_block
from comfylab.blocks.base import ExecutionContext, ExecIn, ExecOut, DataIn, DataOut
from comfylab.blocks.base_script import BaseSubprocessScriptBlock, parse_decorators

DECORATOR_PATTERN = re.compile(
    r'\(\*\s*@(input|output)\s+(.*?)\s*\*\)',
    re.MULTILINE
)

DEFAULT_WOLFRAM_CODE = """(* @input name="value" type="number" default=1.0 *)
(* @output name="result" type="number" *)

result = value * 2;
"""


def parse_wolfram_decorators(code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parses Wolfram-style decorator comments."""
    return parse_decorators(code, DECORATOR_PATTERN)


def parse_wolfram_json_value(val):
    if not isinstance(val, list):
        return val
    if not val:
        return []

    # Unpack explicit symbolic tokens safely
    if val[0] == "Expression":
        expr_type = val[1]
        payload = val[2]
        if expr_type == "Rational":
            return payload[0] / payload[1]
        elif expr_type == "List":
            return [parse_wolfram_json_value(item) for item in payload]
        return None

    # Fallback to keep downstream blocks from crashing if the user writes an invalid function
    if isinstance(val[0], str) and val[0] not in ("List", "Integer", "Real", "Rational"):
        return None  

    return [parse_wolfram_json_value(item) for item in val]


@register_block("script/wolfram")
class WolframScriptBlock(BaseSubprocessScriptBlock):
    icon = "🧠"
    display_name = "Wolfram Script"
    description = "User-defined Wolfram Language code block with decorated inputs and outputs."
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_WOLFRAM_CODE
    file_extension = ".wls"
    executable_name = "wolframscript"

    def _get_subprocess_args(self, script_file_path: str) -> List[str]:
        return ["wolframscript", "-file", script_file_path]

    async def _run_subprocess(self, code: str, inputs: Dict[str, Any], timeout: float):
        # We need to process outputs_data through parse_wolfram_json_value
        await super()._run_subprocess(code, inputs, timeout)
        
        # After execution, parse_wolfram_json_value on self._computed_outputs
        parsed_outputs = {}
        for pin_name, raw_val in self._computed_outputs.items():
            if raw_val == "Null" or raw_val is None:
                parsed_outputs[pin_name] = None
            else:
                try:
                    val = json.loads(raw_val)
                    parsed_outputs[pin_name] = parse_wolfram_json_value(val)
                except Exception:
                    parsed_outputs[pin_name] = raw_val
        self._computed_outputs = parsed_outputs

    def _generate_script(self, code: str, inputs: Dict[str, Any], output_file_path: str) -> str:
        def to_wolfram_literal(val):
            if val is None: return "Null"
            elif isinstance(val, bool): return "True" if val else "False"
            elif isinstance(val, (int, float)): return str(val)
            elif isinstance(val, str):
                escaped = val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                return f'"{escaped}"'
            elif isinstance(val, list):
                parts = [to_wolfram_literal(v) for v in val]
                return f"{{{','.join(parts)}}}"
            elif isinstance(val, dict):
                parts = [f'"{k}" -> {to_wolfram_literal(v)}' for k, v in val.items()]
                return f"<| {', '.join(parts)} |>"
            return "Null"

        # Generate standard input injections
        injection_lines = [f"{name} = {to_wolfram_literal(val)};" for name, val in inputs.items()]
        injection_code = "\n".join(injection_lines) + "\n\n"

        # Minimal, explicit JSON wrapper block
        out_pairs = []
        for out in self._parsed_outputs:
            name = out['name']
            out_pairs.append(f'"{name}" -> If[ValueQ[{name}], ExportString[{name}, "ExpressionJSON"], "Null"]')

        output_script = f'\nExport["{output_file_path}", <| {", ".join(out_pairs)} |>, "JSON"]\n'
        return injection_code + code + output_script

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        val = self._computed_outputs.get(pin_name)
        if val is not None:
            return val

        # If computation returned None, provide a safe, non-crashing structural fallback
        out_def = next((o for o in self._parsed_outputs if o['name'] == pin_name), {})
        out_type = out_def.get('type', 'any')
        
        if out_type == 'number': return 0.0
        if out_type == 'list': return []
        if out_type == 'boolean': return False
        return None


from comfylab.engine.config import get_config
if get_config().get("enable_wolfram_scripting", False):
    register_block("script/wolfram")(WolframScriptBlock)
