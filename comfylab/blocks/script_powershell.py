import shutil
import sys
from typing import Dict, Any, List, Tuple
from comfylab.engine.registry import register_block
from comfylab.blocks.base_script import (
    BaseSubprocessScriptBlock,
    parse_decorators,
    validate_via_external_parser
)
from comfylab.blocks.script import DECORATOR_PATTERN

DEFAULT_POWERSHELL_CODE = """# @input name="value" type="number" default=1.0
# @output name="result" type="number"

$result = $value * 2
"""


def parse_powershell_decorators(code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parses # @input and # @output decorators from PowerShell code."""
    return parse_decorators(code, DECORATOR_PATTERN)


def get_powershell_executable() -> str:
    """Finds the best available PowerShell executable ('pwsh' or 'powershell')."""
    if shutil.which("pwsh"):
        return "pwsh"
    if shutil.which("powershell"):
        return "powershell"
    if sys.platform == "win32" and shutil.which("powershell.exe"):
        return "powershell.exe"
    return "powershell" if sys.platform == "win32" else "pwsh"


@register_block("script/powershell")
class PowerShellScriptBlock(BaseSubprocessScriptBlock):
    icon = "⚡"
    display_name = "PowerShell Script"
    description = "User-defined PowerShell script block with dynamic inputs and outputs."
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_POWERSHELL_CODE
    file_extension = ".ps1"
    executable_name = "powershell"

    i18n = {
        "pt-BR": {
            "display_name": "Script PowerShell",
            "description": "Bloco de código PowerShell definido pelo usuário com entradas e saídas dinâmicas.",
            "category": "Scripts",
            "pins": {
                "In": "Entrada",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Script PowerShell",
            "description": "Bloque de código PowerShell definido por el usuario con entradas y salidas dinámicas.",
            "category": "Scripts",
            "pins": {
                "In": "Entrada",
                "Out": "Saída"
            }
        }
    }

    def _get_executable(self) -> str:
        return get_powershell_executable()

    def _get_subprocess_args(self, script_file_path: str) -> List[str]:
        return [
            self._get_executable(),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-File", script_file_path
        ]

    def _parse_decorators(self, code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        return parse_powershell_decorators(code)

    def _generate_script(self, code: str, inputs: Dict[str, Any], output_file_path: str) -> str:
        def to_ps_literal(val):
            if val is None:
                return "$null"
            elif isinstance(val, bool):
                return "$true" if val else "$false"
            elif isinstance(val, (int, float)):
                return str(val)
            elif isinstance(val, str):
                escaped = val.replace("`", "``").replace('"', '`"').replace('$', '`$').replace("\n", "`n")
                return f'"{escaped}"'
            elif isinstance(val, list):
                parts = [to_ps_literal(v) for v in val]
                return f"@({', '.join(parts)})"
            elif isinstance(val, dict):
                parts = [f'{to_ps_literal(k)} = {to_ps_literal(v)}' for k, v in val.items()]
                return f"@{{ {'; '.join(parts)} }}"
            return "$null"

        injection_lines = []
        for name, val in inputs.items():
            injection_lines.append(f"${name} = {to_ps_literal(val)}")

        injection_code = "\n".join(injection_lines) + "\n\n"

        # Output extraction
        out_assignments = []
        for out in self._parsed_outputs:
            name = out['name']
            out_assignments.append(f'$__out_dict["{name}"] = ${name}')

        output_script = f"""
$__out_dict = @{{}}
{chr(10).join(out_assignments)}

$__json_out = $__out_dict | ConvertTo-Json -Depth 10 -Compress
$__utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText("{output_file_path.replace('"', '`"')}", $__json_out, $__utf8NoBom)
"""
        return injection_code + code + "\n" + output_script


async def validate_code(code: str) -> dict:
    """Validates PowerShell script syntax via AST parser."""
    ps_cmd = (
        "$code = Get-Content -Raw -Path '{temp}'; "
        "$errors = $null; "
        "[System.Management.Automation.Language.Parser]::ParseInput($code, [ref]$null, [ref]$null, [ref]$errors); "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { [Console]::Error.WriteLine($_.Message) }; exit 1 }"
    )
    return await validate_via_external_parser(
        get_powershell_executable(),
        ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        code,
        ".ps1"
    )
