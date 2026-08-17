import os
import re
import sys
import json
import shutil
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from comfylab.engine.registry import register_block
from comfylab.blocks.base_script import (
    BaseSubprocessScriptBlock,
    parse_decorators
)
from backend.workspace import get_temp_dir

logger = logging.getLogger("comfylab.blocks.script_csharp")

DECORATOR_PATTERN = re.compile(
    r'^//\s*@(input|output)\s+(.*)',
    re.MULTILINE
)

REFERENCE_PATTERN = re.compile(
    r'^//\s*@(reference|assembly)\s+(?:path=["\']?|name=["\']?)([^"\'\r\n]+)["\']?',
    re.MULTILINE
)

DEFAULT_CSHARP_CODE = """// @input name="value" type="number" default=1.0
// @output name="result" type="number"

result = value * 2;
"""


def parse_csharp_decorators(code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parses C#-style decorator comments (// @input, // @output)."""
    return parse_decorators(code, DECORATOR_PATTERN)


def parse_csharp_references(code: str) -> List[str]:
    """Extracts assembly references from // @reference or // @assembly comments."""
    refs = []
    for match in REFERENCE_PATTERN.finditer(code):
        ref_path = match.group(2).strip()
        if ref_path:
            refs.append(ref_path)
    return refs


def _get_dotnet_target_framework() -> str:
    """Detects the installed .NET major version and formats TargetFramework (e.g. net10.0, net8.0)."""
    try:
        res = shutil.which("dotnet")
        if res:
            import subprocess
            out = subprocess.check_output([res, "--version"], text=True, timeout=2.0).strip()
            major = out.split('.')[0]
            if major.isdigit():
                return f"net{major}.0"
    except Exception:
        pass
    return "net8.0"


@register_block("script/csharp")
class CSharpScriptBlock(BaseSubprocessScriptBlock):
    icon = "🟣"
    display_name = "C# Script"
    description = "User-defined C# (.NET) code block with dynamic inputs, outputs, and assembly references."
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_CSHARP_CODE
    file_extension = ".cs"
    executable_name = "dotnet"

    i18n = {
        "pt-BR": {
            "display_name": "Script C#",
            "description": "Bloco de código C# (.NET) definido pelo usuário com entradas, saídas dinâmicas e referências a assemblies.",
            "category": "Scripts",
            "pins": {
                "In": "Entrada",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Script C#",
            "description": "Bloque de código C# (.NET) definido por el usuario con entradas, salidas dinámicas y referencias a ensamblados.",
            "category": "Scripts",
            "pins": {
                "In": "Entrada",
                "Out": "Salida"
            }
        }
    }

    def _parse_decorators(self, code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        return parse_csharp_decorators(code)

    async def _run_subprocess(self, code: str, inputs: Dict[str, Any], timeout: float):
        tmp_dir = get_temp_dir()
        proj_dir = tmp_dir / f"csharp_proj_{self.id}"
        proj_dir.mkdir(parents=True, exist_ok=True)

        cs_file = proj_dir / "Program.cs"
        csproj_file = proj_dir / "Script.csproj"
        output_file = proj_dir / "output.json"

        # Determine target framework and assembly references
        tfm = _get_dotnet_target_framework()
        refs = parse_csharp_references(code)
        ref_items = []
        for r in refs:
            ref_items.append(f'<Reference Include="{r}"><HintPath>{r}</HintPath></Reference>')
        ref_xml = "\n    ".join(ref_items) if ref_items else ""

        csproj_content = f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>{tfm}</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
  </PropertyGroup>
  <ItemGroup>
    {ref_xml}
  </ItemGroup>
</Project>"""

        # Generate variable declarations and input assignments
        var_decls = []
        for inp in self._parsed_inputs:
            name = inp['name']
            val = inputs.get(name, inp.get('default', 0))
            if isinstance(val, bool):
                var_decls.append(f"dynamic {name} = {str(val).lower()};")
            elif isinstance(val, (int, float)):
                var_decls.append(f"dynamic {name} = {val};")
            elif isinstance(val, str):
                var_decls.append(f"dynamic {name} = {json.dumps(val)};")
            elif isinstance(val, (list, dict)):
                var_decls.append(f"dynamic {name} = System.Text.Json.JsonSerializer.Deserialize<dynamic>({json.dumps(json.dumps(val))});")
            else:
                var_decls.append(f"dynamic {name} = null;")

        for out in self._parsed_outputs:
            name = out['name']
            if not any(inp['name'] == name for inp in self._parsed_inputs):
                var_decls.append(f"dynamic {name} = null;")

        # Output extraction
        out_assignments = []
        for out in self._parsed_outputs:
            name = out['name']
            out_assignments.append(f'__outDict["{name}"] = {name};')

        program_content = f"""// Auto-generated ComfyLAB C# Wrapper
using System;
using System.IO;
using System.Text.Json;
using System.Collections.Generic;

class Program {{
    static void Main(string[] args) {{
        {chr(10).join('        ' + l for l in var_decls)}

        // --- User Code Start ---
        {code}
        // --- User Code End ---

        var __outDict = new Dictionary<string, object?>();
        {chr(10).join('        ' + l for l in out_assignments)}

        string __jsonStr = JsonSerializer.Serialize(__outDict);
        File.WriteAllText("{output_file.as_posix()}", __jsonStr);
    }}
}}
"""

        try:
            cs_file.write_text(program_content, encoding="utf-8")
            csproj_file.write_text(csproj_content, encoding="utf-8")

            dotnet_exe = shutil.which("dotnet") or "dotnet"
            process = await asyncio.create_subprocess_exec(
                dotnet_exe, "run", "--project", str(csproj_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError(f"C# script execution timed out after {timeout}s.")

            if process.returncode != 0:
                err_msg = stderr.decode().strip() or stdout.decode().strip()
                raise RuntimeError(f"C# script failed with exit code {process.returncode}: {err_msg}")

            if output_file.exists():
                self._computed_outputs = json.loads(output_file.read_text(encoding="utf-8-sig"))
            else:
                self._computed_outputs = {}

        finally:
            shutil.rmtree(proj_dir, ignore_errors=True)


async def validate_code(code: str) -> dict:
    """Validates C# script syntax via dotnet build."""
    dotnet_exe = shutil.which("dotnet")
    if not dotnet_exe:
        return {"valid": True}  # Cannot perform offline check without dotnet CLI

    tmp_dir = get_temp_dir()
    proj_dir = tmp_dir / f"cs_validate_{uuid.uuid4().hex[:8]}"
    proj_dir.mkdir(parents=True, exist_ok=True)
    try:
        cs_file = proj_dir / "Program.cs"
        csproj_file = proj_dir / "Script.csproj"
        tfm = _get_dotnet_target_framework()

        csproj_file.write_text(f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>{tfm}</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
  </PropertyGroup>
</Project>""", encoding="utf-8")

        cs_file.write_text(f"""using System;
using System.IO;
using System.Text.Json;
using System.Collections.Generic;

class Program {{
    static void Main(string[] args) {{
        dynamic value = 1.0;
        dynamic result = null;
        {code}
    }}
}}""", encoding="utf-8")

        proc = await asyncio.create_subprocess_exec(
            dotnet_exe, "build", str(csproj_file), "-v", "q", "--nologo",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            return {"valid": True}
        err = stderr.decode().strip() or stdout.decode().strip()
        return {"valid": False, "error": err}
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)
