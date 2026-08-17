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

from typing import Any, Dict, List, Tuple

from comfylab.engine.registry import register_block
from comfylab.blocks.base_script import BaseSubprocessScriptBlock, validate_via_external_parser, parse_decorators
from comfylab.blocks.script import DECORATOR_PATTERN

DEFAULT_SAGE_CODE = """# @input name="value" type="number" default=1.0
# @output name="result" type="number"

result = value * 2
"""


def parse_sage_decorators(code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parses SageMath decorator comments."""
    return parse_decorators(code, DECORATOR_PATTERN)


@register_block("script/sage")
class SageScriptBlock(BaseSubprocessScriptBlock):
    icon = "🌿"
    display_name = "SageMath Script"
    description = "User-defined SageMath code block with decorated inputs and outputs."
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_SAGE_CODE
    file_extension = ".sage"
    executable_name = "sage"

    i18n = {
        "pt-BR": {
            "display_name": "Script SageMath",
            "description": "Bloco de código SageMath definido pelo usuário com entradas e saídas decoradas.",
            "category": "Scripts",
            "pins": {
                "In": "Entrada",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Script SageMath",
            "description": "Bloque de código SageMath definido por el usuario con entradas y salidas decoradas.",
            "category": "Scripts",
            "pins": {
                "In": "Entrada",
                "Out": "Salida"
            }
        }
    }

    def _generate_script(self, code: str, inputs: Dict[str, Any], output_file_path: str) -> str:
        # Generate inputs injection code in Sage syntax
        def to_sage_literal(val):
            if val is None:
                return "None"
            elif isinstance(val, bool):
                return "True" if val else "False"
            elif isinstance(val, (int, float)):
                return str(val)
            elif isinstance(val, str):
                escaped = val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                return f'"{escaped}"'
            elif isinstance(val, list):
                parts = [to_sage_literal(v) for v in val]
                return f"[{', '.join(parts)}]"
            elif isinstance(val, dict):
                parts = [f'"{k}": {to_sage_literal(v)}' for k, v in val.items()]
                return f"{{{', '.join(parts)}}}"
            return "None"

        injection_lines = []
        for name, val in inputs.items():
            injection_lines.append(f"{name} = {to_sage_literal(val)}")

        injection_code = "\n".join(injection_lines) + "\n\n"

        # Sage to JSON serializer block
        sage_serializer = r"""
import json

def _sage_to_json_serializable(val):
    if val is None:
        return None
    if isinstance(val, (bool, str, int, float)):
        return val
    try:
        if hasattr(val, "is_integer") and val.is_integer():
            return int(val)
        if hasattr(val, "is_real") and val.is_real():
            if hasattr(val, "numerical_approx"):
                return float(val.numerical_approx())
            return float(val)
    except Exception:
        pass
    if hasattr(val, "variables") and callable(val.variables):
        try:
            vars = val.variables()
            if len(vars) == 0 and hasattr(val, "numerical_approx"):
                return float(val.numerical_approx())
        except Exception:
            pass
    if hasattr(val, "rows") and callable(val.rows):
        return [_sage_to_json_serializable(list(r)) for r in val.rows()]
    if hasattr(val, "is_vector") and callable(val.is_vector) and val.is_vector():
        return [_sage_to_json_serializable(item) for item in list(val)]
    if isinstance(val, (list, tuple)):
        return [_sage_to_json_serializable(item) for item in val]
    if isinstance(val, dict):
        return {str(k): _sage_to_json_serializable(v) for k, v in val.items()}
    try:
        return float(val)
    except Exception:
        pass
    return str(val)
"""

        # Output extraction
        out_dict_items = []
        for out in self._parsed_outputs:
            name = out['name']
            out_dict_items.append(f'"{name}": _sage_to_json_serializable(globals().get("{name}", None))')

        output_script = f"""
{sage_serializer}

_out_dict = {{{", ".join(out_dict_items)}}}
with open("{output_file_path}", "w", encoding="utf-8") as _f:
    json.dump(_out_dict, _f)
"""
        return injection_code + code + "\n" + output_script


async def validate_code(code: str) -> dict:
    """Validates SageMath script syntax using sage preparser or python compilation."""
    import shutil
    if shutil.which("sage"):
        return await validate_via_external_parser(
            "sage", ["-c", 'from sage.all import *; preparse(open("{temp}").read())'], code, ".sage"
        )
    # Fallback to python syntax check if sage binary is not in PATH
    try:
        compile(code, '<script:sage>', 'exec')
        return {"valid": True}
    except SyntaxError as e:
        return {"valid": False, "error": str(e), "line": e.lineno, "offset": e.offset}
