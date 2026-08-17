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
from typing import Any, Dict, List, Tuple

from comfylab.engine.registry import register_block
from comfylab.blocks.base_script import BaseSubprocessScriptBlock, validate_via_external_parser, parse_decorators

DECORATOR_PATTERN = re.compile(
    r'/\*\s*@(input|output)\s+(.*?)\s*\*/',
    re.MULTILINE
)

DEFAULT_MAXIMA_CODE = """/* @input name="value" type="number" default=1.0 */
/* @output name="result" type="number" */

result: value * 2;
"""


def parse_maxima_decorators(code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parses Maxima-style decorator comments."""
    return parse_decorators(code, DECORATOR_PATTERN)


@register_block("script/maxima")
class MaximaScriptBlock(BaseSubprocessScriptBlock):
    icon = "🧮"
    display_name = "Maxima Script"
    description = "User-defined Maxima CAS code block with decorated inputs and outputs."
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_MAXIMA_CODE
    file_extension = ".mac"
    executable_name = "maxima"

    i18n = {
        "pt-BR": {
            "display_name": "Script Maxima",
            "description": "Bloco de código Maxima CAS definido pelo usuário com entradas e saídas decoradas.",
            "category": "Scripts",
            "pins": {
                "In": "Entrada",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Script Maxima",
            "description": "Bloque de código Maxima CAS definido por el usuario con entradas y salidas decoradas.",
            "category": "Scripts",
            "pins": {
                "In": "Entrada",
                "Out": "Salida"
            }
        }
    }

    def _get_subprocess_args(self, script_file_path: str) -> List[str]:
        return ["maxima", "--very-quiet", "-Q", "--no-init", "-b", script_file_path]

    def _generate_script(self, code: str, inputs: Dict[str, Any], output_file_path: str) -> str:
        def to_maxima_literal(val):
            if val is None:
                return "false"
            elif isinstance(val, bool):
                return "true" if val else "false"
            elif isinstance(val, (int, float)):
                return str(val)
            elif isinstance(val, str):
                escaped = val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                return f'"{escaped}"'
            elif isinstance(val, list):
                parts = [to_maxima_literal(v) for v in val]
                return f"[{', '.join(parts)}]"
            elif isinstance(val, dict):
                parts = [f'[{to_maxima_literal(k)}, {to_maxima_literal(v)}]' for k, v in val.items()]
                return f"[{', '.join(parts)}]"
            return "false"

        injection_lines = []
        for name, val in inputs.items():
            injection_lines.append(f"{name}: {to_maxima_literal(val)}$")

        injection_code = "\n".join(injection_lines) + "\n\n"

        maxima_json_serializer = r"""
_to_json(val) := block([res, i, len, flt],
  if val = true then return("true")
  else if val = false then return("false")
  else if integerp(val) then return(string(val))
  else if floatnump(val) or numberp(val) then return(string(float(val)))
  else if stringp(val) then return(sconcat("\"", ssubst("\\\"", "\"", val), "\""))
  else if listp(val) then (
    len: length(val),
    if len = 0 then return("[]"),
    res: "[",
    for i: 1 thru len do (
      res: sconcat(res, _to_json(val[i])),
      if i < len then res: sconcat(res, ",")
    ),
    return(sconcat(res, "]"))
  )
  else if matrixp(val) then (
    return(_to_json(args(val)))
  )
  else (
    flt: errcatch(float(val)),
    if flt # [] and numberp(flt[1]) then return(string(flt[1]))
    else return(sconcat("\"", ssubst("\\\"", "\"", string(val)), "\""))
  )
)$
"""

        # Ensure user code ends with a statement terminator (; or $) so it doesn't collide with the output extraction
        code_without_comments = re.sub(r"/\*[\s\S]*?\*/", "", code).strip()
        if code_without_comments and not code_without_comments.endswith(";") and not code_without_comments.endswith("$"):
            user_code = code + "\n$\n"
        else:
            user_code = code + "\n"

        # Output extraction
        out_pairs = []
        for out in self._parsed_outputs:
            name = out['name']
            out_pairs.append(f'sconcat("\\"{name}\\":", _to_json({name}))')

        pairs_joined = ", \",\", ".join(out_pairs) if out_pairs else '""'

        output_script = f"""
_out_fp: openw("{output_file_path}")$
_json_str: sconcat("{{", {pairs_joined}, "}}")$
printf(_out_fp, "~a", _json_str)$
close(_out_fp)$
quit()$
"""
        return maxima_json_serializer + "\n\n" + injection_code + user_code + "\n\n" + output_script


async def validate_code(code: str) -> dict:
    """Validates Maxima script syntax using batch dry-run."""
    return await validate_via_external_parser(
        "maxima", ["--very-quiet", "-Q", "--no-init", "-b", "{temp}"], code, ".mac"
    )
